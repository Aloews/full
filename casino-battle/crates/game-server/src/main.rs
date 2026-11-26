use std::{collections::HashMap, env, net::SocketAddr, sync::Arc};

use axum::{
    extract::{Path, State},
    http::{header, HeaderValue, Method, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use casino_battle_core::{
    BattleReport, DrawOutcome, GameError, RunPhase, RunState, Sigil, SynergyStatus, Unit,
};
use serde::{Deserialize, Serialize};
use sqlx::{postgres::PgPoolOptions, PgPool};
use tokio::sync::RwLock;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use uuid::Uuid;

#[derive(Clone)]
struct AppState {
    runs: Arc<RwLock<HashMap<Uuid, RunState>>>,
    database: Option<PgPool>,
}

impl AppState {
    async fn save(&self, id: Uuid, run: &RunState) -> Result<(), ApiError> {
        if let Some(database) = &self.database {
            let state = sqlx::types::Json(run.clone());
            sqlx::query(
                "INSERT INTO casino_battle_runs (id, seed, state) VALUES ($1, $2, $3) \
                 ON CONFLICT (id) DO UPDATE SET seed = EXCLUDED.seed, state = EXCLUDED.state, updated_at = NOW()",
            )
            .bind(id)
            .bind(run.seed.to_string())
            .bind(state)
            .execute(database)
            .await
            .map_err(ApiError::database)?;
        }
        self.runs.write().await.insert(id, run.clone());
        Ok(())
    }

    async fn load(&self, id: Uuid) -> Result<RunState, ApiError> {
        if let Some(database) = &self.database {
            let state = sqlx::query_scalar::<_, sqlx::types::Json<RunState>>(
                "SELECT state FROM casino_battle_runs WHERE id = $1",
            )
            .bind(id)
            .fetch_optional(database)
            .await
            .map_err(ApiError::database)?;

            if let Some(state) = state {
                self.runs.write().await.insert(id, state.0.clone());
                return Ok(state.0);
            }
            return Err(ApiError::new(StatusCode::NOT_FOUND, "run_not_found"));
        }

        self.runs
            .read()
            .await
            .get(&id)
            .cloned()
            .ok_or_else(|| ApiError::new(StatusCode::NOT_FOUND, "run_not_found"))
    }

    async fn transition<T, F>(&self, id: Uuid, operation: F) -> Result<(RunState, T), ApiError>
    where
        F: FnOnce(&mut RunState) -> Result<T, GameError>,
    {
        if let Some(database) = &self.database {
            let mut transaction = database.begin().await.map_err(ApiError::database)?;
            let stored = sqlx::query_scalar::<_, sqlx::types::Json<RunState>>(
                "SELECT state FROM casino_battle_runs WHERE id = $1 FOR UPDATE",
            )
            .bind(id)
            .fetch_optional(&mut *transaction)
            .await
            .map_err(ApiError::database)?
            .ok_or_else(|| ApiError::new(StatusCode::NOT_FOUND, "run_not_found"))?;

            let mut run = stored.0;
            let result = operation(&mut run).map_err(ApiError::game)?;
            sqlx::query(
                "UPDATE casino_battle_runs SET state = $2, updated_at = NOW() WHERE id = $1",
            )
            .bind(id)
            .bind(sqlx::types::Json(run.clone()))
            .execute(&mut *transaction)
            .await
            .map_err(ApiError::database)?;
            transaction.commit().await.map_err(ApiError::database)?;
            self.runs.write().await.insert(id, run.clone());
            return Ok((run, result));
        }

        let mut runs = self.runs.write().await;
        let run = runs
            .get_mut(&id)
            .ok_or_else(|| ApiError::new(StatusCode::NOT_FOUND, "run_not_found"))?;
        let result = operation(run).map_err(ApiError::game)?;
        Ok((run.clone(), result))
    }
}

#[derive(Clone, Debug, Serialize)]
struct RunSnapshot {
    phase: RunPhase,
    wave: u32,
    essence: u32,
    hearts: u8,
    board: Vec<Vec<Sigil>>,
    party: Vec<Unit>,
    synergies: Vec<SynergyStatus>,
    total_draws: u32,
    battle_wins: u32,
}

impl From<&RunState> for RunSnapshot {
    fn from(run: &RunState) -> Self {
        Self {
            phase: run.phase,
            wave: run.wave,
            essence: run.essence,
            hearts: run.hearts,
            board: run.board.iter().map(|row| row.to_vec()).collect(),
            party: run.party.clone(),
            synergies: run.synergies(),
            total_draws: run.total_draws,
            battle_wins: run.battle_wins,
        }
    }
}

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    code: &'static str,
}

impl ApiError {
    fn new(status: StatusCode, code: &'static str) -> Self {
        Self { status, code }
    }

    fn database(_: sqlx::Error) -> Self {
        Self::new(StatusCode::INTERNAL_SERVER_ERROR, "persistence_error")
    }

    fn game(error: GameError) -> Self {
        let status = match error {
            GameError::NotEnoughEssence | GameError::RunOver | GameError::InvalidMerge => {
                StatusCode::CONFLICT
            }
            GameError::EmptyParty | GameError::InvalidLane => StatusCode::UNPROCESSABLE_ENTITY,
            GameError::UnitNotFound => StatusCode::NOT_FOUND,
        };
        Self::new(status, "invalid_game_action")
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, Json(ErrorBody { error: self.code })).into_response()
    }
}

