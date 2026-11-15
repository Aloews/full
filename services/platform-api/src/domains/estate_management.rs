use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyTask {
    pub id: Uuid,
    pub property_id: Uuid,
    pub vendor_id: Option<Uuid>,
    pub description: String,
    pub estimated_cost_minor: Option<i64>,
    pub owner_approval_required: bool,
    pub owner_approved: bool,
}
impl PropertyTask {
    pub fn can_dispatch(&self) -> bool {
        !self.description.trim().is_empty()
            && (!self.owner_approval_required || self.owner_approved)
            && self.estimated_cost_minor.is_none_or(|v| v >= 0)
    }
}
