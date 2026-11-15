use axum::{Json, Router, routing::get};
use serde::Serialize;

use crate::{
    elite_estate_api::{self, AppState},
    modules,
};

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
    service: &'static str,
    version: &'static str,
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        service: "aurel-platform-api",
        version: env!("CARGO_PKG_VERSION"),
    })
}

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/modules", get(modules::list))
        .merge(elite_estate_api::routes(state))
}
