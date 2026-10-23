"""Map MCP tool hints to the reference model's declared-effect vocabulary.

The mapping below is OUR interpretation, not the deposit's. The deposit records
what servers declared and deliberately imputes nothing: absent means undeclared
rather than false. A gate has no such luxury, it must resolve absence before it
can decide, so this module offers both resolutions and reports them separately.

MCP spec defaults, verified at revision 2026-07-28:
    readOnlyHint     default false
    destructiveHint  default true   (meaningful only when readOnlyHint is false)
    idempotentHint   default false  (meaningful only when readOnlyHint is false)
    openWorldHint    default true
"""
from typing import Optional, Dict

SPEC_DEFAULTS = {
    "readOnlyHint": "false",
    "destructiveHint": "true",
    "idempotentHint": "false",
    "openWorldHint": "true",
}


def _effect(read_only: str, destructive: str, open_world: str) -> str:
    if read_only == "true":
        return "read_only"
    if destructive == "true":
        return "non_recoverable"
    if open_world == "true":
        return "externally_recoverable"
    return "recoverable_local"


def declared_effect(row: Dict[str, str], resolve_absent: bool) -> Optional[str]:
    """Return the declared effect for one tool row, or None if undeclared.

    resolve_absent False is the strict reading: any hint on the decision path
    that is absent leaves the tool undeclared, and the gate fails it closed.

    resolve_absent True imputes the MCP spec default for an absent hint, which
    is what a deployed gate must do, then maps as normal.
    """
    def h(name: str) -> Optional[str]:
        v = row.get(name, "absent")
        if v != "absent":
            return v
        return SPEC_DEFAULTS[name] if resolve_absent else None

    ro = h("readOnlyHint")
    if ro is None:
        return None
    if ro == "true":
        return "read_only"

    de = h("destructiveHint")
    if de is None:
        return None
    if de == "true":
        return "non_recoverable"

    ow = h("openWorldHint")
    if ow is None:
        return None
    return _effect(ro, de, ow)
