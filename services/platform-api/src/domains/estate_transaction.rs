use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DealRoom {
    pub id: Uuid,
    pub organization_id: Uuid,
    pub property_id: Uuid,
    pub buyer_id: Uuid,
    pub seller_id: Uuid,
    pub status: DealStatus,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum DealStatus { Draft, DueDiligence, Offer, UnderContract, Completed, Cancelled }
