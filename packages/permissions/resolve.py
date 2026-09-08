"""Pure resolution of (assignments, permission, object) → decision."""
from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import MODULES, module_of


@dataclass(frozen=True)
class AssignmentSnapshot:
    role_key: str
    permissions: frozenset[str]
    scope_type: str            # tenant | branch | halaqah | course | student_set | self
    scope_refs: tuple = ()     # ids as strings


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""
    via: AssignmentSnapshot | None = None
    scope_type: str = ""


@dataclass
class ScopeAttrs:
    """What an object exposes for scope matching. Missing attrs mean 'not applicable'."""
    branch_id: str | None = None
    halaqah_ids: tuple = field(default_factory=tuple)
    student_id: str | None = None
    person_id: str | None = None


def module_enabled(module_key: str, enabled: set[str]) -> bool:
    m = MODULES.get(module_key)
    if m is None:
        return False
    return m.core or module_key in enabled


def scope_covers(snap: AssignmentSnapshot, attrs: ScopeAttrs | None, subject_person_id: str | None = None) -> bool:
    if snap.scope_type == "tenant":
        return True
    if attrs is None:
        return False
    refs = set(map(str, snap.scope_refs))
    if snap.scope_type == "branch":
        return attrs.branch_id is not None and str(attrs.branch_id) in refs
    if snap.scope_type == "halaqah":
        return any(str(h) in refs for h in attrs.halaqah_ids)
    if snap.scope_type == "student_set":
        return attrs.student_id is not None and str(attrs.student_id) in refs
    if snap.scope_type == "self":
        return attrs.person_id is not None and subject_person_id is not None and str(attrs.person_id) == str(subject_person_id)
    return False


def can(assignments: list[AssignmentSnapshot], permission: str, obj=None, subject_person_id: str | None = None) -> Decision:
    if module_of(permission) not in MODULES:
        return Decision(False, f"unknown permission {permission}")
    attrs = None
    if obj is not None:
        attrs = obj if isinstance(obj, ScopeAttrs) else getattr(obj, "scope_attrs", lambda: None)()
    for snap in assignments:
        if permission not in snap.permissions:
            continue
        if obj is None:
            return Decision(True, "", snap, snap.scope_type)
        if scope_covers(snap, attrs, subject_person_id):
            return Decision(True, "", snap, snap.scope_type)
    return Decision(False, "permission_denied")
