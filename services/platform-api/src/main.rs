use aurel_platform_api::{elite_estate_api::AppState, routes};
use sqlx::postgres::PgPoolOptions;
use std::{env, net::SocketAddr};
use tokio::net::TcpListener;
use tower_http::{limit::RequestBodyLimitLayer, trace::TraceLayer};
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

    let database_url = env::var("DATABASE_URL")
        .map_err(|_| "DATABASE_URL is required; configure a dedicated AUREL PostgreSQL database")?;
    let jwt_secret = env::var("AUREL_JWT_SECRET").map_err(|_| "AUREL_JWT_SECRET is required")?;
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await?;
    sqlx::migrate!("./migrations").run(&pool).await?;
    let state = AppState::new(pool, jwt_secret)?;

    let address: SocketAddr = format!(
        "0.0.0.0:{}",
        env::var("PORT").unwrap_or_else(|_| "8080".into())
    )
    .parse()?;
    let app = routes::router(state)
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
