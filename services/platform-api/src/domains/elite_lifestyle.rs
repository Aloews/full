use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConciergeRequest {
    pub id: Uuid,
    pub client_id: Uuid,
    pub category: String,
    pub details: String,
    pub preferred_provider_id: Option<Uuid>,
    pub client_consent: bool,
}
impl ConciergeRequest {
    pub fn can_route(&self) -> bool {
        self.client_consent && !self.category.trim().is_empty() && !self.details.trim().is_empty()
    }
}
