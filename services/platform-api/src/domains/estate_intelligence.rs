use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketObservation {
    pub id: Uuid,
    pub market_code: String,
    pub metric: String,
    pub value: f64,
    pub currency: Option<String>,
    pub source_uri: String,
    pub observed_at: String,
    pub methodology: String,
}
impl MarketObservation {
    pub fn is_publishable(&self) -> bool {
        self.value.is_finite()
            && !self.metric.trim().is_empty()
            && !self.source_uri.trim().is_empty()
            && !self.observed_at.trim().is_empty()
            && !self.methodology.trim().is_empty()
    }
}
