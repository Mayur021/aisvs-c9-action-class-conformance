"""Reference implementation of reversibility-graded action-class authority.

Public surface:

    from reversibility import (
        ReversibilityClass, ConsequenceTier, Oversight,
        classify, required_oversight, gate, GateResult,
        chain_reversibility, gate_chain,
        Binding, Observation, ObservationPolicy, Coverage,
        effective_binding, declaration_is_usable, chain_binding, coverage,
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
from .model import recognised_effect
from .chain import chain_reversibility, gate_chain
from .observation import (
    Binding,
    Coverage,
    Observation,
    ObservationPolicy,
    chain_binding,
    coverage,
    declaration_is_usable,
    effective_binding,
)

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
    "recognised_effect",
    "Binding",
    "Observation",
    "ObservationPolicy",
    "Coverage",
    "effective_binding",
    "declaration_is_usable",
    "chain_binding",
    "coverage",
]

__version__ = "1.2.0"
