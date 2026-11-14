use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuyerMandate {
    pub id: Uuid,
    pub organization_id: Uuid,
    pub client_id: Uuid,
    pub country_codes: Vec<String>,
    pub budget_min_minor: Option<i64>,
    pub budget_max_minor: Option<i64>,
    pub currency: String,
    pub consent_recorded: bool,
}

impl BuyerMandate {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.country_codes.is_empty() {
            return Err("market_required");
        }
        if self.currency.len() != 3 {
            return Err("invalid_currency");
        }
        if self
            .budget_min_minor
            .zip(self.budget_max_minor)
            .is_some_and(|(min, max)| min > max)
        {
            return Err("invalid_budget_range");
        }
        Ok(())
    }
    pub fn can_start_search(&self) -> bool {
        self.consent_recorded && self.validate().is_ok()
    }
}
