use axum::{
    Json, Router,
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode, request::Parts},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::{get, post},
    Extension,
};
use chrono::{DateTime, Utc};
use jsonwebtoken::{Algorithm, DecodingKey, Validation, decode};
use serde::{Deserialize, Serialize};
use sqlx::{PgPool, Postgres, Transaction};
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    jwt_secret: Vec<u8>,
}

impl AppState {
    pub fn new(pool: PgPool, jwt_secret: String) -> Result<Self, &'static str> {
        if jwt_secret.len() < 32 {
            return Err("AUREL_JWT_SECRET must contain at least 32 bytes");
        }
        Ok(Self { pool, jwt_secret: jwt_secret.into_bytes() })
    }
}

#[derive(Debug, Clone)]
pub struct AuthContext {
    pub actor_id: Uuid,
    pub organization_id: Uuid,
    pub role: String,
}

#[derive(Debug, Deserialize)]
struct Claims {
    sub: Uuid,
    org_id: Uuid,
    role: String,
    exp: usize,
    iss: String,
    aud: String,
}

pub async fn authenticate(
    State(state): State<AppState>,
    mut request: axum::http::Request<axum::body::Body>,
    next: Next,
) -> Response {
    let token = request.headers().get(axum::http::header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.strip_prefix("Bearer "));
    let Some(token) = token else { return StatusCode::UNAUTHORIZED.into_response(); };

    let mut validation = Validation::new(Algorithm::HS256);
    validation.set_issuer(&["aurel"]);
    validation.set_audience(&["aurel-api"]);
    let claims = match decode::<Claims>(token, &DecodingKey::from_secret(&state.jwt_secret), &validation) {
        Ok(data) => data.claims,
        Err(_) => return StatusCode::UNAUTHORIZED.into_response(),
    };
    if claims.iss != "aurel" || claims.aud != "aurel-api" || claims.role.is_empty() {
        return StatusCode::UNAUTHORIZED.into_response();
    }
    request.extensions_mut().insert(AuthContext {
        actor_id: claims.sub,
        organization_id: claims.org_id,
        role: claims.role,
    });
    next.run(request).await
}

#[derive(Debug, Serialize, sqlx::FromRow)]
struct PropertyRow {
    id: Uuid,
    title: String,
    description: String,
    country_code: String,
    city: String,
    property_type: String,
    currency: String,
    asking_price_minor: Option<i64>,
    verification_state: String,
    visibility: String,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateProperty {
    title: String,
    description: String,
    country_code: String,
    city: String,
    property_type: String,
    currency: String,
    asking_price_minor: Option<i64>,
}

impl CreateProperty {
    fn validate(&self) -> Result<(), &'static str> {
        if !(5..=180).contains(&self.title.trim().len()) { return Err("invalid_title"); }
        if !(20..=12000).contains(&self.description.trim().len()) { return Err("invalid_description"); }
        if self.country_code.len() != 2 || !self.country_code.chars().all(|c| c.is_ascii_uppercase()) { return Err("invalid_country_code"); }
        if !(2..=120).contains(&self.city.trim().len()) { return Err("invalid_city"); }
        if !["apartment","house","villa","penthouse","land","commercial","other"].contains(&self.property_type.as_str()) { return Err("invalid_property_type"); }
        if self.currency.len() != 3 || !self.currency.chars().all(|c| c.is_ascii_uppercase()) { return Err("invalid_currency"); }
        if self.asking_price_minor.is_some_and(|value| value <= 0) { return Err("invalid_asking_price"); }
        Ok(())
    }
}

#[derive(Debug, Deserialize)]
struct ListQuery {
    country_code: Option<String>,
    city: Option<String>,
    property_type: Option<String>,
    limit: Option<i64>,
    offset: Option<i64>,
}

