CREATE TABLE IF NOT EXISTS casino_battle_runs (
    id UUID PRIMARY KEY,
    seed TEXT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS casino_battle_runs_updated_at_idx
    ON casino_battle_runs (updated_at DESC);
