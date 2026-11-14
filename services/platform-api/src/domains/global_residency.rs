use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResidencyCase {
    pub id: Uuid,
    pub client_id: Uuid,
    pub jurisdiction_code: String,
    pub licensed_partner_id: Option<Uuid>,
    pub client_consent: bool,
}
impl ResidencyCase {
    pub fn can_refer_to_partner(&self) -> bool {
        self.client_consent
            && self.licensed_partner_id.is_some()
            && self.jurisdiction_code.len() == 2
    }
}
