use aurel_platform_api::{elite_estate_api::AppState, neon_auth::NeonAuth, routes};
use axum::http::{HeaderValue, Method, header};
use sqlx::postgres::PgPoolOptions;
use std::{env, net::SocketAddr};
use tokio::net::TcpListener;
use tower_http::{cors::CorsLayer, limit::RequestBodyLimitLayer, trace::TraceLayer};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "aurel_platform_api=info,tower_http=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    let database_url = env::var("DATABASE_URL").map_err(|_| {
        std::io::Error::other(
            "DATABASE_URL is required; configure a dedicated AUREL PostgreSQL database",
        )
    })?;
    let auth_base_url = env::var("NEON_AUTH_BASE_URL")
        .map_err(|_| std::io::Error::other("NEON_AUTH_BASE_URL is required"))?;
    let jwks_url = env::var("NEON_AUTH_JWKS_URL")
        .unwrap_or_else(|_| format!("{}/.well-known/jwks.json", auth_base_url.trim_end_matches('/')));
    let web_origin = env::var("AUREL_WEB_ORIGIN")
        .map_err(|_| std::io::Error::other("AUREL_WEB_ORIGIN is required"))?;
    let allowed_origin: HeaderValue = web_origin.parse()?;
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await?;
    sqlx::migrate!("./migrations").run(&pool).await?;
    let neon_auth = NeonAuth::new(jwks_url, auth_base_url).await?;
    let state = AppState::new(pool, neon_auth);

    let address: SocketAddr = format!(
        "0.0.0.0:{}",
        env::var("PORT").unwrap_or_else(|_| "8080".into())
    )
    .parse()?;
    let cors = CorsLayer::new()
        .allow_origin(allowed_origin)
        .allow_methods([Method::GET, Method::POST])
        .allow_headers([header::AUTHORIZATION, header::CONTENT_TYPE]);
    let app = routes::router(state)
        .layer(cors)
        .layer(RequestBodyLimitLayer::new(1_048_576))
        .layer(TraceLayer::new_for_http());

    let listener = TcpListener::bind(address).await?;
    tracing::info!(%address, "AUREL Rust API listening");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

async fn shutdown_signal() {
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("shutdown signal received");
}
