"""Platform catalog: modules, their safety class, dependencies, and permission keys.

Safety classes: GREEN deterministic, YELLOW assistive (off by default), RED human-authority only
(RED entries exist only to document that no automation may perform them)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Module:
    key: str
    name_ar: str
    name_en: str
    safety: str = "GREEN"
    core: bool = False
    requires: tuple[str, ...] = ()
    default_enabled: bool = True
    permissions: tuple[str, ...] = field(default_factory=tuple)


MODULES: dict[str, Module] = {m.key: m for m in [
    Module("platform.identity", "الهوية والحسابات", "Identity & Accounts", core=True, permissions=("platform.identity.manage",)),
    Module("platform.tenancy", "المؤسسة والفروع", "Tenants & Branches", core=True, permissions=("platform.tenancy.manage", "platform.tenancy.read")),
    Module("platform.rbac", "الأدوار والصلاحيات", "Roles & Permissions", core=True, permissions=("platform.rbac.assign", "platform.rbac.manage_roles", "platform.rbac.read")),
    Module("platform.audit", "سجل التدقيق", "Audit Log", core=True, permissions=("platform.audit.read",)),
    Module("quran.core", "نواة القرآن", "Quran Core", core=True, permissions=("quran.core.read",)),
    Module("quran.reading", "الورد اليومي", "Daily Reading", requires=("quran.core",), permissions=("quran.reading.use",)),
    Module("quran.audio", "الاستماع للتلاوة", "Ayah Audio", requires=("quran.core",), permissions=("quran.audio.use",)),
    Module("people.students", "الطلاب", "Students", core=True, permissions=("people.students.read", "people.students.read_pii", "people.students.write", "people.students.transfer")),
    Module("people.guardians", "أولياء الأمور", "Guardians", permissions=("people.guardians.read", "people.guardians.write", "people.guardians.link")),
    Module("people.staff", "المعلمون والموظفون", "Teachers & Staff", permissions=("people.staff.read", "people.staff.write")),
    Module("ops.halaqat", "الحلقات", "Halaqat", permissions=("ops.halaqat.read", "ops.halaqat.write", "ops.halaqat.assign_staff", "ops.halaqat.enroll")),
    Module("ops.attendance", "الحضور", "Attendance", requires=("ops.halaqat",), permissions=("ops.attendance.read", "ops.attendance.mark")),
    Module("hifz.journey", "رحلة الطالب مع القرآن", "Quran Journey", core=True, requires=("quran.core",), permissions=("hifz.journey.read", "hifz.journey.write")),
    Module("hifz.memory_map", "خريطة الحفظ", "Memory Map", core=True, requires=("hifz.journey",), permissions=("hifz.memory_map.read", "hifz.memory_map.override")),
    Module("hifz.retention", "محرك الثبات", "Retention Engine", requires=("hifz.memory_map",), permissions=("hifz.retention.read",)),
    Module("hifz.policy", "منهجية الحفظ", "Learning Policy", requires=("hifz.journey",), permissions=("hifz.policy.read", "hifz.policy.write", "hifz.policy.assign")),
    Module("hifz.planner", "خطة الحفظ والمراجعة", "Adaptive Planner", requires=("hifz.retention", "hifz.policy"), permissions=("hifz.planner.read", "hifz.planner.approve", "hifz.planner.override")),
    Module("hifz.tasmee", "التسميع", "Tasmee'", requires=("hifz.memory_map",), permissions=("hifz.tasmee.read", "hifz.tasmee.record", "hifz.tasmee.edit_own", "hifz.tasmee.edit_any")),
    Module("hifz.assessments", "الاختبارات", "Assessments", requires=("hifz.tasmee",), permissions=("hifz.assessments.read", "hifz.assessments.define", "hifz.assessments.record")),
    Module("hifz.practice", "التدريب الذاتي", "Self-Practice", requires=("quran.core",), permissions=("hifz.practice.use",)),
    Module("hifz.asr", "كشف الأخطاء الصوتي", "Recitation Mismatch Detection", safety="YELLOW", default_enabled=False, requires=("hifz.practice", "hifz.review_queue"), permissions=("hifz.asr.use",)),
    Module("hifz.review_queue", "قائمة مراجعة المعلم", "Teacher Review Queue", requires=("hifz.tasmee",), permissions=("hifz.review_queue.read", "hifz.review_queue.resolve")),
    Module("hifz.ijazah", "توثيق الإجازة", "Ijazah Documentation", safety="RED", default_enabled=False, permissions=("hifz.ijazah.read", "hifz.ijazah.grant")),
    Module("parent.portal", "بوابة ولي الأمر", "Parent Portal", requires=("people.guardians",), permissions=("parent.portal.use",)),
    Module("intel.supervisor", "لوحة المشرف", "Supervisor Dashboard", requires=("hifz.retention",), permissions=("intel.supervisor.read",)),
    Module("intel.intervention", "الإنذار المبكر", "Intervention Engine", requires=("intel.supervisor",), permissions=("intel.intervention.read", "intel.intervention.act")),
    Module("intel.reports", "التقارير", "Reports", permissions=("intel.reports.read", "intel.reports.export")),
    Module("finance.fees", "الرسوم", "Fees", default_enabled=False, permissions=("finance.fees.read", "finance.fees.write")),
    Module("finance.invoicing", "الفواتير", "Invoicing", default_enabled=False, requires=("finance.fees",), permissions=("finance.invoicing.read", "finance.invoicing.issue")),
    Module("finance.payments", "المدفوعات", "Payments", default_enabled=False, requires=("finance.invoicing",), permissions=("finance.payments.read", "finance.payments.record", "finance.payments.refund")),
    Module("live.classroom", "الفصل المباشر", "Live Classroom", default_enabled=False, requires=("ops.halaqat",), permissions=("live.classroom.host", "live.classroom.join", "live.classroom.manage")),
    Module("ai.assist", "المساعد الذكي", "AI Assistant", safety="YELLOW", default_enabled=False, requires=("hifz.tasmee",), permissions=("ai.assist.use",)),
]}

ALL_PERMISSIONS: frozenset[str] = frozenset(p for m in MODULES.values() for p in m.permissions)


def module_of(permission: str) -> str:
    return permission.rsplit(".", 1)[0]


def validate_enable(module_key: str, enabled: set[str]) -> list[str]:
    """Returns missing dependencies for enabling module_key."""
    m = MODULES[module_key]
    return [r for r in m.requires if r not in enabled and not MODULES[r].core]


# ---- System roles ------------------------------------------------------------------------
SYSTEM_ROLES: dict[str, dict] = {
    "owner": {"name_ar": "مالك المؤسسة", "name_en": "Organization Owner",
              "permissions": sorted(p for p in ALL_PERMISSIONS if p != "hifz.ijazah.grant")},
    "center_admin": {"name_ar": "مدير المركز", "name_en": "Center Admin", "permissions": sorted(
        [p for p in ALL_PERMISSIONS if not p.startswith("finance.") and p not in ("hifz.ijazah.grant", "platform.rbac.manage_roles")]
        + ["finance.payments.read", "finance.payments.record"])},
    "branch_manager": {"name_ar": "مدير الفرع", "name_en": "Branch Manager", "permissions": sorted(
        p for p in ALL_PERMISSIONS if not p.startswith("finance.") and not p.startswith("platform.tenancy.manage") and p not in ("hifz.ijazah.grant", "platform.rbac.manage_roles"))},
    "quran_supervisor": {"name_ar": "مشرف القرآن", "name_en": "Quran Supervisor", "permissions": [
        "people.students.read", "people.staff.read", "ops.halaqat.read", "ops.halaqat.enroll", "ops.attendance.read",
        "hifz.journey.read", "hifz.journey.write", "hifz.memory_map.read", "hifz.memory_map.override", "hifz.retention.read",
        "hifz.policy.read", "hifz.policy.assign", "hifz.planner.read", "hifz.planner.approve", "hifz.planner.override",
        "hifz.tasmee.read", "hifz.tasmee.record", "hifz.tasmee.edit_any", "hifz.assessments.read", "hifz.assessments.define",
        "hifz.assessments.record", "hifz.review_queue.read", "intel.supervisor.read", "intel.intervention.read",
        "intel.intervention.act", "intel.reports.read", "intel.reports.export", "quran.core.read", "platform.rbac.read", "ai.assist.use", "hifz.asr.use"]},
    "teacher": {"name_ar": "معلم", "name_en": "Teacher", "permissions": [
        "people.students.read", "ops.halaqat.read", "ops.attendance.read", "ops.attendance.mark",
        "hifz.journey.read", "hifz.memory_map.read", "hifz.retention.read", "hifz.policy.read",
        "hifz.planner.read", "hifz.planner.approve", "hifz.planner.override", "hifz.tasmee.read", "hifz.tasmee.record",
        "hifz.tasmee.edit_own", "hifz.assessments.read", "hifz.assessments.record", "hifz.review_queue.read",
        "hifz.review_queue.resolve", "live.classroom.host", "quran.core.read", "quran.reading.use", "quran.audio.use", "ai.assist.use", "hifz.asr.use"]},
    "assistant_teacher": {"name_ar": "معلم مساعد", "name_en": "Assistant Teacher", "permissions": [
        "people.students.read", "ops.halaqat.read", "ops.attendance.read", "ops.attendance.mark",
        "hifz.journey.read", "hifz.memory_map.read", "hifz.planner.read", "hifz.tasmee.read", "quran.core.read", "quran.reading.use", "quran.audio.use"]},
    "student": {"name_ar": "طالب", "name_en": "Student", "permissions": [
        "hifz.journey.read", "hifz.memory_map.read", "hifz.planner.read", "hifz.practice.use", "hifz.asr.use", "hifz.tasmee.read", "live.classroom.join", "quran.core.read", "quran.reading.use", "quran.audio.use"]},
    "guardian": {"name_ar": "ولي أمر", "name_en": "Guardian", "permissions": [
        "people.students.read", "hifz.journey.read", "hifz.memory_map.read", "hifz.planner.read", "hifz.tasmee.read", "ops.attendance.read",
        "parent.portal.use", "quran.core.read", "quran.reading.use", "quran.audio.use"]},
    "solo_learner": {"name_ar": "متعلّم مستقل", "name_en": "Independent learner", "permissions": [
        "hifz.journey.read", "hifz.journey.write", "hifz.memory_map.read", "hifz.planner.read", "hifz.planner.approve", "hifz.planner.override",
        "hifz.practice.use", "hifz.asr.use", "hifz.tasmee.read", "hifz.tasmee.record", "hifz.assessments.read", "people.students.read", "quran.core.read", "quran.reading.use", "quran.audio.use",
        "platform.tenancy.read", "platform.rbac.read", "platform.rbac.assign", "platform.audit.read"]},
    "listener": {"name_ar": "مُسمِّع", "name_en": "Listener", "permissions": [
        "people.students.read", "hifz.journey.read", "hifz.memory_map.read", "hifz.planner.read", "hifz.tasmee.read", "hifz.tasmee.record",
        "hifz.assessments.read", "hifz.asr.use", "quran.core.read", "quran.reading.use", "quran.audio.use"]},
    "finance": {"name_ar": "موظف مالية", "name_en": "Finance", "permissions": [
        "people.students.read", "people.guardians.read", "finance.fees.read", "finance.fees.write",
        "finance.invoicing.read", "finance.invoicing.issue", "finance.payments.read", "finance.payments.record",
        "finance.payments.refund", "intel.reports.read"]},
    "support": {"name_ar": "دعم", "name_en": "Support", "permissions": [
        "people.students.read", "people.guardians.read", "people.staff.read", "ops.halaqat.read", "platform.audit.read", "platform.rbac.read"]},
}
