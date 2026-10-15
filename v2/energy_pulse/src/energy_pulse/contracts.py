"""Versioned input contract and asset/rule registry for synthetic telemetry."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


ASSETS = {
    "PUMP-A102": {"site_id": "SYNTHETIC-SITE-01", "name": "Pump A102"},
    "COMP-B201": {"site_id": "SYNTHETIC-SITE-01", "name": "Compressor B201"},
    "CHILL-C301": {"site_id": "SYNTHETIC-SITE-02", "name": "Chiller C301"},
}

RULES = {
    "temperature": {"version": "temp-high-v1", "operator": ">", "threshold": 80.0, "unit": "C"},
    "vibration": {"version": "vibration-high-v1", "operator": ">", "threshold": 5.5, "unit": "mm/s"},
    "pressure": {"version": "pressure-low-v1", "operator": "<", "threshold": 45.0, "unit": "bar"},
}

UNITS = {"temperature": "C", "vibration": "mm/s", "pressure": "bar"}
CADENCE_MINUTES = 15
LATENESS_HOURS = 48


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    event_id: str
    source_id: str
    asset_id: str
    site_id: str
    observed_at_utc: datetime
    metric: Literal["temperature", "vibration", "pressure"]
    value: float
    unit: Literal["C", "mm/s", "bar"]
    quality: Literal["GOOD", "SUSPECT", "BAD"]
    schema_version: Literal[1]

    @field_validator("event_id", "source_id", "asset_id", "site_id")
    @classmethod
    def validate_identifier(cls, value: str, info) -> str:
        max_length = {"event_id": 160, "source_id": 40, "asset_id": 40, "site_id": 50}[info.field_name]
        if not value or len(value) > max_length or not all(c.isupper() or c.isdigit() or c == "-" for c in value):
            raise ValueError("invalid_identifier")
        return value

    @field_validator("observed_at_utc")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("observed_at_must_be_utc")
        if value.minute % CADENCE_MINUTES or value.second or value.microsecond:
            raise ValueError("observed_at_off_cadence")
        return value.astimezone(timezone.utc)

    @field_validator("value")
    @classmethod
    def validate_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("value_not_finite")
        return value

    @model_validator(mode="after")
    def validate_pair_and_asset(self) -> TelemetryEvent:
        if self.unit != UNITS[self.metric]:
            raise ValueError("metric_unit_mismatch")
        if self.asset_id not in ASSETS:
            raise ValueError("unknown_asset")
        if self.site_id != ASSETS[self.asset_id]["site_id"]:
            raise ValueError("asset_site_mismatch")
        return self


def is_breach(metric: str, value: float) -> bool:
    rule = RULES[metric]
    return value > rule["threshold"] if rule["operator"] == ">" else value < rule["threshold"]
