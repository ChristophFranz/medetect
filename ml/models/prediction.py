"""Unified JSON-safe prediction schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PredictionRecord:
    image_id: str
    tool: str
    model: str
    defective: bool
    confidence: float
    boxes: list[list[float]] = field(default_factory=list)
    masks: list[dict[str, Any]] = field(default_factory=list)
    instance_scores: list[float] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["confidence"] = float(self.confidence)
        result["latency_ms"] = float(self.latency_ms)
        return result
