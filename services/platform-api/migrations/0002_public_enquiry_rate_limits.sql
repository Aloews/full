-- AUREL staging/public enquiry abuse-control state.
-- The application role may only manage hashed counters; no contact details are stored here.
CREATE TABLE IF NOT EXISTS public.property_enquiry_rate_limits (
    scope text NOT NULL CHECK (scope IN ('ip','email','property')),
    key_hash text NOT NULL CHECK (length(key_hash) = 64),
    window_started_at timestamptz NOT NULL,
    request_count integer NOT NULL CHECK (request_count > 0),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (scope, key_hash)
);
CREATE INDEX IF NOT EXISTS property_enquiry_rate_limits_last_seen_idx
    ON public.property_enquiry_rate_limits(last_seen_at);
GRANT SELECT, INSERT, UPDATE, DELETE
    ON public.property_enquiry_rate_limits TO aurel_app;
