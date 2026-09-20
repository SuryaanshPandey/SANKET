"""Clarity: Evidence-grade document information extraction platform & engine."""

from clarity.contract.schemas import (
    EntityContractItem,
    EntityType,
    EventContractItem,
    EventType,
    GraphContractResponse,
    RelationshipContractItem,
    SourceTraceability,
)
from clarity.engine import ClarityEngine

__version__ = "1.10.3"

__all__ = [
    "ClarityEngine",
    "GraphContractResponse",
    "EntityContractItem",
    "EventContractItem",
    "RelationshipContractItem",
    "SourceTraceability",
    "EntityType",
    "EventType",
]
