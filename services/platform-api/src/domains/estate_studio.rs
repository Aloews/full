use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Campaign {
    pub id: Uuid,
    pub organization_id: Uuid,
    pub property_id: Uuid,
    pub title: String,
    pub approved_by_client: bool,
    pub rights_confirmed: bool,
}
impl Campaign {
    pub fn can_publish(&self) -> bool {
        !self.title.trim().is_empty() && self.approved_by_client && self.rights_confirmed
    }
}
