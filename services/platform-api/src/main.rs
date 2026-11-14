use std::{env, net::SocketAddr};
use aurel_platform_api::routes;
use tokio::net::TcpListener;
use tower_http::{limit::RequestBodyLimitLayer, trace::TraceLayer};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "aurel_platform_api=info,tower_http=info".into()))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    let address: SocketAddr = format!("0.0.0.0:{}", env::var("PORT").unwrap_or_else(|_| "8080".into())).parse()?;
    let app = routes::router()
        .layer(RequestBodyLimitLayer::new(1_048_576))
        .layer(TraceLayer::new_for_http());

    let listener = TcpListener::bind(address).await?;
    tracing::info!(%address, "AUREL Rust API listening");
    axum::serve(listener, app).with_graceful_shutdown(shutdown_signal()).await?;
    Ok(())
}

async fn shutdown_signal() {
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("shutdown signal received");
}
