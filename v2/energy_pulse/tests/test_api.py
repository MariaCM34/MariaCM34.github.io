from fastapi.testclient import TestClient

from energy_pulse.api import create_app
from energy_pulse.pipeline import build, ingest
from energy_pulse.producer import produce
from datetime import datetime, timezone


def test_api_reads_persisted_lineage_and_rejects_bad_filters(tmp_path):
    source = tmp_path / "events.jsonl"
    db = tmp_path / "energy.sqlite"
    produce(source, slots=12)
    ingest(db, source)
    build(db, start=datetime(2026, 10, 15, tzinfo=timezone.utc), slots=12)
    client = TestClient(create_app(db))
    assert client.get("/health").json() == {"status": "ok", "schema_version": 1, "synthetic": True}
    readings = client.get("/api/measurements", params={"asset_id": "PUMP-A102", "metric": "temperature"}).json()
    assert len(readings["items"]) == 12
    assert readings["items"][5]["value"] == 84.3
    incident = client.get("/api/incidents").json()["items"][0]
    lineage = client.get(f"/api/incidents/{incident['incident_id']}/lineage").json()
    assert lineage["measurement"]["event_id"] == lineage["raw"]["event_id"] == incident["first_event_id"]
    assert lineage["measurement"]["value"] == 84.3
    assert lineage["gold"]["received_samples"] == 4
    assert [t["state"] for t in lineage["transitions"]] == ["OPEN", "CLOSED"]
    assert client.get("/api/measurements", params={"asset_id": "UNKNOWN", "metric": "temperature"}).status_code == 422
    assert client.get("/api/quality", params={"limit": 5000}).status_code == 422
    assert client.get("/api/incidents/UNKNOWN/lineage").status_code == 404
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200
