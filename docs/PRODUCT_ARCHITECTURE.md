# AUREL — Product Architecture

## Platform principle
One international platform with ten bounded service modules. The first release prioritizes trusted inventory, buyer mandates and shared client identity.

## Module contracts

| Module | Core records | Initial acceptance criteria |
|---|---|---|
| Elite Estate | Property, media, location, provenance | Publish only reviewed inventory; every material claim has source and verification state |
| Private Buyer | Mandate, criteria, shortlist, viewing | Consent-based mandate lifecycle and advisor assignment |
| Estate Studio | Campaign, asset, approval | Versioned assets, rights metadata and client approval |
| Estate Intelligence | Comparable, observation, scenario | Each metric carries source, timestamp, methodology and confidence |
| Off-Market Club | Opportunity, access grant, NDA | No public indexing; explicit access grants and audit trail |
| Estate Transaction | Deal room, checklist, document | Least-privilege document access and immutable audit events |
| Estate Management | Asset, task, vendor, expense | Owner approvals, vendor controls and expense evidence |
| Global Residency | Case, jurisdiction, referral | No legal/tax advice; licensed partner credentials and scope disclosed |
| Developer Intelligence | Project, unit, lead, funnel | Tenant isolation, inventory sync and funnel provenance |
| Elite Lifestyle | Request, provider, fulfilment | Consent, provider vetting and transparent terms |

## Shared platform services
- Identity and access roles for clients, brokers, owners, developers, advisors, operators and administrators.
- Organization and tenancy isolation for agencies and developers.
- Normalized property master with address, geospatial point, building, unit, media and source records.
- Provenance: source reference, observed timestamp, verification state, reviewer and evidence.
- Multilingual search; confidential inventory excluded without explicit access grant.
- Workflows for mandates, enquiries, viewings, offers, diligence and service requests.
- Append-only audit events for sensitive reads, exports and permission changes.
- Private object storage, short-lived signed links, malware scanning and retention controls.
- Provider adapters with retries, idempotency, rate limits and consent boundaries.

## Verification states
unverified → in_review → verified; rejected and stale are review states. A listing cannot be labelled verified without evidence, reviewer and verification timestamp. Estimates must never be presented as confirmed sale prices.

## Delivery sequence
R0 foundation and data model; R1 Elite Estate + Private Buyer + broker CRM; R2 Off-Market access controls; R3 Estate Transaction + sourced Intelligence; R4 Studio, Management, Residency, Developer and Lifestyle workflows.

## Jurisdictional constraints
Brokerage licensing, AML/KYC, sanctions, privacy, advertising, cross-border data transfers and referral fees vary by jurisdiction. Local counsel and licensed providers must approve operating workflows. The platform must not imply it is a law firm, bank, immigration adviser or licensed broker where it is not.

## Explicit non-goals
No fabricated listings, prices, clients or testimonials; no automated legal conclusions, valuation guarantees or investment-return promises; no public exposure of confidential inventory; no handling of client funds or identity documents before security and compliance approval.
