from packages.permissions.catalog import ALL_PERMISSIONS, MODULES, SYSTEM_ROLES, validate_enable
from packages.permissions.resolve import AssignmentSnapshot, ScopeAttrs, can, module_enabled


def snap(role, scope_type, refs=()):
    return AssignmentSnapshot(role, frozenset(SYSTEM_ROLES[role]["permissions"]), scope_type, tuple(refs))


def test_catalog_consistency():
    for m in MODULES.values():
        for r in m.requires:
            assert r in MODULES, (m.key, r)
        for p in m.permissions:
            assert p.startswith(m.key + "."), p
    for role in SYSTEM_ROLES.values():
        assert set(role["permissions"]) <= ALL_PERMISSIONS


def test_teacher_scoped_to_own_halaqah():
    t = [snap("teacher", "halaqah", ["H1"])]
    in_h1 = ScopeAttrs(branch_id="B1", halaqah_ids=("H1",), student_id="S1")
    in_h2 = ScopeAttrs(branch_id="B1", halaqah_ids=("H2",), student_id="S2")
    assert can(t, "hifz.tasmee.record", in_h1).allowed
    assert not can(t, "hifz.tasmee.record", in_h2).allowed
    assert not can(t, "finance.fees.read", in_h1).allowed


def test_supervisor_scoped_to_branch():
    s = [snap("quran_supervisor", "branch", ["B1"])]
    assert can(s, "hifz.memory_map.read", ScopeAttrs(branch_id="B1", halaqah_ids=("H9",))).allowed
    assert not can(s, "hifz.memory_map.read", ScopeAttrs(branch_id="B2")).allowed
    assert not can(s, "finance.fees.read", ScopeAttrs(branch_id="B1")).allowed


def test_guardian_only_linked_children():
    g = [snap("guardian", "student_set", ["S1", "S2"])]
    assert can(g, "hifz.journey.read", ScopeAttrs(student_id="S2")).allowed
    assert not can(g, "hifz.journey.read", ScopeAttrs(student_id="S3")).allowed


def test_finance_never_sees_assessments():
    f = [snap("finance", "tenant")]
    assert can(f, "finance.invoicing.issue").allowed
    assert not can(f, "hifz.memory_map.read", ScopeAttrs(student_id="S1")).allowed


def test_no_role_can_grant_ijazah_by_default():
    for key in SYSTEM_ROLES:
        assert not can([snap(key, "tenant")], "hifz.ijazah.grant").allowed


def test_module_gating_and_dependencies():
    assert module_enabled("quran.core", set())            # core always on
    assert not module_enabled("hifz.asr", set())
    assert validate_enable("hifz.planner", {"hifz.policy"}) == ["hifz.retention"]
    assert validate_enable("hifz.planner", {"hifz.policy", "hifz.retention"}) == []
