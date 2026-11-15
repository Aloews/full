use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessGrant {
    pub opportunity_id: Uuid,
    pub grantee_id: Uuid,
    pub granted_by: Uuid,
    pub nda_accepted: bool,
    pub expires_at: String,
}
impl AccessGrant {
    pub fn allows_access(&self, now_iso: &str) -> bool {
        self.nda_accepted && self.expires_at.as_str() > now_iso
    }
}
