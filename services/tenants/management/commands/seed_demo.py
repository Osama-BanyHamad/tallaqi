"""Seed a realistic demo tenant (Arabic names, two branches, four halaqat, ~36 students with simulated history)."""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from packages.permissions.catalog import MODULES
from packages.quran_core import get_core
from services.common import context
from services.hifz import services as hifz
from services.hifz.models import QuranJourney
from services.identity.models import Account
from services.people.models import AttendanceRecord, Enrollment, Guardian, GuardianLink, Halaqah, HalaqahStaff, Person, Staff, Student
from services.rbac.services import assign, ensure_system_roles
from services.tenants.models import Branch, Membership, Tenant, TenantModule

PASSWORD = "Talaqqi@2026"
MALE = ["أحمد", "محمد", "يوسف", "عبدالله", "عمر", "خالد", "حمزة", "زيد", "إبراهيم", "بلال", "أنس", "سعد", "معاذ", "طارق", "ياسر", "أسامة", "عبدالرحمن", "مصعب"]
FEMALE = ["مريم", "فاطمة", "عائشة", "خديجة", "زينب", "سارة", "هاجر", "أسماء", "رقية", "نور", "سلمى", "ليان", "جنى", "ريم", "آلاء", "حنين", "تسنيم", "بيان"]
FAMILY = ["الخطيب", "العمري", "الزعبي", "الحوراني", "النابلسي", "الشريف", "البدوي", "الرفاعي", "أبو زيد", "الطراونة", "العبادي", "الحمود", "المصري", "القيسي", "السعدي", "الحديدي", "الكردي", "الشامي"]


