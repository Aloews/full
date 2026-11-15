use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum VerificationState {
    Unverified,
    InReview,
    Verified,
    Rejected,
    Stale,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Property {
    pub id: Uuid,
    pub organization_id: Uuid,
    pub title: String,
    pub country_code: String,
    pub currency: String,
    pub asking_price_minor: Option<i64>,
    pub verification: VerificationState,
}

impl Property {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.title.trim().is_empty() {
            return Err("title_required");
        }
        if self.country_code.len() != 2
            || !self.country_code.chars().all(|c| c.is_ascii_uppercase())
        {
            return Err("invalid_country_code");
        }
        if self.currency.len() != 3 || !self.currency.chars().all(|c| c.is_ascii_uppercase()) {
            return Err("invalid_currency");
        }
        if self.asking_price_minor.is_some_and(|v| v <= 0) {
            return Err("invalid_asking_price");
        }
        Ok(())
    }

    pub fn can_be_public(&self, has_evidence: bool, reviewed_by: Option<Uuid>) -> bool {
        self.verification == VerificationState::Verified && has_evidence && reviewed_by.is_some()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unverified_property_cannot_be_public() {
        let property = Property {
            id: Uuid::nil(),
            organization_id: Uuid::nil(),
            title: "Villa".into(),
            country_code: "MC".into(),
            currency: "EUR".into(),
            asking_price_minor: Some(1_000_000),
            verification: VerificationState::Unverified,
        };
        assert!(!property.can_be_public(true, Some(Uuid::new_v4())));
    }
}