#[derive(Serialize)]
struct ErrorBody {
    error: &'static str,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CreateRunRequest {}

#[derive(Deserialize)]
struct MergeRequest {
    keeper_id: u64,
    donor_id: u64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FormationRequest {
    unit_id: u64,
    lane: u8,
}

#[derive(Serialize)]
struct CreateRunResponse {
    run_id: Uuid,
    state: RunSnapshot,
}

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
    persistence: &'static str,
}

async fn health(State(state): State<AppState>) -> Result<Json<HealthResponse>, ApiError> {
    let persistence = if let Some(database) = &state.database {
        sqlx::query("SELECT 1")
            .execute(database)
            .await
            .map_err(ApiError::database)?;
        "postgres"
    } else {
        "development_memory_only"
    };
    Ok(Json(HealthResponse {
        status: "ok",
        persistence,
    }))
}

async fn create_run(
    State(state): State<AppState>,
    Json(request): Json<CreateRunRequest>,
) -> Result<(StatusCode, Json<CreateRunResponse>), ApiError> {
    let _ = request;
    let run_id = Uuid::new_v4();
    let run = RunState::new(run_id.as_u128() as u64);
    state.save(run_id, &run).await?;
    Ok((
        StatusCode::CREATED,
        Json(CreateRunResponse {
            run_id,
            state: RunSnapshot::from(&run),
        }),
    ))
}

async fn get_run(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<RunSnapshot>, ApiError> {
    let run = state.load(run_id).await?;
    Ok(Json(RunSnapshot::from(&run)))
}

async fn draw(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<DrawOutcome>, ApiError> {
    let (_, outcome) = state.transition(run_id, RunState::draw).await?;
    Ok(Json(outcome))
}

async fn battle(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<BattleReport>, ApiError> {
    let (_, report) = state
        .transition(run_id, RunState::resolve_auto_battle)
        .await?;
    Ok(Json(report))
}

async fn set_formation(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
    Json(request): Json<FormationRequest>,
) -> Result<Json<RunSnapshot>, ApiError> {
    let (run, ()) = state
        .transition(run_id, |run| run.set_lane(request.unit_id, request.lane))
        .await?;
    Ok(Json(RunSnapshot::from(&run)))
}

async fn merge(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
    Json(request): Json<MergeRequest>,
) -> Result<Json<RunSnapshot>, ApiError> {
    let (run, ()) = state
        .transition(run_id, |run| {
            run.merge_units(request.keeper_id, request.donor_id)
        })
        .await?;
    Ok(Json(RunSnapshot::from(&run)))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(env::var("RUST_LOG").unwrap_or_else(|_| "info".to_owned()))
        .init();

    let database = if let Ok(url) = env::var("DATABASE_URL") {
        let pool = PgPoolOptions::new()
            .max_connections(8)
            .connect(&url)
            .await?;
        sqlx::migrate!("./migrations").run(&pool).await?;
        Some(pool)
    } else {
        tracing::warn!("DATABASE_URL is unset; using a single-process development store");
        None
    };

    let allowed_origins = env::var("CORS_ALLOWED_ORIGINS")
        .unwrap_or_else(|_| "http://localhost:5173".to_owned())
        .split(',')
        .map(str::trim)
        .filter(|origin| !origin.is_empty())
        .map(HeaderValue::from_str)
        .collect::<Result<Vec<_>, _>>()?;
    let cors = CorsLayer::new()
        .allow_origin(allowed_origins)
        .allow_methods([Method::GET, Method::POST])
        .allow_headers([header::CONTENT_TYPE]);

    let state = AppState {
        runs: Arc::new(RwLock::new(HashMap::new())),
        database,
    };
    let app = Router::new()
        .route("/healthz", get(health))
        .route("/api/v1/runs", post(create_run))
        .route("/api/v1/runs/:run_id", get(get_run))
        .route("/api/v1/runs/:run_id/draw", post(draw))
        .route("/api/v1/runs/:run_id/battle", post(battle))
        .route("/api/v1/runs/:run_id/merge", post(merge))
        .route("/api/v1/runs/:run_id/formation", post(set_formation))
        .with_state(state)
        .layer(cors)
        .layer(TraceLayer::new_for_http());

    let address: SocketAddr = env::var("BIND_ADDR")
        .or_else(|_| env::var("PORT").map(|port| format!("0.0.0.0:{port}")))
        .unwrap_or_else(|_| "0.0.0.0:3000".to_owned())
        .parse()?;
    let listener = tokio::net::TcpListener::bind(address).await?;
    tracing::info!(%address, "Casino Battle API listening");
    axum::serve(listener, app).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_snapshot_does_not_expose_rng_seed_or_internal_state() {
        let run = RunState::new(0xD00D_F00D);
        let snapshot = RunSnapshot::from(&run);
        let json = serde_json::to_value(snapshot).unwrap();

        assert!(json.get("seed").is_none());
        assert!(json.get("rng_state").is_none());
        assert!(json.get("next_unit_id").is_none());
        assert_eq!(json["party"].as_array().unwrap().len(), 1);
    }
}
