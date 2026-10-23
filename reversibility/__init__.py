"""Reference implementation of reversibility-graded action-class authority.

Public surface:

    from reversibility import (
        ReversibilityClass, ConsequenceTier, Oversight,
        classify, required_oversight, gate, GateResult,
        chain_reversibility, gate_chain,
        chain_within_approved, gate_chain_extension,
        Binding, Observation, ObservationPolicy, Coverage,
        effective_binding, declaration_is_usable, chain_binding, coverage,
    )
"""
from .model import (
    Supersession,
    supersession_direction,
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
from .chain import (
    chain_reversibility,
    chain_within_approved,
    gate_chain,
    gate_chain_extension,
)
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
    "Supersession",
    "supersession_direction",
    "classify",
    "required_oversight",
    "gate",
    "chain_reversibility",
    "chain_within_approved",
    "gate_chain",
    "gate_chain_extension",
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

__version__ = "1.3.0"
