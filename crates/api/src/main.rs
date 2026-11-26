use axum::{
    Json, Router,
    extract::{Path, State},
    http::StatusCode,
    response::{Html, IntoResponse, Response},
    routing::{get, post},
};
use serde::Deserialize;
use serde_json::json;
use slotbound_core::{GameError, GameState, ItemKind};
use sqlx::{PgPool, postgres::PgPoolOptions};
use std::{
    collections::HashMap,
    fs,
    net::SocketAddr,
    path::PathBuf,
    sync::{
        Arc,
        atomic::{AtomicU64, Ordering},
    },
};
use tokio::sync::RwLock;

#[derive(Clone)]
struct AppState {
    runs: Arc<RwLock<HashMap<String, GameState>>>,
    next_id: Arc<AtomicU64>,
    data_dir: Arc<PathBuf>,
    pool: Option<PgPool>,
}

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    code: &'static str,
    message: String,
}
impl ApiError {
    fn not_found() -> Self {
        Self {
            status: StatusCode::NOT_FOUND,
            code: "run_not_found",
            message: "Run not found".into(),
        }
    }
    fn storage() -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            code: "storage_failure",
            message: "The run could not be saved".into(),
        }
    }
    fn database() -> Self {
        Self {
            status: StatusCode::SERVICE_UNAVAILABLE,
            code: "database_unavailable",
            message: "Persistent storage is temporarily unavailable".into(),
        }
    }
    fn from_game(error: GameError) -> Self {
        let status = match error {
            GameError::RunEnded
            | GameError::WrongPhase
            | GameError::NoSpins
            | GameError::NudgeSpent
            | GameError::CoreChoiceRequired => StatusCode::CONFLICT,
            GameError::NotEnoughGold | GameError::UnitCapacityReached | GameError::InvalidNudge => {
                StatusCode::UNPROCESSABLE_ENTITY
            }
            GameError::UnitNotFound => StatusCode::NOT_FOUND,
            _ => StatusCode::UNPROCESSABLE_ENTITY,
        };
        let code = match error {
            GameError::RunEnded => "run_ended",
            GameError::WrongPhase => "wrong_phase",
            GameError::NoSpins => "no_spins",
            GameError::NotEnoughGold => "not_enough_gold",
            GameError::UnitCapacityReached => "unit_capacity_reached",
            GameError::InvalidNudge => "invalid_nudge",
            GameError::NudgeSpent => "nudge_spent",
            GameError::UnitNotFound => "unit_not_found",
            GameError::SameUnit => "same_unit",
            GameError::TargetLocked => "target_locked",
            GameError::DonorLocked => "donor_locked",
            GameError::InvalidPromotion => "invalid_promotion",
            GameError::InvalidCoreChoice => "invalid_core_choice",
            GameError::CoreChoiceRequired => "core_choice_required",
            GameError::InvalidItem => "invalid_item",
        };
        Self {
            status,
            code,
            message: error.to_string(),
        }
    }
}
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(json!({"error_code": self.code, "message": self.message})),
        )
            .into_response()
    }
}

#[derive(Deserialize)]
struct CreateRun {
    seed: Option<u64>,
}
#[derive(Deserialize)]
struct NudgeRequest {
    column: usize,
    direction: i8,
}
#[derive(Deserialize)]
struct AbsorbRequest {
    target_id: u64,
    donor_id: u64,
}
#[derive(Deserialize)]
struct PromotionRequest {
    unit_id: u64,
    choice: String,
}
#[derive(Deserialize)]
struct IndexRequest {
    index: usize,
}
#[derive(Deserialize)]
struct ItemRequest {
    item: ItemKind,
}
#[derive(Deserialize)]
struct UnitRequest {
    unit_id: u64,
}

fn app_state(data_dir: PathBuf, pool: Option<PgPool>) -> AppState {
    let mut runs = HashMap::new();
    if pool.is_none() {
        if let Ok(entries) = fs::read_dir(&data_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|ext| ext.to_str()) != Some("json") {
                    continue;
                }
                match fs::read(&path)
                    .ok()
                    .and_then(|bytes| serde_json::from_slice::<GameState>(&bytes).ok())
                {
                    Some(game) => {
                        runs.insert(game.run_id.clone(), game);
                    }
                    None => eprintln!("Skipping unreadable Slotbound save: {}", path.display()),
                }
            }
        }
    }

    AppState {
        runs: Arc::new(RwLock::new(runs)),
        next_id: Arc::new(AtomicU64::new(1)),
        data_dir: Arc::new(data_dir),
        pool,
    }
}

