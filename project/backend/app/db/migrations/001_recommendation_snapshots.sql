-- Additive, idempotent migration; property snapshots remain unchanged.
CREATE TABLE IF NOT EXISTS recommendation_snapshots (
    property_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    request_payload TEXT NOT NULL,
    response_payload TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (property_id, scenario_id)
);
CREATE INDEX IF NOT EXISTS recommendation_snapshots_latest
ON recommendation_snapshots(property_id, updated_at DESC);
