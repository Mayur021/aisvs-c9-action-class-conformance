"""Worst-case reversibility across a composed chain (AISVS C9.2.10).

A sequence of individually in-scope, reversible steps can still reach an
irreversible terminal outcome that no single step exhibits. Bounding each step
on its own does not bound the chain. The effective class of a composed chain is
therefore the worst-case reversibility reachable across it, and the whole chain
is gated at that tier from commencement, not step by step.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .model import (
    ConsequenceTier,
    GateResult,
    ReversibilityClass,
    classify,
    required_oversight,
    EVIDENCE_TIER,
)
from .observation import (
    Binding,
    Observation,
    ObservationPolicy,
    chain_binding,
    declaration_is_usable,
    effective_binding,
)


def chain_reversibility(classes: Iterable[ReversibilityClass]) -> ReversibilityClass:
    """The effective reversibility class of a composed chain.

    Returns the most severe class reachable across the chain. An empty chain has
    no established bound and fails closed to IRREVERSIBLE.
    """
    classes = list(classes)
    if not classes:
        return ReversibilityClass.IRREVERSIBLE
    return ReversibilityClass(max(classes))


def _chain_consequence(effects, consequences):
    """The chain's consequence tier, and why, when the axis is not fully given.

    A step the caller said nothing about is unaccounted, not low. Defaulting it
    to the weakest tier lets an omission buy a softer gate, which is the same
    fail-open shape as an undeclared class defaulting to reversible. Every
    shortfall resolves to the strongest tier instead, and the basis is recorded
    so a reader can tell a gate that was strengthened by omission from one the
    caller actually asked for.

    Declining the axis outright (consequences=None) lands on the same verdict
    with a different recorded basis: the caller declined, rather than supplied a
    list that did not cover the chain.
    """
    n = len(effects)
    if consequences is None:
        return ConsequenceTier.CRITICAL, (
            "consequence axis declined, all "
            f"{n} step(s) unaccounted, resolved to the strongest tier"
        )
    cons = list(consequences)
    if len(cons) != n:
        return ConsequenceTier.CRITICAL, (
            f"{len(cons)} consequence(s) for {n} step(s), unaccounted, "
            "resolved to the strongest tier"
        )
    if not cons:
        return ConsequenceTier.CRITICAL, (
            "empty chain, nothing accounted, resolved to the strongest tier"
        )
    return ConsequenceTier(max(cons)), None


def _append(why: str, unaccounted: Optional[str]) -> str:
    return why if unaccounted is None else f"{why}; consequence: {unaccounted}"


def gate_chain(
    declared_effects: Iterable[Optional[str]],
    consequences: Optional[Iterable[ConsequenceTier]] = None,
    observations: Optional[Iterable[Optional[Observation]]] = None,
    policy: Optional[ObservationPolicy] = None,
) -> GateResult:
    """Gate a composed chain on its worst-case reachable class from the start.

    Each step is classified from its declared effect (undeclared fails closed).
    The chain's oversight is computed from the worst-case reversibility and the
    worst-case consequence reachable anywhere in the chain. A step carrying no
    consequence is unaccounted rather than low, and every unaccounted step
    resolves to the strongest tier, so an omission cannot buy a softer gate.

    Where observations are supplied, the chain is also as stale as its stalest
    link: the same worst-case rule applied to a second axis. A chain containing
    one step whose declaration is no longer bound is gated as though that step
    were unclassified, because it is.
    """
    effects = list(declared_effects)
    step_classes = [classify(e) for e in effects]
    r = chain_reversibility(step_classes)

    c, unaccounted = _chain_consequence(effects, consequences)

    if observations is None:
        ov = required_oversight(r, c)
        return GateResult(
            reversibility=r,
            consequence=c,
            oversight=ov,
            evidence_tier=EVIDENCE_TIER[ov],
            rationale=_append(
                f"worst-case across {len(step_classes)} steps: "
                f"reversibility={r.name.lower()}, gated at commencement",
                unaccounted,
            ),
            binding=None,
            mode="declaration-only",
        )

    obs = list(observations)
    b = chain_binding(effective_binding(o, policy) for o in obs)
    if not declaration_is_usable(b):
        r = ReversibilityClass.IRREVERSIBLE
        why = _append(
            f"worst-case across {len(step_classes)} steps, stalest link "
            f"binding={b.name.lower()}: declarations not usable, failed closed",
            unaccounted,
        )
    else:
        why = _append(
            f"worst-case across {len(step_classes)} steps: "
            f"reversibility={r.name.lower()}, binding={b.name.lower()}, "
            f"gated at commencement",
            unaccounted,
        )
    ov = required_oversight(r, c)
    return GateResult(
        reversibility=r,
        consequence=c,
        oversight=ov,
        evidence_tier=EVIDENCE_TIER[ov],
        rationale=why,
        binding=b,
        mode="declaration+observation",
    )
