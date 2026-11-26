use std::{
    collections::HashMap,
    env,
    net::SocketAddr,
    sync::Arc,
    time::{SystemTime, UNIX_EPOCH},
};

use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use casino_battle_core::{DrawOutcome, GameError, RunState};
use serde::{Deserialize, Serialize};
use sqlx::{postgres::PgPoolOptions, PgPool};
use tokio::sync::{Mutex, RwLock};
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use uuid::Uuid;

#[derive(Clone)]
struct AppState {
    runs: Arc<RwLock<HashMap<Uuid, RunState>>>,
    database: Option<PgPool>,
    transition_guard: Arc<Mutex<()>>,
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
            .bind(run.seed as i64)
            .bind(state)
            .execute(database)
            .await
            .map_err(ApiError::database)?;
        }
        self.runs.write().await.insert(id, run.clone());
        Ok(())
    }

    async fn load(&self, id: Uuid) -> Result<RunState, ApiError> {
        if let Some(run) = self.runs.read().await.get(&id).cloned() {
            return Ok(run);
        }
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
        }
        Err(ApiError::new(StatusCode::NOT_FOUND, "run_not_found"))
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
            GameError::NotEnoughEssence => StatusCode::CONFLICT,
            GameError::RunOver => StatusCode::CONFLICT,
            GameError::EmptyParty => StatusCode::UNPROCESSABLE_ENTITY,
            GameError::UnitNotFound => StatusCode::NOT_FOUND,
            GameError::InvalidMerge => StatusCode::CONFLICT,
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
struct CreateRunRequest {
    seed: Option<u64>,
}

#[derive(Deserialize)]
struct MergeRequest {
    keeper_id: u64,
    donor_id: u64,
}

#[derive(Serialize)]
struct CreateRunResponse {
    run_id: Uuid,
    state: RunState,
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
    let seed = request.seed.unwrap_or_else(random_seed);
    let run = RunState::new(seed);
    let run_id = Uuid::new_v4();
    state.save(run_id, &run).await?;
    Ok((
        StatusCode::CREATED,
        Json(CreateRunResponse { run_id, state: run }),
    ))
}

async fn get_run(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<RunState>, ApiError> {
    Ok(Json(state.load(run_id).await?))
}

async fn draw(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<DrawOutcome>, ApiError> {
    let _guard = state.transition_guard.lock().await;
    let mut run = state.load(run_id).await?;
    let outcome = run.draw().map_err(ApiError::game)?;
    state.save(run_id, &run).await?;
    Ok(Json(outcome))
}

async fn battle(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
) -> Result<Json<casino_battle_core::BattleReport>, ApiError> {
    let _guard = state.transition_guard.lock().await;
    let mut run = state.load(run_id).await?;
    let report = run.resolve_auto_battle().map_err(ApiError::game)?;
    state.save(run_id, &run).await?;
    Ok(Json(report))
}

async fn merge(
    State(state): State<AppState>,
    Path(run_id): Path<Uuid>,
    Json(request): Json<MergeRequest>,
) -> Result<Json<RunState>, ApiError> {
    let _guard = state.transition_guard.lock().await;
    let mut run = state.load(run_id).await?;
    run.merge_units(request.keeper_id, request.donor_id)
        .map_err(ApiError::game)?;
    state.save(run_id, &run).await?;
    Ok(Json(run))
}

fn random_seed() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos() as u64)
        .unwrap_or(1)
        .max(1)
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

    let state = AppState {
        runs: Arc::new(RwLock::new(HashMap::new())),
        database,
        transition_guard: Arc::new(Mutex::new(())),
    };
    let app = Router::new()
        .route("/healthz", get(health))
        .route("/api/v1/runs", post(create_run))
        .route("/api/v1/runs/:run_id", get(get_run))
        .route("/api/v1/runs/:run_id/draw", post(draw))
        .route("/api/v1/runs/:run_id/battle", post(battle))
        .route("/api/v1/runs/:run_id/merge", post(merge))
        .with_state(state)
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http());

    let address: SocketAddr = env::var("BIND_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:3000".to_owned())
        .parse()?;
    let listener = tokio::net::TcpListener::bind(address).await?;
    tracing::info!(%address, "Casino Battle API listening");
    axum::serve(listener, app).await?;
    Ok(())
}