fn database_pool() -> Option<PgPool> {
    let url = std::env::var("DATABASE_URL").ok()?;
    let pool = PgPoolOptions::new()
        .max_connections(4)
        .connect_lazy(&url)
        .expect("DATABASE_URL is invalid");
    Some(pool)
}

fn default_data_dir() -> PathBuf {
    std::env::var_os("SLOTBOUND_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(".slotbound-data/runs"))
}

pub fn app() -> Router {
    app_with_storage(default_data_dir(), database_pool())
}

fn app_with_data_dir(data_dir: PathBuf) -> Router {
    app_with_storage(data_dir, None)
}

fn app_with_storage(data_dir: PathBuf, pool: Option<PgPool>) -> Router {
    Router::new()
        .route("/", get(index))
        .route("/app.js", get(javascript))
        .route("/style.css", get(stylesheet))
        .route("/healthz", get(health))
        .route("/api/runs", post(create_run))
        .route("/api/runs/{run_id}", get(get_run))
        .route("/api/runs/{run_id}/spin", post(spin))
        .route("/api/runs/{run_id}/nudge", post(nudge))
        .route("/api/runs/{run_id}/absorb", post(absorb))
        .route("/api/runs/{run_id}/promotion", post(promotion))
        .route("/api/runs/{run_id}/lock", post(toggle_lock))
        .route("/api/runs/{run_id}/battle", post(battle))
        .route("/api/runs/{run_id}/next-wave", post(next_wave))
        .route("/api/runs/{run_id}/core", post(choose_core))
        .route("/api/runs/{run_id}/item", post(buy_item))
        .with_state(app_state(data_dir, pool))
}
async fn save_game(data_dir: &PathBuf, game: &GameState) -> Result<(), ApiError> {
    tokio::fs::create_dir_all(data_dir)
        .await
        .map_err(|_| ApiError::storage())?;
    let filename = format!("{}.json", game.run_id);
    let final_path = data_dir.join(filename);
    let temp_path = data_dir.join(format!("{}.tmp", game.run_id));
    let bytes = serde_json::to_vec(game).map_err(|_| ApiError::storage())?;
    tokio::fs::write(&temp_path, bytes)
        .await
        .map_err(|_| ApiError::storage())?;
    tokio::fs::rename(&temp_path, &final_path)
        .await
        .map_err(|_| ApiError::storage())?;
    Ok(())
}

async fn mutate_run<F>(
    state: AppState,
    run_id: String,
    mutation: F,
) -> Result<Json<GameState>, ApiError>
where
    F: FnOnce(&mut GameState) -> Result<(), GameError>,
{
    if let Some(pool) = &state.pool {
        let mut transaction = pool.begin().await.map_err(|_| ApiError::database())?;
        let stored: Option<sqlx::types::Json<GameState>> =
            sqlx::query_scalar("SELECT state FROM slotbound_runs WHERE run_id = $1 FOR UPDATE")
                .bind(&run_id)
                .fetch_optional(&mut *transaction)
                .await
                .map_err(|_| ApiError::database())?;
        let mut game = stored.map(|row| row.0).ok_or_else(ApiError::not_found)?;

        mutation(&mut game).map_err(ApiError::from_game)?;

        sqlx::query("UPDATE slotbound_runs SET state = $2, updated_at = now() WHERE run_id = $1")
            .bind(&run_id)
            .bind(sqlx::types::Json(game.clone()))
            .execute(&mut *transaction)
            .await
            .map_err(|_| ApiError::database())?;

        transaction
            .commit()
            .await
            .map_err(|_| ApiError::database())?;
        return Ok(Json(game));
    }

    let mut runs = state.runs.write().await;
    let game = runs.get_mut(&run_id).ok_or_else(ApiError::not_found)?;
    let previous = game.clone();
    if let Err(error) = mutation(game) {
        return Err(ApiError::from_game(error));
    }
    if save_game(&state.data_dir, game).await.is_err() {
        *game = previous;
        return Err(ApiError::storage());
    }
    Ok(Json(game.clone()))
}
async fn index() -> Html<&'static str> {
    Html(include_str!("../../../web/index.html"))
}
async fn javascript() -> Response {
    (
        [(
            axum::http::header::CONTENT_TYPE,
            "text/javascript; charset=utf-8",
        )],
        include_str!("../../../web/app.js"),
    )
        .into_response()
}
async fn stylesheet() -> Response {
    (
        [(axum::http::header::CONTENT_TYPE, "text/css; charset=utf-8")],
        include_str!("../../../web/style.css"),
    )
        .into_response()
}
async fn health(State(state): State<AppState>) -> Json<serde_json::Value> {
    Json(json!({
        "status": "ok",
        "service": "slotbound-api",
        "storage": if state.pool.is_some() { "postgresql" } else { "local_file" }
    }))
}

