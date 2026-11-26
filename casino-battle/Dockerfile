FROM rust:1.85-slim AS builder
WORKDIR /workspace
COPY . .
RUN cargo build --release -p casino-battle-server

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --create-home casino
COPY --from=builder /workspace/target/release/casino-battle-server /usr/local/bin/casino-battle-server
USER casino
ENV RUST_LOG=info
EXPOSE 3000
ENTRYPOINT ["/usr/local/bin/casino-battle-server"]
