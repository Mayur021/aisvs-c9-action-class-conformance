"""Reference model for reversibility-graded action-class authority.

Implements the classification and gating primitives behind OWASP AISVS v1.0
chapter C9 (Orchestration & Agentic Security):

  - C9.2.3  trusted reversibility classification
  - C9.2.4  runtime enforcement by class
  - C9.5.3  the decision is enforced by policy, never by the model itself

Design commitments this reference makes explicit (the places implementations
commonly diverge):

  1. Four classes, including the two that are usually lost:
     read-only, reversible, EXTERNALLY REVERSIBLE, IRREVERSIBLE.
  2. Reversibility and consequence are INDEPENDENT axes. Required oversight is
     a function of both, taking the worse of the two, not one collapsed scale.
  3. Fail-closed: an action whose class cannot be determined is treated as the
     most restrictive class, so omitting the classification cannot lower the bar.
  4. The class is derived from the tool's declared effect or policy, never
     asserted by the agent at runtime.
  5. A declaration is usable only while it is still bound to the contract it was
     declared against. Observation is optional; where it is absent the model
     runs declaration-only and behaves exactly as it did before that input
     existed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from .observation import (
    Binding,
    Observation,
    ObservationPolicy,
    declaration_is_usable,
    effective_binding,
)


class ReversibilityClass(IntEnum):
    """The four-class reversibility ladder (AISVS C9.2.3 vocabulary).

    Ordered least-to-most severe; a higher value is harder to walk back.
    """

    READ_ONLY = 0              # observes state, changes nothing
    REVERSIBLE = 1            # recoverable local state you can restore yourself
    EXTERNALLY_REVERSIBLE = 2  # recoverable only by a party other than you
    IRREVERSIBLE = 3          # cannot be walked back once it runs


class ConsequenceTier(IntEnum):
    """Blast radius / impact. A SEPARATE axis from reversibility."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Oversight(IntEnum):
    """Required human involvement, ordered least-to-most."""

    UNATTENDED = 0         # the agent may run this without a human
    SUPERVISED = 1         # human on the loop, able to intervene
    APPROVAL_REQUIRED = 2  # a human approves before it runs
    HUMAN_OWNS = 3         # a named human owns the call; the strongest gate


# Evidence tier names, indexed by Oversight level. Evidence strength rises with
# the required oversight, so there is a distinct top tier for the hardest gate.
EVIDENCE_TIER = {
    Oversight.UNATTENDED: "basic",
    Oversight.SUPERVISED: "standard",
    Oversight.APPROVAL_REQUIRED: "enhanced",
    Oversight.HUMAN_OWNS: "highest",
}

# The tool's declared effect maps to a reversibility class. Anything not in this
# table (including None) fails closed to IRREVERSIBLE.
_DECLARED_EFFECT = {
    "read_only": ReversibilityClass.READ_ONLY,
    "recoverable_local": ReversibilityClass.REVERSIBLE,
    "externally_recoverable": ReversibilityClass.EXTERNALLY_REVERSIBLE,
    "non_recoverable": ReversibilityClass.IRREVERSIBLE,
    "externally_visible": ReversibilityClass.IRREVERSIBLE,
}


def classify(declared_effect: Optional[str]) -> ReversibilityClass:
    """Derive the reversibility class from a tool's declared effect or policy.

    The input is the effect the tool registry declares, never the agent's own
    account of what it did. An undeclared or unrecognised effect fails closed to
    IRREVERSIBLE so that omitting the class cannot quietly lower the gate.
    """
    if declared_effect is None:
        return ReversibilityClass.IRREVERSIBLE
    try:
        return _DECLARED_EFFECT.get(declared_effect, ReversibilityClass.IRREVERSIBLE)
    except TypeError:
        # An unhashable effect is certainly not one the registry defines. This
        # is the decision path, so it takes the same fail-closed exit as any
        # other unrecognised input: a caller that reads the exception as "no
        # policy applied" would turn the raise into an open gate.
        return ReversibilityClass.IRREVERSIBLE


def _oversight_from_reversibility(r: ReversibilityClass) -> Oversight:
    return {
        ReversibilityClass.READ_ONLY: Oversight.UNATTENDED,
        ReversibilityClass.REVERSIBLE: Oversight.SUPERVISED,
        ReversibilityClass.EXTERNALLY_REVERSIBLE: Oversight.APPROVAL_REQUIRED,
        ReversibilityClass.IRREVERSIBLE: Oversight.HUMAN_OWNS,
    }[r]


