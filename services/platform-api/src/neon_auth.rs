use std::{sync::Arc, time::{Duration, Instant}};
use jsonwebtoken::{Algorithm, DecodingKey, Validation, decode, decode_header, jwk::{Jwk, JwkSet}};
use reqwest::Client;
use serde::Deserialize;
use sqlx::{PgPool, FromRow};
use tokio::sync::{Mutex, RwLock};
use uuid::Uuid;

#[derive(Clone)]
pub struct NeonAuth {
    jwks_url: String,
    issuer: String,
    client: Client,
    cache: Arc<RwLock<JwksCache>>,
    refresh_lock: Arc<Mutex<()>>,
}

struct JwksCache {
    keys: JwkSet,
    fetched_at: Instant,
}

#[derive(Debug, Deserialize)]
struct Claims {
    sub: Uuid,
    iss: String,
    exp: usize,
}

#[derive(Debug, FromRow)]
struct MembershipRow {
    organization_id: Uuid,
    organization_name: String,
    role: String,
}

impl NeonAuth {
    pub async fn new(jwks_url: String, issuer: String) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        if !jwks_url.starts_with("https://") || !issuer.starts_with("https://") {
            return Err("Neon Auth JWKS and issuer must use HTTPS".into());
        }
        let client = Client::builder()
            .timeout(Duration::from_secs(5))
            .user_agent("aurel-platform-api/0.1")
            .build()?;
        let keys = client.get(&jwks_url).send().await?.error_for_status()?.json::<JwkSet>().await?;
        if keys.keys.is_empty() {
            return Err("Neon Auth JWKS returned no signing keys".into());
        }
        Ok(Self {
            jwks_url,
            issuer,
            client,
            cache: Arc::new(RwLock::new(JwksCache { keys, fetched_at: Instant::now() })),
            refresh_lock: Arc::new(Mutex::new(())),
        })
    }

    async fn key_for(&self, kid: &str) -> Option<Jwk> {
        {
            let cache = self.cache.read().await;
            if cache.fetched_at.elapsed() < Duration::from_secs(600) {
                if let Some(key) = cache.keys.find(kid) {
                    return Some(key.clone());
                }
                if cache.fetched_at.elapsed() < Duration::from_secs(60) {
                    return None;
                }
            }
        }

        let _guard = self.refresh_lock.lock().await;
        {
            let cache = self.cache.read().await;
            if cache.fetched_at.elapsed() < Duration::from_secs(60) {
                return cache.keys.find(kid).cloned();
            }
        }
        let response = self.client.get(&self.jwks_url).send().await.ok()?
            .error_for_status().ok()?;
        let keys = response.json::<JwkSet>().await.ok()?;
        if keys.keys.is_empty() {
            return None;
        }
        let found = keys.find(kid).cloned();
        *self.cache.write().await = JwksCache { keys, fetched_at: Instant::now() };
        found
    }

    pub async fn verify_user(&self, token: &str) -> Option<Uuid> {
        let header = decode_header(token).ok()?;
        if header.alg != Algorithm::EdDSA {
            return None;
        }
        let kid = header.kid.as_deref()?;
        let jwk = self.key_for(kid).await?;
        let key = DecodingKey::from_jwk(&jwk).ok()?;
        let mut validation = Validation::new(Algorithm::EdDSA);
        validation.set_issuer(&[self.issuer.as_str()]);
        validation.validate_aud = false;
        validation.leeway = 30;
        let claims = decode::<Claims>(token, &key, &validation).ok()?.claims;
        if claims.iss != self.issuer || claims.exp == 0 {
            return None;
        }
        Some(claims.sub)
    }

    pub async fn membership(&self, pool: &PgPool, user_id: Uuid, organization_id: Uuid) -> Option<(String, String)> {
        let row = sqlx::query_as::<_, MembershipRow>(
            r#"SELECT o.id AS organization_id, o.name AS organization_name, m.role
               FROM neon_auth.member m
               JOIN neon_auth.organization o ON o.id = m."organizationId"
               WHERE m."userId" = $1 AND m."organizationId" = $2"#
        )
        .bind(user_id)
        .bind(organization_id)
        .fetch_optional(pool)
        .await
        .ok()??;
        let role = match row.role.as_str() {
            "owner" => "owner",
            "admin" => "admin",
            "member" => "broker",
            _ => return None,
        };
        let _ = row.organization_id;
        Some((row.organization_name, role.to_string()))
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn managed_organization_roles_map_to_least_privilege_application_roles() {
        assert_eq!(super::NeonAuth::map_role("owner"), Some("owner"));
        assert_eq!(super::NeonAuth::map_role("admin"), Some("admin"));
        assert_eq!(super::NeonAuth::map_role("member"), Some("broker"));
        assert_eq!(super::NeonAuth::map_role("unknown"), None);
    }
}
