use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentProject {
    pub id: Uuid,
    pub organization_id: Uuid,
    pub name: String,
    pub jurisdiction_code: String,
    pub inventory_source: String,
}
impl DevelopmentProject {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.name.trim().is_empty() {
            return Err("name_required");
        }
        if self.jurisdiction_code.len() != 2 {
            return Err("invalid_jurisdiction");
        }
        if self.inventory_source.trim().is_empty() {
            return Err("inventory_source_required");
        }
        Ok(())
    }
}