async fn create_run(
    State(state): State<AppState>,
    Json(body): Json<CreateRun>,
) -> Result<Json<GameState>, ApiError> {
    let id = state.next_id.fetch_add(1, Ordering::Relaxed);
    let seed = body
        .seed
        .unwrap_or_else(|| id.wrapping_mul(0x9E37_79B9_7F4A_7C15));
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    let run_id = format!("run-{seed:016x}-{nonce:x}-{id}");
    let game = GameState::new(seed, run_id.clone());

    if let Some(pool) = &state.pool {
        sqlx::query("INSERT INTO slotbound_runs (run_id, state) VALUES ($1, $2)")
            .bind(&run_id)
            .bind(sqlx::types::Json(game.clone()))
            .execute(pool)
            .await
            .map_err(|_| ApiError::database())?;
    } else {
        save_game(&state.data_dir, &game).await?;
        state.runs.write().await.insert(run_id, game.clone());
    }

    Ok(Json(game))
}
async fn get_run(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GameState>, ApiError> {
    if let Some(pool) = &state.pool {
        let stored: Option<sqlx::types::Json<GameState>> =
            sqlx::query_scalar("SELECT state FROM slotbound_runs WHERE run_id = $1")
                .bind(&run_id)
                .fetch_optional(pool)
                .await
                .map_err(|_| ApiError::database())?;
        return stored
            .map(|row| Json(row.0))
            .ok_or_else(ApiError::not_found);
    }

    state
        .runs
        .read()
        .await
        .get(&run_id)
        .cloned()
        .map(Json)
        .ok_or_else(ApiError::not_found)
}
async fn spin(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.spin().map(|_| ())).await
}

async fn nudge(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<NudgeRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| {
        game.nudge(body.column, body.direction).map(|_| ())
    })
    .await
}

async fn absorb(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<AbsorbRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| {
        game.absorb(body.target_id, body.donor_id)
    })
    .await
}

async fn promotion(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<PromotionRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| {
        game.choose_promotion(body.unit_id, &body.choice)
    })
    .await
}

async fn toggle_lock(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<UnitRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.toggle_lock(body.unit_id)).await
}

async fn battle(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.battle().map(|_| ())).await
}

async fn next_wave(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.next_wave()).await
}

async fn choose_core(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<IndexRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.choose_core(body.index)).await
}

async fn buy_item(
    State(state): State<AppState>,
    Path(run_id): Path<String>,
    Json(body): Json<ItemRequest>,
) -> Result<Json<GameState>, ApiError> {
    mutate_run(state, run_id, |game| game.buy_item(body.item)).await
}

