CREATE TABLE IF NOT EXISTS public.slotbound_runs (
    run_id TEXT PRIMARY KEY,
    state JSONB NOT NULL CHECK (jsonb_typeof(state) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS slotbound_runs_updated_at_idx
    ON public.slotbound_runs (updated_at DESC);
