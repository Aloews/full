CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE organizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 160),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE properties (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id),
    created_by uuid NOT NULL,
    reviewed_by uuid,
    title text NOT NULL CHECK (length(trim(title)) BETWEEN 5 AND 180),
    description text NOT NULL CHECK (length(trim(description)) BETWEEN 20 AND 12000),
    country_code char(2) NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
    city text NOT NULL CHECK (length(trim(city)) BETWEEN 2 AND 120),
    property_type text NOT NULL CHECK (property_type IN ('apartment','house','villa','penthouse','land','commercial','other')),
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    asking_price_minor bigint CHECK (asking_price_minor IS NULL OR asking_price_minor > 0),
    verification_state text NOT NULL DEFAULT 'unverified' CHECK (verification_state IN ('unverified','in_review','verified','rejected','stale')),
    visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private','public','off_market')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    verified_at timestamptz,
    CHECK (verification_state <> 'verified' OR (reviewed_by IS NOT NULL AND verified_at IS NOT NULL)),
    CHECK (visibility <> 'public' OR verification_state = 'verified')
);
CREATE TABLE property_evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES organizations(id),
    property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    added_by uuid NOT NULL,
    evidence_type text NOT NULL CHECK (evidence_type IN ('ownership','mandate','source_listing','price_confirmation','media_rights','inspection','other')),
    source_url text CHECK (source_url IS NULL OR (length(source_url) <= 2048 AND source_url ~ '^https://')),
    reference_code text CHECK (reference_code IS NULL OR length(reference_code) <= 180),
    note text NOT NULL CHECK (length(trim(note)) BETWEEN 10 AND 2000),
    observed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE property_audit_events (
    id bigserial PRIMARY KEY,
    organization_id uuid NOT NULL REFERENCES organizations(id),
    property_id uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    actor_id uuid NOT NULL,
    action text NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE property_enquiries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id uuid NOT NULL REFERENCES properties(id),
    name text NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 120),
    email text NOT NULL CHECK (length(trim(email)) BETWEEN 5 AND 254),
    message text NOT NULL CHECK (length(trim(message)) BETWEEN 10 AND 4000),
    consent_recorded boolean NOT NULL CHECK (consent_recorded = true),
    created_at timestamptz NOT NULL DEFAULT now(),
    status text NOT NULL DEFAULT 'new' CHECK (status IN ('new','assigned','contacted','closed','spam'))
);
CREATE INDEX properties_org_updated_idx ON properties (organization_id, updated_at DESC);
CREATE INDEX properties_public_search_idx ON properties (country_code, city, property_type) WHERE verification_state = 'verified' AND visibility = 'public';
CREATE INDEX property_evidence_property_idx ON property_evidence (property_id, created_at DESC);
CREATE INDEX property_audit_property_idx ON property_audit_events (property_id, created_at DESC);
CREATE INDEX property_enquiries_property_idx ON property_enquiries (property_id, created_at DESC);

ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties FORCE ROW LEVEL SECURITY;
ALTER TABLE property_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_evidence FORCE ROW LEVEL SECURITY;
ALTER TABLE property_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_audit_events FORCE ROW LEVEL SECURITY;
ALTER TABLE property_enquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_enquiries FORCE ROW LEVEL SECURITY;

CREATE POLICY properties_tenant_access ON properties
  USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
  WITH CHECK (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY properties_public_read ON properties FOR SELECT
  USING (visibility = 'public' AND verification_state = 'verified' AND reviewed_by IS NOT NULL);

CREATE POLICY evidence_tenant_access ON property_evidence
  USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
  WITH CHECK (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY evidence_public_read ON property_evidence FOR SELECT
  USING (EXISTS (SELECT 1 FROM properties p WHERE p.id = property_evidence.property_id
    AND p.visibility = 'public' AND p.verification_state = 'verified' AND p.reviewed_by IS NOT NULL));

CREATE POLICY audit_tenant_access ON property_audit_events
  USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
  WITH CHECK (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY enquiries_tenant_read ON property_enquiries FOR SELECT
  USING (EXISTS (SELECT 1 FROM properties p WHERE p.id = property_enquiries.property_id
    AND p.organization_id = nullif(current_setting('app.organization_id', true), '')::uuid));
CREATE POLICY enquiries_public_insert ON property_enquiries FOR INSERT
  WITH CHECK (consent_recorded = true AND EXISTS (SELECT 1 FROM properties p WHERE p.id = property_enquiries.property_id
    AND p.visibility = 'public' AND p.verification_state = 'verified'));

CREATE OR REPLACE FUNCTION prevent_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_events_are_append_only';
END;
$$;
CREATE TRIGGER property_audit_no_update BEFORE UPDATE OR DELETE ON property_audit_events
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

CREATE OR REPLACE FUNCTION enforce_property_publication_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.verification_state = 'verified' OR NEW.visibility = 'public' THEN
    IF NEW.reviewed_by IS NULL OR NEW.reviewed_by = NEW.created_by THEN
      RAISE EXCEPTION 'independent_reviewer_required';
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM property_evidence e
      WHERE e.property_id = NEW.id AND e.organization_id = NEW.organization_id
    ) THEN
      RAISE EXCEPTION 'property_evidence_required';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER property_publication_requires_evidence
  BEFORE INSERT OR UPDATE OF verification_state, visibility, reviewed_by
  ON properties FOR EACH ROW EXECUTE FUNCTION enforce_property_publication_evidence();

CREATE OR REPLACE FUNCTION prevent_evidence_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'property_evidence_is_append_only';
END;
$$;
CREATE TRIGGER property_evidence_no_update_or_delete
  BEFORE UPDATE OR DELETE ON property_evidence
  FOR EACH ROW EXECUTE FUNCTION prevent_evidence_mutation();
