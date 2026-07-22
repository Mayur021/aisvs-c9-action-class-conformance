"""Reference implementation of reversibility-graded action-class authority.

Public surface:

    from reversibility import (
        ReversibilityClass, ConsequenceTier, Oversight,
        classify, required_oversight, gate, GateResult,
        chain_reversibility, gate_chain,
    )
"""
from .model import (
    ConsequenceTier,
    EVIDENCE_TIER,
    GateResult,
    Oversight,
    ReversibilityClass,
    classify,
    gate,
    required_oversight,
)
from .chain import chain_reversibility, gate_chain

__all__ = [
    "ReversibilityClass",
    "ConsequenceTier",
    "Oversight",
    "EVIDENCE_TIER",
    "GateResult",
    "classify",
    "required_oversight",
    "gate",
    "chain_reversibility",
    "gate_chain",
]

__version__ = "0.1.0"
