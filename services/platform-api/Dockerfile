FROM rust:1.88-bookworm AS builder
WORKDIR /app
COPY Cargo.toml ./
COPY services/platform-api/Cargo.toml services/platform-api/Cargo.toml
COPY services/platform-api/src services/platform-api/src
RUN cargo build --release -p aurel-platform-api

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 --create-home app
COPY --from=builder /app/target/release/aurel-platform-api /usr/local/bin/aurel-platform-api
USER app
ENV PORT=8080
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/aurel-platform-api"]
