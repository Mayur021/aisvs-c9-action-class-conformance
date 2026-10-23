"""Worst-case reversibility across a composed chain (AISVS C9.2.10, C9.2.11).

A sequence of individually in-scope, reversible steps can still reach an
irreversible terminal outcome that no single step exhibits. Bounding each step
on its own does not bound the chain. The effective class of a composed chain is
therefore the worst-case reversibility reachable across it, and the whole chain
is gated at that tier from commencement, not step by step.

1.01 added two obligations this module also carries. C9.2.10 gained the clause
that the chain must be "established by a component outside the control of the
agent being gated": a fold computed over a set the gated party chose is not a
bound on that party, so provenance is an input here rather than an assumption.
C9.2.11 requires that execution exceeding the approved chain is blocked until a
new approval is obtained, and that the new approval is gated on the worst class
across the CUMULATIVE chain rather than on the extension alone.

Both inputs are optional and can only tighten. Supplying neither leaves every
verdict exactly as it was before they existed, which is the same discipline the
observation axis follows.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .model import (
    ConsequenceTier,
    GateResult,
    Oversight,
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


def _provenance(why: str, established_externally: Optional[bool]) -> str:
    """Record who established the chain's extent, where the caller said.

    Silence is recorded as silence rather than as either answer, so that a
    caller who has not wired this input is not credited with satisfying
    C9.2.10's clause, and is not penalised for it either.
    """
    if established_externally is None:
        return why
    if established_externally:
        return f"{why}; chain extent established outside the gated agent"
    return (
        f"{why}; chain extent supplied by the gated agent, "
        "fold is not a bound on that agent, failed closed"
    )


def gate_chain(
    declared_effects: Iterable[Optional[str]],
    consequences: Optional[Iterable[ConsequenceTier]] = None,
    observations: Optional[Iterable[Optional[Observation]]] = None,
    policy: Optional[ObservationPolicy] = None,
    chain_established_externally: Optional[bool] = None,
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

    `chain_established_externally` carries C9.2.10's 1.01 clause. None means the
    caller has not stated provenance and the verdict is unchanged, so adding this
    input cannot move an existing result. False means the gated agent supplied
    its own chain, in which case the fold is over a set that party chose and is
    not a bound on it: that fails closed and is recorded as a finding. True
    records that an independent component established the extent.
    """
    effects = list(declared_effects)
    step_classes = [classify(e) for e in effects]
    r = chain_reversibility(step_classes)

    c, unaccounted = _chain_consequence(effects, consequences)

    self_established = chain_established_externally is False
    if self_established:
        r = ReversibilityClass.IRREVERSIBLE

    if observations is None:
        ov = required_oversight(r, c)
        return GateResult(
            reversibility=r,
            consequence=c,
            oversight=ov,
            evidence_tier=EVIDENCE_TIER[ov],
            rationale=_append(
                _provenance(
                    f"worst-case across {len(step_classes)} steps: "
                    f"reversibility={r.name.lower()}, gated at commencement",
                    chain_established_externally,
                ),
                unaccounted,
            ),
            binding=None,
            mode="declaration-only",
            finding=self_established,
        )

    obs = list(observations)
    b = chain_binding(effective_binding(o, policy) for o in obs)
    if not declaration_is_usable(b):
        r = ReversibilityClass.IRREVERSIBLE
        why = _append(
            _provenance(
                f"worst-case across {len(step_classes)} steps, stalest link "
                f"binding={b.name.lower()}: declarations not usable, failed closed",
                chain_established_externally,
            ),
            unaccounted,
        )
    else:
        why = _append(
            _provenance(
                f"worst-case across {len(step_classes)} steps: "
                f"reversibility={r.name.lower()}, binding={b.name.lower()}, "
                f"gated at commencement",
                chain_established_externally,
            ),
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
        finding=self_established,
    )


def _common_prefix_len(approved, attempted) -> int:
    n = 0
    for a, b in zip(approved, attempted):
        if a != b:
            break
        n += 1
    return n


def chain_within_approved(
    approved_effects: Iterable[Optional[str]],
    attempted_effects: Iterable[Optional[str]],
) -> bool:
    """Whether an attempted chain stays inside what was approved (C9.2.11).

    Covered means the attempt is a prefix of the approved chain: the same steps,
    in the same order, going no further. Anything else exceeds it, including a
    reordering and a substitution of equal length, because an approval is given
    for a specific sequence and not for a multiset of steps. That is the strict
    reading, and it is the one that fails closed: treating a reordering as
    covered would let an agent reach a later step without the earlier one that
    an approver may have been relying on.
    """
    approved = list(approved_effects)
    attempted = list(attempted_effects)
    if len(attempted) > len(approved):
        return False
    return _common_prefix_len(approved, attempted) == len(attempted)


def gate_chain_extension(
    approved_effects: Iterable[Optional[str]],
    attempted_effects: Iterable[Optional[str]],
    consequences: Optional[Iterable[ConsequenceTier]] = None,
    observations: Optional[Iterable[Optional[Observation]]] = None,
    policy: Optional[ObservationPolicy] = None,
    chain_established_externally: Optional[bool] = None,
) -> GateResult:
    """Gate an attempt against the chain that was actually approved (C9.2.11).

    Where the attempt stays inside the approved chain, the existing approval
    stands and the verdict is the approved chain's own gate.

    Where it exceeds, execution is blocked until a new approval is obtained, and
    that new approval is gated on the CUMULATIVE chain: everything approved plus
    the steps taken beyond the point of divergence. Gating only the extension
    would let a sequence of separately modest additions reach a class the
    original approval never covered, which is the same compositional failure
    C9.2.10 addresses within a single chain.

    The floor for an exceeding attempt is APPROVAL_REQUIRED even where the
    cumulative class would otherwise sit below it, because the control blocks
    the execution until re-approval rather than grading it. The cumulative class
    can raise that floor; it cannot lower it.

    `consequences` and `observations`, where given, run over the cumulative
    chain, since that is the sequence being gated.
    """
    approved = list(approved_effects)
    attempted = list(attempted_effects)

    if chain_within_approved(approved, attempted):
        g = gate_chain(
            approved, consequences, observations, policy,
            chain_established_externally,
        )
        return GateResult(
            reversibility=g.reversibility,
            consequence=g.consequence,
            oversight=g.oversight,
            evidence_tier=g.evidence_tier,
            rationale=(
                f"attempt of {len(attempted)} step(s) stays within the approved "
                f"chain of {len(approved)}; existing approval stands. {g.rationale}"
            ),
            binding=g.binding,
            mode=g.mode,
            finding=g.finding,
        )

    k = _common_prefix_len(approved, attempted)
    cumulative = approved + attempted[k:]
    g = gate_chain(
        cumulative, consequences, observations, policy,
        chain_established_externally,
    )
    ov = Oversight(max(g.oversight, Oversight.APPROVAL_REQUIRED))
    return GateResult(
        reversibility=g.reversibility,
        consequence=g.consequence,
        oversight=ov,
        evidence_tier=EVIDENCE_TIER[ov],
        rationale=(
            f"attempt diverges from the approved chain at step {k + 1}; blocked "
            f"pending new approval, gated on the cumulative chain of "
            f"{len(cumulative)} step(s). {g.rationale}"
        ),
        binding=g.binding,
        mode=g.mode,
        finding=True,
    )
