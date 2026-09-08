"""Idempotently create student logins for the demo tenant (student1@, student2@) linked to real students."""
from django.core.management.base import BaseCommand

from services.common import context
from services.identity.models import Account
from services.people.models import Student
from services.rbac.models import Role
from services.rbac.services import assign
from services.tenants.models import Membership, Tenant

PASSWORD = "Talaqqi@2026"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", default="demo")
        parser.add_argument("--count", type=int, default=2)

    def handle(self, *args, **opts):
        with context.platform_admin("demo-students"):
            t = Tenant.objects.get(slug=opts["slug"])
        with context.tenant(t.id):
            role = Role.objects.get(key="student")
            students = list(Student.objects.filter(status="active").select_related("person").order_by("student_code")[: opts["count"]])
            for i, st in enumerate(students, start=1):
                email = f"student{i}@{opts['slug']}.talaqqi"
                with context.platform_admin("demo-students"):
                    acc = Account.objects.filter(email=email).first() or Account.objects.create_user(email=email, password=PASSWORD, full_name=st.person.display_name_ar, locale="ar")
                    m, created = Membership.objects.get_or_create(account=acc, tenant=t, defaults={"person": st.person})
                if created or not m.role_assignments.exists():
                    assign(m, role, "self", [])
                self.stdout.write(f"{email} -> {st.person.display_name_ar} ({st.student_code})")
        self.stdout.write(self.style.SUCCESS(f"student logins ready (password {PASSWORD})"))