#[derive(Debug, Deserialize)]
struct EvidenceInput {
    evidence_type: String,
    source_url: Option<String>,
    reference_code: Option<String>,
    note: String,
    observed_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
struct ReviewInput {
    approved: bool,
    publish: bool,
}

#[derive(Debug, Deserialize)]
struct EnquiryInput {
    name: String,
    email: String,
    message: String,
    consent_recorded: bool,
}

#[derive(Debug, Serialize)]
struct CreatedId { id: Uuid }

#[derive(Debug, Serialize)]
struct ErrorBody { error: &'static str }

fn error(status: StatusCode, code: &'static str) -> Response {
    (status, Json(ErrorBody { error: code })).into_response()
}

async fn tenant_transaction(pool: &PgPool, auth: &AuthContext) -> Result<Transaction<'static, Postgres>, sqlx::Error> {
    let mut tx = pool.begin().await?;
    sqlx::query("SELECT set_config('app.organization_id', $1, true), set_config('app.actor_id', $2, true), set_config('app.role', $3, true)")
        .bind(auth.organization_id.to_string())
        .bind(auth.actor_id.to_string())
        .bind(&auth.role)
        .execute(&mut *tx).await?;
    Ok(tx)
}

fn can_edit(role: &str) -> bool { matches!(role, "owner" | "broker" | "admin") }
fn can_review(role: &str) -> bool { matches!(role, "reviewer" | "admin") }

async fn create_property(
    State(state): State<AppState>,
    Extension(auth): Extension<AuthContext>,
    Json(input): Json<CreateProperty>,
) -> Response {
    if !can_edit(&auth.role) { return error(StatusCode::FORBIDDEN, "insufficient_role"); }
    if let Err(code) = input.validate() { return error(StatusCode::UNPROCESSABLE_ENTITY, code); }
    let mut tx = match tenant_transaction(&state.pool, &auth).await { Ok(tx) => tx, Err(_) => return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error") };
    let row = sqlx::query_as::<_, PropertyRow>(
        "INSERT INTO properties (organization_id, created_by, title, description, country_code, city, property_type, currency, asking_price_minor) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id,title,description,country_code,city,property_type,currency,asking_price_minor,verification_state,visibility,created_at,updated_at"
    )
        .bind(auth.organization_id).bind(auth.actor_id).bind(input.title.trim()).bind(input.description.trim())
        .bind(&input.country_code).bind(input.city.trim()).bind(&input.property_type).bind(&input.currency)
        .bind(input.asking_price_minor).fetch_one(&mut *tx).await;
    let row = match row { Ok(row) => row, Err(_) => return error(StatusCode::UNPROCESSABLE_ENTITY, "property_insert_failed") };
    let _ = sqlx::query("INSERT INTO property_audit_events (organization_id,property_id,actor_id,action,details) VALUES ($1,$2,$3,'property_created','{}'::jsonb)")
        .bind(auth.organization_id).bind(row.id).bind(auth.actor_id).execute(&mut *tx).await;
    if tx.commit().await.is_err() { return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error"); }
    (StatusCode::CREATED, Json(row)).into_response()
}

async fn list_properties(
    State(state): State<AppState>,
    Extension(auth): Extension<AuthContext>,
    Query(query): Query<ListQuery>,
) -> Response {
    let limit = query.limit.unwrap_or(30).clamp(1, 100);
    let offset = query.offset.unwrap_or(0).max(0);
    let mut tx = match tenant_transaction(&state.pool, &auth).await { Ok(tx) => tx, Err(_) => return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error") };
    let rows = sqlx::query_as::<_, PropertyRow>(
        "SELECT id,title,description,country_code,city,property_type,currency,asking_price_minor,verification_state,visibility,created_at,updated_at FROM properties WHERE ($1::text IS NULL OR country_code=$1) AND ($2::text IS NULL OR city ILIKE '%'||$2||'%') AND ($3::text IS NULL OR property_type=$3) ORDER BY updated_at DESC LIMIT $4 OFFSET $5"
    ).bind(query.country_code).bind(query.city).bind(query.property_type).bind(limit).bind(offset).fetch_all(&mut *tx).await;
    match rows {
        Ok(rows) => { if tx.commit().await.is_err() { return error(StatusCode::INTERNAL_SERVER_ERROR,"database_error"); } Json(rows).into_response() }
        Err(_) => error(StatusCode::INTERNAL_SERVER_ERROR, "database_error")
    }
}

async fn add_evidence(
    State(state): State<AppState>,
    Extension(auth): Extension<AuthContext>,
    Path(property_id): Path<Uuid>,
    Json(input): Json<EvidenceInput>,
) -> Response {
    if !can_edit(&auth.role) { return error(StatusCode::FORBIDDEN, "insufficient_role"); }
    if !["ownership","mandate","source_listing","price_confirmation","media_rights","inspection","other"].contains(&input.evidence_type.as_str())
        || !(10..=2000).contains(&input.note.trim().len())
        || input.source_url.as_ref().is_some_and(|url| !url.starts_with("https://") || url.len() > 2048)
        || input.reference_code.as_ref().is_some_and(|value| value.len() > 180) {
        return error(StatusCode::UNPROCESSABLE_ENTITY, "invalid_evidence");
    }
    let mut tx = match tenant_transaction(&state.pool, &auth).await { Ok(tx) => tx, Err(_) => return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error") };
    let result = sqlx::query("INSERT INTO property_evidence (organization_id,property_id,added_by,evidence_type,source_url,reference_code,note,observed_at) SELECT $1,id,$2,$3,$4,$5,$6,$7 FROM properties WHERE id=$8")
        .bind(auth.organization_id).bind(auth.actor_id).bind(input.evidence_type).bind(input.source_url).bind(input.reference_code)
        .bind(input.note.trim()).bind(input.observed_at).bind(property_id).execute(&mut *tx).await;
    match result {
        Ok(result) if result.rows_affected() == 1 => {
            let _ = sqlx::query("INSERT INTO property_audit_events (organization_id,property_id,actor_id,action) VALUES ($1,$2,$3,'evidence_added')")
                .bind(auth.organization_id).bind(property_id).bind(auth.actor_id).execute(&mut *tx).await;
            if tx.commit().await.is_err() { return error(StatusCode::INTERNAL_SERVER_ERROR,"database_error"); }
            StatusCode::CREATED.into_response()
        }
        Ok(_) => error(StatusCode::NOT_FOUND, "property_not_found"),
        Err(_) => error(StatusCode::UNPROCESSABLE_ENTITY, "evidence_insert_failed"),
    }
}

async fn submit_for_review(
    State(state): State<AppState>,
    Extension(auth): Extension<AuthContext>,
    Path(property_id): Path<Uuid>,
) -> Response {
    if !can_edit(&auth.role) { return error(StatusCode::FORBIDDEN, "insufficient_role"); }
    let mut tx = match tenant_transaction(&state.pool, &auth).await { Ok(tx) => tx, Err(_) => return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error") };
    let result = sqlx::query("UPDATE properties p SET verification_state='in_review',visibility='private',reviewed_by=NULL,verified_at=NULL,updated_at=now() WHERE p.id=$1 AND EXISTS (SELECT 1 FROM property_evidence e WHERE e.property_id=p.id)")
        .bind(property_id).execute(&mut *tx).await;
    match result {
        Ok(result) if result.rows_affected()==1 => {
            let _ = sqlx::query("INSERT INTO property_audit_events (organization_id,property_id,actor_id,action) VALUES ($1,$2,$3,'submitted_for_review')")
                .bind(auth.organization_id).bind(property_id).bind(auth.actor_id).execute(&mut *tx).await;
            if tx.commit().await.is_err() { return error(StatusCode::INTERNAL_SERVER_ERROR,"database_error"); }
            StatusCode::ACCEPTED.into_response()
        }
        Ok(_) => error(StatusCode::CONFLICT, "property_missing_or_evidence_required"),
        Err(_) => error(StatusCode::INTERNAL_SERVER_ERROR, "database_error"),
    }
}

async fn review_property(
    State(state): State<AppState>,
    Extension(auth): Extension<AuthContext>,
    Path(property_id): Path<Uuid>,
    Json(input): Json<ReviewInput>,
) -> Response {
    if !can_review(&auth.role) { return error(StatusCode::FORBIDDEN, "reviewer_role_required"); }
    if input.publish && !input.approved { return error(StatusCode::UNPROCESSABLE_ENTITY, "cannot_publish_rejected_property"); }
    let mut tx = match tenant_transaction(&state.pool, &auth).await { Ok(tx) => tx, Err(_) => return error(StatusCode::INTERNAL_SERVER_ERROR, "database_error") };
    let result = sqlx::query("UPDATE properties p SET verification_state=$1,visibility=$2,reviewed_by=$3,verified_at=CASE WHEN $4 THEN now() ELSE NULL END,updated_at=now() WHERE p.id=$5 AND p.created_by<>$3 AND p.verification_state='in_review' AND (NOT $4 OR EXISTS (SELECT 1 FROM property_evidence e WHERE e.property_id=p.id))")
        .bind(if input.approved { "verified" } else { "rejected" })
        .bind(if input.approved && input.publish { "public" } else { "private" })
        .bind(auth.actor_id).bind(input.approved).bind(property_id).execute(&mut *tx).await;
    match result {
        Ok(result) if result.rows_affected()==1 => {
            let action = if input.approved { "property_verified" } else { "property_rejected" };
            let _ = sqlx::query("INSERT INTO property_audit_events (organization_id,property_id,actor_id,action) VALUES ($1,$2,$3,$4)")
                .bind(auth.organization_id).bind(property_id).bind(auth.actor_id).bind(action).execute(&mut *tx).await;
            if tx.commit().await.is_err() { return error(StatusCode::INTERNAL_SERVER_ERROR,"database_error"); }
            StatusCode::OK.into_response()
        }
        Ok(_) => error(StatusCode::CONFLICT, "review_requires_independent_reviewer_and_evidence"),
        Err(_) => error(StatusCode::INTERNAL_SERVER_ERROR, "database_error"),
    }
}

async fn public_properties(
    State(state): State<AppState>,
    Query(query): Query<ListQuery>,
) -> Response {
    let limit = query.limit.unwrap_or(24).clamp(1, 50);
    let offset = query.offset.unwrap_or(0).max(0);
    let rows = sqlx::query_as::<_, PropertyRow>(
        "SELECT id,title,description,country_code,city,property_type,currency,asking_price_minor,verification_state,visibility,created_at,updated_at FROM properties WHERE visibility='public' AND verification_state='verified' AND ($1::text IS NULL OR country_code=$1) AND ($2::text IS NULL OR city ILIKE '%'||$2||'%') AND ($3::text IS NULL OR property_type=$3) ORDER BY updated_at DESC LIMIT $4 OFFSET $5"
    ).bind(query.country_code).bind(query.city).bind(query.property_type).bind(limit).bind(offset).fetch_all(&state.pool).await;
    match rows { Ok(rows)=>Json(rows).into_response(), Err(_)=>error(StatusCode::INTERNAL_SERVER_ERROR,"database_error") }
}

async fn create_enquiry(
    State(state): State<AppState>,
    Path(property_id): Path<Uuid>,
    Json(input): Json<EnquiryInput>,
) -> Response {
    if !input.consent_recorded { return error(StatusCode::UNPROCESSABLE_ENTITY, "consent_required"); }
    if !(2..=120).contains(&input.name.trim().len()) || !(5..=254).contains(&input.email.trim().len())
        || !input.email.contains('@') || !(10..=4000).contains(&input.message.trim().len()) {
        return error(StatusCode::UNPROCESSABLE_ENTITY, "invalid_enquiry");
    }
    let result = sqlx::query("INSERT INTO property_enquiries (property_id,name,email,message,consent_recorded) SELECT id,$2,$3,$4,true FROM properties WHERE id=$1 AND visibility='public' AND verification_state='verified' RETURNING id")
        .bind(property_id).bind(input.name.trim()).bind(input.email.trim().to_lowercase()).bind(input.message.trim())
        .fetch_one(&state.pool).await;
    match result {
        Ok(row) => (StatusCode::CREATED, Json(CreatedId { id: sqlx::Row::get(&row, "id") })).into_response(),
        Err(sqlx::Error::RowNotFound) => error(StatusCode::NOT_FOUND, "public_property_not_found"),
        Err(_) => error(StatusCode::INTERNAL_SERVER_ERROR, "enquiry_failed"),
    }
}

pub fn routes(state: AppState) -> Router {
    let protected = Router::new()
        .route("/properties", get(list_properties).post(create_property))
        .route("/properties/{id}/evidence", post(add_evidence))
        .route("/properties/{id}/submit", post(submit_for_review))
        .route("/properties/{id}/review", post(review_property))
        .route_layer(middleware::from_fn_with_state(state.clone(), authenticate));
    Router::new()
        .route("/public/properties", get(public_properties))
        .route("/public/properties/{id}/enquiries", post(create_enquiry))
        .nest("/api/v1", protected)
        .with_state(state)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_property_rejects_short_descriptions_and_bad_currency() {
        let input = CreateProperty {
            title: "Luxury villa".into(),
            description: "Too short".into(),
            country_code: "MC".into(),
            city: "Monaco".into(),
            property_type: "villa".into(),
            currency: "EURO".into(),
            asking_price_minor: None,
        };
        assert_eq!(input.validate(), Err("invalid_description"));
    }

    #[test]
    fn role_boundaries_are_explicit() {
        assert!(can_edit("broker"));
        assert!(!can_edit("viewer"));
        assert!(can_review("reviewer"));
        assert!(!can_review("broker"));
    }
}
