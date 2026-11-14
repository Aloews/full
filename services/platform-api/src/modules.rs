use axum::Json;
use serde::Serialize;

#[derive(Serialize)]
pub struct Module {
    pub id: &'static str,
    pub name: &'static str,
    pub domain: &'static str,
    pub phase: &'static str,
}

const MODULES: [Module; 10] = [
    Module { id: "elite-estate", name: "Elite Estate", domain: "property discovery and verified inventory", phase: "foundation" },
    Module { id: "private-buyer", name: "Private Buyer", domain: "buyer mandates and advisory workflow", phase: "planned" },
    Module { id: "estate-studio", name: "Estate Studio", domain: "property media and campaign workflow", phase: "planned" },
    Module { id: "estate-intelligence", name: "Estate Intelligence", domain: "sourced market observations and scenarios", phase: "planned" },
    Module { id: "off-market-club", name: "Off-Market Club", domain: "confidential inventory and access grants", phase: "planned" },
    Module { id: "estate-transaction", name: "Estate Transaction", domain: "diligence and secure deal workflow", phase: "planned" },
    Module { id: "estate-management", name: "Estate Management", domain: "property operations and vendor workflow", phase: "planned" },
    Module { id: "global-residency", name: "Global Residency", domain: "relocation coordination with licensed partners", phase: "planned" },
    Module { id: "developer-intelligence", name: "Developer Intelligence", domain: "developer inventory, leads and sales analytics", phase: "planned" },
    Module { id: "elite-lifestyle", name: "Elite Lifestyle", domain: "vetted concierge provider network", phase: "planned" },
];

pub async fn list() -> Json<Vec<&'static Module>> {
    Json(MODULES.iter().collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn exposes_exactly_ten_product_modules() {
        let Json(items) = list().await;
        assert_eq!(items.len(), 10);
        assert_eq!(items[0].id, "elite-estate");
        assert_eq!(items[9].id, "elite-lifestyle");
    }
}
