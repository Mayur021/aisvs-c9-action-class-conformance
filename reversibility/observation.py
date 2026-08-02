"""Observation of whether a declaration is still bound to the contract it was
declared against.

The classification in `model` grades what an action's registry entry SAYS the
action does. That is a declaration, and a declaration made against a contract
that has since mutated is not evidence about the action running today. This
module carries the second input: whether the declaration is still bound.

What this module does NOT claim. An observation here is not a witness of
execution. Nothing observes the action running, and no runtime effect is
compared against the declared one. The failure this models is declaration
STALENESS, not declaration falsity: the declaration was made against a contract
that no longer exists.

Three commitments, each chosen against a specific failure mode:

  1. Corroboration is a count, not a fact, and the threshold belongs to whoever
     knows the observers. This module takes only observations that have already
     cleared a producer's threshold, so the core holds no producer-specific
     semantics.
  2. Absence is not agreement. UNOBSERVED is a third state, not a synonym for
     BOUND. A corpus in which most entries never change is mostly silent, and
     reading silence as conformance manufactures false comfort at exactly the
     scale where it matters.
  3. Observations expire. Conformance tested against a stale observation is
     worse than untested because it reads as verified, so an observation carries
     an as-of time and ages out to UNOBSERVED on a clock.

The clock is deliberate. Ranking entries by prior drift and re-auditing the top
slice cannot substitute for it. Where most of a population has no change history
at all, a ranking built on prior change has a signal pool smaller than the audit
budget: coverage caps early, and a large share of changes land on entries the
ranking never reaches at any budget. A clock reaches every entry eventually. A
ranking reaches only the entries that have already moved.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Iterable, Optional, Sequence, Tuple


class Binding(IntEnum):
    """Whether a declaration is still bound to the contract it was made against.

    Ordered least-to-most doubtful, matching the convention in `model` that a
    higher value is the worse case.
    """

    BOUND = 0        # the contract the declaration was made against is still in force
    STALE = 1        # the contract mutated after the declaration was made
    UNOBSERVED = 2   # not enough independent observation to say either way


@dataclass(frozen=True)
class Observation:
    """A binding state that has already cleared the producer's threshold.

    `observed_as_of` is when the producer last had grounds for this state. It is
    required for BOUND, because a bound state with no age cannot be aged out and
    would read as permanently verified.
    """

    binding: Binding
    observed_as_of: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.binding is Binding.BOUND and self.observed_as_of is None:
            raise ValueError(
                "a BOUND observation must carry observed_as_of; without it the "
                "observation cannot expire and would read as permanently verified"
            )


@dataclass(frozen=True)
class ObservationPolicy:
    """How the consumer ages observations out.

    `max_age` of None means observations never expire, which is only honest for
    a corpus you re-observe continuously. `now` is injected so a conformance run
    is reproducible rather than dependent on when it was executed.
    """

    max_age: Optional[timedelta] = None
    now: Optional[datetime] = None

    def _now(self) -> datetime:
        return self.now if self.now is not None else datetime.now(timezone.utc)


def effective_binding(
    observation: Optional[Observation],
    policy: Optional[ObservationPolicy] = None,
) -> Binding:
    """The binding state after the staleness clock is applied.

    A BOUND observation older than the policy's max age ages out to UNOBSERVED
    rather than to STALE: the contract is not known to have mutated, it is
    merely no longer known to be current. Absence of an observation is
    UNOBSERVED for the same reason.
    """
    if observation is None:
        return Binding.UNOBSERVED
    if observation.binding is not Binding.BOUND:
        return observation.binding
    policy = policy or ObservationPolicy()
    if policy.max_age is None:
        return Binding.BOUND
    as_of = observation.observed_as_of
    if as_of is None:
        return Binding.UNOBSERVED
    return (
        Binding.BOUND
        if policy._now() - as_of <= policy.max_age
        else Binding.UNOBSERVED
    )


def declaration_is_usable(binding: Binding) -> bool:
    """Whether a declaration may inform the gate.

    Only BOUND is usable. STALE and UNOBSERVED are distinct states in the record
    but produce the same gate outcome, because a declaration that is either
    detached from its contract or unattested is not evidence about the action.
    """
    return binding is Binding.BOUND


def chain_binding(bindings: Iterable[Binding]) -> Binding:
    """The effective binding of a composed chain: as stale as its stalest link.

    This is the worst-case-across-chain rule that AISVS C9.2.10 applies to
    classes, applied to a second axis. An empty chain has nothing attested and
    fails closed to UNOBSERVED.
    """
    bindings = list(bindings)
    if not bindings:
        return Binding.UNOBSERVED
    return Binding(max(bindings))


@dataclass(frozen=True)
class Coverage:
    """Declared and verified coverage over a population, and the gap between.

    `declared` is the share of actions carrying a class the gate can read.
    `verified` is the share whose declaration is also still bound to its
    contract. `binding_gap` is the difference: the share that looks classified
    and is not attested. It is computable only where observations exist, which
    is why declaration-only runs report None.
    """

    population: int
    declared: float
    verified: float
    binding_gap: float


def coverage(
    actions: Sequence[Tuple[Optional[str], Optional[Observation]]],
    recognised,
    policy: Optional[ObservationPolicy] = None,
) -> Coverage:
    """Compute declared coverage, verified coverage and the binding gap.

    `actions` is a sequence of (declared_effect, observation) pairs.
    `recognised` is a predicate returning True where the declared effect is one
    the registry actually defines, so that an unrecognised string counts against
    declared coverage rather than for it.
    """
    n = len(actions)
    if n == 0:
        return Coverage(population=0, declared=0.0, verified=0.0, binding_gap=0.0)
    declared = sum(1 for eff, _ in actions if recognised(eff))
    verified = sum(
        1
        for eff, obs in actions
        if recognised(eff) and declaration_is_usable(effective_binding(obs, policy))
    )
    return Coverage(
        population=n,
        declared=declared / n,
        verified=verified / n,
        binding_gap=(declared - verified) / n,
    )