class Command(BaseCommand):
    help = "Seed the demo tenant 'demo' with realistic Arabic data and simulated Hifz history."

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="demo")
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **opts):
        random.seed(7)
        slug = opts["slug"]
        with context.platform_admin("seed"):
            if opts["reset"]:
                Tenant.objects.filter(slug=slug).delete()
                Account.objects.filter(email__endswith=f"@{slug}.talaqqi").delete()
            if Tenant.objects.filter(slug=slug).exists():
                self.stdout.write("demo tenant exists (use --reset)")
                return
            t = Tenant.objects.create(slug=slug, name="مركز النور لتحفيظ القرآن الكريم", name_en="Al-Noor Quran Center", kind="center",
                                      locales=["ar", "en"], timezone="Asia/Amman", currency="JOD",
                                      branding={"accent": "#1E6B73", "app_name": "مركز النور"})
            for m in MODULES.values():
                if not m.core and m.default_enabled:
                    TenantModule.objects.create(tenant=t, module_key=m.key, enabled=True)
        with context.tenant(t.id):
            self.seed_tenant(t, slug)
        self.stdout.write(self.style.SUCCESS(f"seeded tenant '{slug}'. Login: owner@{slug}.talaqqi / {PASSWORD} (also supervisor@, teacher1@..teacher4@, parent1@, finance@)"))

    @transaction.atomic
    def seed_tenant(self, t: Tenant, slug: str):
        core = get_core()
        roles = ensure_system_roles(t)
        b_main = Branch.objects.create(tenant=t, name="الفرع الرئيسي — إربد", name_en="Main Branch — Irbid", code="IRB")
        b_north = Branch.objects.create(tenant=t, name="فرع الحصن", name_en="Al-Husn Branch", code="HSN", gender_policy="female")

        def person(first, family, gender, dob=None, phone=""):
            return Person.objects.create(tenant=t, first_name=first, last_name=family, display_name_ar=f"{first} {family}",
                                         gender=gender, date_of_birth=dob, phone=phone)

        def account(local, role_key, scope_type="tenant", refs=(), person_obj=None, full_name=""):
            a = Account.objects.create_user(email=f"{local}@{slug}.talaqqi", password=PASSWORD, full_name=full_name or local, locale="ar")
            m = Membership.objects.create(account=a, tenant=t, person=person_obj)
            assign(m, roles[role_key], scope_type, list(refs))
            return a

        owner_p = person("د. حسان", "الخطيب", "male")
        account("owner", "owner", person_obj=owner_p, full_name="د. حسان الخطيب")
        sup_p = person("أبو خالد", "العمري", "male")
        Staff.objects.create(tenant=t, person=sup_p, branch=b_main, staff_type="supervisor")
        account("supervisor", "quran_supervisor", "branch", [b_main.id, b_north.id], sup_p, "أبو خالد العمري")
        fin_p = person("بلال", "الرفاعي", "male")
        Staff.objects.create(tenant=t, person=fin_p, branch=b_main, staff_type="finance")
        account("finance", "finance", person_obj=fin_p, full_name="بلال الرفاعي")

        teachers = []
        specs = [("الشيخ أحمد", "الزعبي", "male", b_main, "حلقة الفجر", "in_person", "sabaq_sabqi_manzil", "السبت–الخميس 6:00–7:30"),
                 ("الشيخ عمر", "الحوراني", "male", b_main, "حلقة المتقدمين", "hybrid", "sabaq_sabqi_manzil", "السبت–الأربعاء 16:00–17:30"),
                 ("الأستاذة مريم", "النابلسي", "female", b_north, "حلقة الصغار", "in_person", "children_ayah", "الأحد–الخميس 15:00–16:00"),
                 ("الأستاذة سلمى", "الشريف", "female", b_north, "حلقة الحافظات (مراجعة)", "online", "post_hifz_40", "السبت والثلاثاء 20:00–21:00")]
        halaqat = []
        for i, (first, fam, g, branch, hname, kind, pol, sched) in enumerate(specs, start=1):
            p = person(first, fam, g)
            st = Staff.objects.create(tenant=t, person=p, branch=branch, staff_type="teacher", riwayat=["hafs_asim"],
                                      qualifications=[{"title": "إجازة برواية حفص عن عاصم", "year": 2015 + i}])
            h = Halaqah.objects.create(tenant=t, branch=branch, name=hname, kind=kind, policy_key=pol, capacity=12,
                                       gender_policy="female" if g == "female" else "male", schedule_summary=sched)
            HalaqahStaff.objects.create(tenant=t, halaqah=h, staff=st)
            account(f"teacher{i}", "teacher", "halaqah", [h.id], p, f"{first} {fam}")
            teachers.append(st)
            halaqat.append(h)

        now = datetime.now(timezone.utc)
        code_no = 1000
        parent_accounts_left = 2
        for h_i, h in enumerate(halaqat):
            branch = h.branch
            names = FEMALE if h.gender_policy == "female" else MALE
            n_students = 9
            for k in range(n_students):
                first = names[(h_i * 5 + k) % len(names)]
                fam = FAMILY[(h_i * 7 + k * 3) % len(FAMILY)]
                age = random.randint(8, 16) if h.policy_key != "post_hifz_40" else random.randint(18, 30)
                code_no += 1
                sp = person(first, fam, "female" if names is FEMALE else "male", date(2026 - age, random.randint(1, 12), random.randint(1, 28)))
                student = Student.objects.create(tenant=t, person=sp, branch=branch, student_code=f"S{code_no}", is_minor=age < 18,
                                                 level=random.choice(["مبتدئ", "متوسط", "متقدم"]))
                Enrollment.objects.create(tenant=t, student=student, halaqah=h, start_date=date(2025, 9, 1))
                gp = person("أم " + first if names is FEMALE else "أبو " + first, fam, "female" if names is FEMALE else "male", phone=f"07{random.randint(70000000, 99999999)}")
                guardian = Guardian.objects.create(tenant=t, person=gp)
                GuardianLink.objects.create(tenant=t, guardian=guardian, student=student, relationship="parent")
                if parent_accounts_left and h_i == 0:
                    account(f"parent{3 - parent_accounts_left}", "guardian", "student_set", [student.id], gp, gp.display_name_ar)
                    parent_accounts_left -= 1
                journey = QuranJourney.objects.create(tenant=t, student=student, started_at=date(2025, 9, 1), policy_key=h.policy_key,
                                                      current_ayah_index=core.surah(114).start_index)
                self.simulate(core, journey, teachers[h_i], h, now, profile=h.policy_key, seed=k)
                # attendance last 14 days
                for d in range(14):
                    day = (now - timedelta(days=d)).date()
                    if day.weekday() == 4:
                        continue
                    status = random.choices(["present", "present", "present", "present", "absent", "late"], k=1)[0]
                    if k == 2 and d < 6:
                        status = "absent"
                    AttendanceRecord.objects.create(tenant=t, halaqah=h, student=student, on_date=day, status=status)
        for j in QuranJourney.objects.all():
            hifz.refresh_aggregates(j)
            hifz.recompute_milestones(j, now)
            hifz.run_decay(j, now)
            hifz.generate_plan(j, now.date(), now)

    def simulate(self, core, journey, teacher, halaqah, now, *, profile: str, seed: int):
        """Replay months of Tasmee' history so the retention model produces a realistic memory map."""
        rnd = random.Random(seed * 31 + len(journey.student.student_code))
        if profile == "post_hifz_40":
            # Completed Hifz: bulk-seed the whole map directly (fast), then replay a few real revision sessions.
            from services.hifz.models import StudentAyahState
            rows = []
            for page in range(1, 605):
                p = core.page(page)
                mem_at = now - timedelta(days=720 - page)
                base = 0.92 if page % 9 else 0.55
                if rnd.random() < 0.06:
                    base = 0.3
                last = now - timedelta(days=rnd.randint(1, 50))
                for i in range(p.first_ayah_index, p.last_ayah_index + 1):
                    score = min(1.0, max(0.1, base + rnd.uniform(-0.08, 0.08)))
                    stab = 90 if base > 0.9 else 12 if base > 0.5 else 3
                    state = "mastered" if score >= 0.95 and stab >= 90 else "strong" if score >= 0.85 else "needs_revision" if score >= 0.6 else "weak" if score >= 0.35 else "critical"
                    rows.append(StudentAyahState(tenant_id=journey.tenant_id, journey=journey, ayah_index=i, state=state, retention_score=score,
                                                 stability_days=stab, memorized_at=mem_at, last_recited_at=last, last_passed_at=last,
                                                 success_count=rnd.randint(4, 12), fail_count=0 if base > 0.9 else rnd.randint(1, 3),
                                                 consecutive_successes=6 if base > 0.9 else 1, next_due_at=last + timedelta(days=stab)))
            StudentAyahState.objects.bulk_create(rows, batch_size=2000)
            journey.memorized_pages_order = list(range(1, 605))
            for k in range(12):
                page = core.page(rnd.randint(1, 604))
                fail = rnd.random() < 0.2
                mistakes = [{"ayah_index": page.first_ayah_index, "mistake_type": "forgotten_word"}] if fail else []
                hifz.record_recitation(journey, teacher=teacher, halaqah=halaqah, purpose="far", from_ayah_index=page.first_ayah_index,
                                       to_ayah_index=page.last_ayah_index, outcome="repeat" if fail else "pass", mistakes=mistakes,
                                       at=now - timedelta(days=12 - k), refresh=False)
            journey.status = "retaining"
            journey.current_ayah_index = None
            journey.save()
            return
        # Memorizing from Juz 30 backwards: pick how far this student got.
        if profile == "children_ayah":
            total_days = rnd.randint(45, 110)
            pace_ayat = 3
        else:
            total_days = rnd.randint(70, 180)
            pace_ayat = rnd.choice([6, 8, 10, 14])
        day = now - timedelta(days=total_days)
        pos = journey.current_ayah_index
        weak_student = seed in (2, 5)
        while day < now - timedelta(days=1) and pos:
            if day.weekday() == 4:
                day += timedelta(days=1)
                continue
            a = core.ayah_by_index(pos)
            s = core.surah(a.surah)
            end = min(pos + pace_ayat - 1, s.start_index + s.ayah_count - 1)
            fail = rnd.random() < (0.28 if weak_student else 0.1)
            mistakes = []
            if fail or rnd.random() < 0.3:
                for _ in range(rnd.randint(1, 3)):
                    mistakes.append({"ayah_index": rnd.randint(pos, end), "mistake_type": rnd.choice(["forgotten_word", "incorrect_word", "harakah", "tajweed", "mutashabihat_confusion"]),
                                     "severity": "major" if fail else "minor"})
            hifz.record_recitation(journey, teacher=teacher, halaqah=halaqah, purpose="new", from_ayah_index=pos, to_ayah_index=end,
                                   outcome="repeat" if fail else "pass", mistakes=mistakes, at=day + timedelta(hours=6), refresh=False)
            journey.refresh_from_db()
            if not fail:
                pos = journey.current_ayah_index
            # near revision of previous pages
            order = journey.memorized_pages_order or []
            if order and rnd.random() < 0.8:
                page = core.page(rnd.choice(order[-6:]))
                rfail = rnd.random() < (0.3 if weak_student else 0.12)
                rm = [{"ayah_index": rnd.randint(page.first_ayah_index, page.last_ayah_index), "mistake_type": "forgotten_word"}] if rfail else []
                hifz.record_recitation(journey, teacher=teacher, halaqah=halaqah, purpose="near", from_ayah_index=page.first_ayah_index,
                                       to_ayah_index=page.last_ayah_index, outcome="repeat" if rfail else "pass", mistakes=rm, at=day + timedelta(hours=7), refresh=False)
            if len(order) > 8 and rnd.random() < 0.5:
                page = core.page(rnd.choice(order[:-6]))
                ffail = rnd.random() < (0.35 if weak_student else 0.15)
                fm = [{"ayah_index": rnd.randint(page.first_ayah_index, page.last_ayah_index), "mistake_type": rnd.choice(["forgotten_word", "skipped_ayah"])}] if ffail else []
                hifz.record_recitation(journey, teacher=teacher, halaqah=halaqah, purpose="far", from_ayah_index=page.first_ayah_index,
                                       to_ayah_index=page.last_ayah_index, outcome="repeat" if ffail else "pass", mistakes=fm, at=day + timedelta(hours=7, minutes=30), refresh=False)
            day += timedelta(days=1)
            journey.refresh_from_db()
            pos = journey.current_ayah_index
        if weak_student:
            journey.level = "يحتاج متابعة"
            journey.save()