def _oversight_from_consequence(c: ConsequenceTier) -> Oversight:
    return {
        ConsequenceTier.LOW: Oversight.UNATTENDED,
        ConsequenceTier.MEDIUM: Oversight.SUPERVISED,
        ConsequenceTier.HIGH: Oversight.APPROVAL_REQUIRED,
        ConsequenceTier.CRITICAL: Oversight.HUMAN_OWNS,
    }[c]


def required_oversight(
    reversibility: ReversibilityClass,
    consequence: ConsequenceTier = ConsequenceTier.LOW,
) -> Oversight:
    """Oversight required for an action, as a function of BOTH axes.

    The two axes are independent; the requirement is the worse of the two. A
    low-consequence but irreversible action still lands on the hard gate, and a
    high-consequence but fully reversible action is still elevated by its blast
    radius. Neither axis alone is sufficient.
    """
    return Oversight(
        max(
            _oversight_from_reversibility(reversibility),
            _oversight_from_consequence(consequence),
        )
    )


@dataclass(frozen=True)
class GateResult:
    reversibility: ReversibilityClass
    consequence: ConsequenceTier
    oversight: Oversight
    evidence_tier: str
    rationale: str
    binding: Optional[Binding] = None
    mode: str = "declaration-only"


def recognised_effect(declared_effect: Optional[str]) -> bool:
    """Whether the registry actually defines this effect.

    An unrecognised string is not a classification, so it counts against
    declared coverage rather than for it.
    """
    if declared_effect is None:
        return False
    try:
        return declared_effect in _DECLARED_EFFECT
    except TypeError:
        # Same reasoning as classify: gate() calls both, so a guard on only one
        # of them leaves the raise on the decision path.
        return False


def gate(
    declared_effect: Optional[str],
    consequence: ConsequenceTier = ConsequenceTier.LOW,
    observation: Optional[Observation] = None,
    policy: Optional[ObservationPolicy] = None,
) -> GateResult:
    """Classify an action and return the gate decision for it.

    Enforcement is deterministic and lives outside the agent: this function is
    the policy the agent's proposed action is checked against, it does not ask
    the agent what it thinks the class should be.

    Two modes, and the default is unchanged from earlier releases.

    Declaration-only, when no observation is supplied: the decision rests on the
    declared class alone, exactly as before. Results recorded against a
    declaration-only run remain valid.

    Declaration plus observation, when one is supplied: the declaration is used
    only while it is still bound to the contract it was declared against. A
    STALE or UNOBSERVED binding makes the declaration unusable, and the action
    takes the same fail-closed path as an undeclared one. Passing no observation
    is not the same as observing nothing: the first says this run has no
    observation layer, the second says the layer looked and could not attest.
    """
    r = classify(declared_effect)
    known = recognised_effect(declared_effect)

    if observation is None:
        ov = required_oversight(r, consequence)
        why = (
            "class undeclared or unrecognised, failed closed to irreversible"
            if not known
            else (
                f"reversibility={r.name.lower()}, consequence={consequence.name.lower()}, "
                f"oversight is the worse of the two axes"
            )
        )
        return GateResult(
            reversibility=r,
            consequence=consequence,
            oversight=ov,
            evidence_tier=EVIDENCE_TIER[ov],
            rationale=why,
            binding=None,
            mode="declaration-only",
        )

    b = effective_binding(observation, policy)
    if not declaration_is_usable(b):
        r = ReversibilityClass.IRREVERSIBLE
        why = (
            f"declaration not usable: binding={b.name.lower()}, "
            f"failed closed to irreversible"
        )
    elif not known:
        why = "class undeclared or unrecognised, failed closed to irreversible"
    else:
        why = (
            f"reversibility={r.name.lower()}, consequence={consequence.name.lower()}, "
            f"binding={b.name.lower()}, oversight is the worse of the two axes"
        )
    ov = required_oversight(r, consequence)
    return GateResult(
        reversibility=r,
        consequence=consequence,
        oversight=ov,
        evidence_tier=EVIDENCE_TIER[ov],
        rationale=why,
        binding=b,
        mode="declaration+observation",
    )