#[tokio::main]
async fn main() {
    let data_dir = default_data_dir();
    let pool = database_pool();

    if let Some(pool) = &pool {
        sqlx::migrate!("./migrations")
            .run(pool)
            .await
            .expect("apply Slotbound PostgreSQL migrations");
    }

    let port = std::env::var("PORT")
        .ok()
        .and_then(|v| v.parse::<u16>().ok())
        .unwrap_or(3000);
    let address = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(address)
        .await
        .expect("bind API listener");
    println!("Slotbound server listening on http://{address}");
    axum::serve(listener, app_with_storage(data_dir, pool))
        .await
        .expect("serve Slotbound API");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::{Request, header},
    };
    use http_body_util::BodyExt;
    use tower::ServiceExt;

    #[tokio::test]
    async fn health_endpoint_is_available() {
        let response = app()
            .oneshot(
                Request::builder()
                    .uri("/healthz")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn create_then_read_run_round_trips() {
        let dir = std::env::temp_dir().join(format!("slotbound-api-test-{}-1", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let router = app_with_data_dir(dir.clone());
        let response = router
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/runs")
                    .header(header::CONTENT_TYPE, "application/json")
                    .body(Body::from(r#"{"seed":42}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        let bytes = response.into_body().collect().await.unwrap().to_bytes();
        let created: GameState = serde_json::from_slice(&bytes).unwrap();
        let spin_uri = format!("/api/runs/{}/spin", created.run_id);
        let spun = router
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri(spin_uri)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(spun.status(), StatusCode::OK);
        let bytes = spun.into_body().collect().await.unwrap().to_bytes();
        let saved_after_spin: GameState = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(saved_after_spin.spins_remaining, 5);
        let uri = format!("/api/runs/{}", created.run_id);
        let response = router
            .clone()
            .oneshot(Request::builder().uri(uri).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        let bytes = response.into_body().collect().await.unwrap().to_bytes();
        let loaded: GameState = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(loaded, saved_after_spin);
        let restored = app_with_data_dir(dir.clone());
        let response = restored
            .oneshot(
                Request::builder()
                    .uri(format!("/api/runs/{}", created.run_id))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        fs::remove_dir_all(dir).unwrap();
    }

    #[tokio::test]
    async fn postgres_storage_survives_a_new_router_instance() {
        let Ok(url) = std::env::var("TEST_DATABASE_URL") else {
            return;
        };
        let pool = PgPoolOptions::new()
            .max_connections(3)
            .connect(&url)
            .await
            .unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();

        let data_dir = std::env::temp_dir().join(format!(
            "slotbound-postgres-test-{}",
            std::process::id()
        ));
        let router = app_with_storage(data_dir.clone(), Some(pool.clone()));
        let created = router.clone().oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/runs")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(r#"{"seed":20261126}"#))
                .unwrap(),
        ).await.unwrap();
        assert_eq!(created.status(), StatusCode::OK);
        let created: GameState =
            serde_json::from_slice(&created.into_body().collect().await.unwrap().to_bytes()).unwrap();

        let spun = router.clone().oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/runs/{}/spin", created.run_id))
                .body(Body::empty())
                .unwrap(),
        ).await.unwrap();
        assert_eq!(spun.status(), StatusCode::OK);
        let expected: GameState =
            serde_json::from_slice(&spun.into_body().collect().await.unwrap().to_bytes()).unwrap();
        assert_eq!(expected.spins_remaining, 5);

        // A new router starts with an empty in-memory cache; the database remains authoritative.
        let restored = app_with_storage(data_dir.clone(), Some(pool.clone()));
        let loaded = restored.oneshot(
            Request::builder()
                .uri(format!("/api/runs/{}", created.run_id))
                .body(Body::empty())
                .unwrap(),
        ).await.unwrap();
        assert_eq!(loaded.status(), StatusCode::OK);
        let actual: GameState =
            serde_json::from_slice(&loaded.into_body().collect().await.unwrap().to_bytes()).unwrap();
        assert_eq!(actual, expected);

        sqlx::query("DELETE FROM slotbound_runs WHERE run_id = $1")
            .bind(&created.run_id)
            .execute(&pool)
            .await
            .unwrap();
    }

    #[tokio::test]
    async fn invalid_phase_returns_conflict_without_mutation() {
        let dir = std::env::temp_dir().join(format!("slotbound-api-test-{}-2", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let router = app_with_data_dir(dir.clone());
        let created = router
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/runs")
                    .header(header::CONTENT_TYPE, "application/json")
                    .body(Body::from(r#"{"seed":8}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        let state: GameState =
            serde_json::from_slice(&created.into_body().collect().await.unwrap().to_bytes())
                .unwrap();
        let uri = format!("/api/runs/{}/battle", state.run_id);
        let first = router
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri(&uri)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(first.status(), StatusCode::OK);
        let second = router
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri(&uri)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(second.status(), StatusCode::CONFLICT);
        fs::remove_dir_all(dir).unwrap();
    }
}
