from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.utils.dateparse import parse_date
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.audit.models import AuditLog
from services.common.exceptions import DomainError
from services.common.permissions import CapabilityPermission, scoped
from services.people.models import Student

from . import services
from .models import FeePlan, Invoice, InvoiceLine, Payment, StudentFeePlan


def _students(request):
    return scoped(request, Student.objects.select_related("person", "branch"), branch_field="branch_id", student_field="id",
                  person_field="person_id")


def _invoices(request):
    qs = Invoice.objects.select_related("student__person", "student__branch", "source_plan__plan")
    return scoped(request, qs, branch_field="student__branch_id", student_field="student_id", person_field="student__person_id")


# ---- fee plans -----------------------------------------------------------------------------
class FeePlanSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True, default="")
    active_students = serializers.SerializerMethodField()

    class Meta:
        model = FeePlan
        fields = ["id", "name", "cadence", "amount", "currency", "description", "is_active", "sibling_discount_pct", "branch", "branch_name",
                  "active_students", "created_at"]
        read_only_fields = ["id", "currency", "created_at"]

    def get_active_students(self, obj):
        n = getattr(obj, "_active_students", None)
        return n if n is not None else obj.assignments.filter(status="active").count()


class FeePlanViewSet(viewsets.ModelViewSet):
    serializer_class = FeePlanSerializer
    permission_classes = [CapabilityPermission]
    required_module = "finance.fees"
    required_permission = {"list": "finance.fees.read", "retrieve": "finance.fees.read", "create": "finance.fees.write",
                           "update": "finance.fees.write", "partial_update": "finance.fees.write", "destroy": "finance.fees.write"}
    filterset_fields = ["cadence", "is_active", "branch"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "amount", "created_at"]

    def get_queryset(self):
        from django.db.models import Count, Q
        return FeePlan.objects.select_related("branch").annotate(_active_students=Count("assignments", filter=Q(assignments__status="active"))).order_by("name")

    def perform_create(self, serializer):
        obj = serializer.save(currency=self.request.tenant.currency)
        AuditLog.record(self.request, "fee_plan.created", "FeePlan", obj.id, after=FeePlanSerializer(obj).data)

    def perform_update(self, serializer):
        before = FeePlanSerializer(serializer.instance).data
        obj = serializer.save()
        AuditLog.record(self.request, "fee_plan.updated", "FeePlan", obj.id, before=before, after=FeePlanSerializer(obj).data)

    def perform_destroy(self, instance):
        if instance.assignments.exists():
            raise DomainError("Plan has student assignments; deactivate it instead of deleting.")
        AuditLog.record(self.request, "fee_plan.deleted", "FeePlan", instance.id, before=FeePlanSerializer(instance).data)
        instance.delete()


# ---- student plan assignments ---------------------------------------------------------------
class StudentFeePlanSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.person.display_name_ar", read_only=True)
    student_code = serializers.CharField(source="student.student_code", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_amount = serializers.DecimalField(source="plan.amount", max_digits=12, decimal_places=3, read_only=True)
    plan_cadence = serializers.CharField(source="plan.cadence", read_only=True)
    currency = serializers.CharField(source="plan.currency", read_only=True)

    class Meta:
        model = StudentFeePlan
        fields = ["id", "student", "student_name", "student_code", "plan", "plan_name", "plan_amount", "plan_cadence", "currency",
                  "discount_pct", "scholarship_pct", "scholarship_note", "start_date", "end_date", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_student(self, student):
        request = self.context["request"]
        if not _students(request).filter(pk=student.pk).exists():
            raise serializers.ValidationError("Student not found.")
        return student

    def validate(self, attrs):
        start, end = attrs.get("start_date", getattr(self.instance, "start_date", None)), attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date cannot be before start_date."})
        return attrs


class StudentFeePlanViewSet(viewsets.ModelViewSet):
    serializer_class = StudentFeePlanSerializer
    permission_classes = [CapabilityPermission]
    required_module = "finance.fees"
    required_permission = {"list": "finance.fees.read", "retrieve": "finance.fees.read", "create": "finance.fees.write",
                           "update": "finance.fees.write", "partial_update": "finance.fees.write", "destroy": "finance.fees.write",
                           "invoice": "finance.invoicing.issue"}
    filterset_fields = ["student", "plan", "status"]
    search_fields = ["student__person__display_name_ar", "student__student_code", "plan__name"]
    ordering_fields = ["start_date", "created_at"]

    def get_queryset(self):
        qs = StudentFeePlan.objects.select_related("student__person", "student__branch", "plan")
        return scoped(self.request, qs, branch_field="student__branch_id", student_field="student_id", person_field="student__person_id").order_by("-start_date")

    def perform_create(self, serializer):
        obj = serializer.save()
        AuditLog.record(self.request, "student_plan.assigned", "StudentFeePlan", obj.id, after=StudentFeePlanSerializer(obj).data)

    def perform_update(self, serializer):
        before = StudentFeePlanSerializer(serializer.instance).data
        obj = serializer.save()
        AuditLog.record(self.request, "student_plan.updated", "StudentFeePlan", obj.id, before=before, after=StudentFeePlanSerializer(obj).data)

    def perform_destroy(self, instance):
        if instance.invoices.exists():
            raise DomainError("Assignment has invoices; end it instead of deleting.")
        AuditLog.record(self.request, "student_plan.deleted", "StudentFeePlan", instance.id, before=StudentFeePlanSerializer(instance).data)
        instance.delete()

    @action(detail=True, methods=["post"])
    def invoice(self, request, pk=None):
        """Generate one invoice for this assignment: {period_label, issued_on?, due_on?}."""
        sp = self.get_object()
        from services.common.permissions import check
        check(request, "finance.invoicing.issue", "finance.invoicing")
        period = (request.data.get("period_label") or "").strip()
        if not period:
            raise DomainError("period_label is required.")
        issued_on = parse_date(request.data.get("issued_on") or "") or date.today()
        due_on = parse_date(request.data.get("due_on") or "") or None
        inv = services.generate_invoice(sp, period, issued_on=issued_on, due_on=due_on, request=request)
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_201_CREATED)


# ---- invoices ------------------------------------------------------------------------------
class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ["id", "kind", "description", "quantity", "unit_amount", "amount", "order"]


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)
    student = serializers.UUIDField(source="invoice.student_id", read_only=True)
    student_name = serializers.CharField(source="invoice.student.person.display_name_ar", read_only=True)
    student_code = serializers.CharField(source="invoice.student.student_code", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True, default="")

    class Meta:
        model = Payment
        fields = ["id", "invoice", "invoice_number", "student", "student_name", "student_code", "amount", "currency", "method", "reference",
                  "received_on", "note", "receipt_number", "recorded_by", "recorded_by_name", "status", "refunded_at", "refund_reason", "created_at"]
        read_only_fields = fields


class InvoiceListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.person.display_name_ar", read_only=True)
    student_code = serializers.CharField(source="student.student_code", read_only=True)
    branch_name = serializers.CharField(source="student.branch.name", read_only=True)
    plan_name = serializers.CharField(source="source_plan.plan.name", read_only=True, default="")
    outstanding = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "number", "student", "student_name", "student_code", "branch_name", "payer_name", "issued_on", "due_on", "currency",
                  "subtotal", "discount_total", "total", "paid_total", "outstanding", "status", "period_label", "plan_name", "source_plan", "created_at"]
        read_only_fields = fields


class InvoiceSerializer(InvoiceListSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default="")

    class Meta(InvoiceListSerializer.Meta):
        fields = InvoiceListSerializer.Meta.fields + ["notes", "created_by", "created_by_name", "lines", "payments"]
        read_only_fields = fields


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [CapabilityPermission]
    required_module = "finance.invoicing"
    required_permission = {"list": "finance.invoicing.read", "retrieve": "finance.invoicing.read", "summary": "finance.invoicing.read",
                           "generate": "finance.invoicing.issue", "void": "finance.invoicing.issue"}
    filterset_fields = ["status", "student", "period_label", "source_plan"]
    search_fields = ["number", "payer_name", "student__person__display_name_ar", "student__person__display_name_en", "student__student_code"]
    ordering_fields = ["issued_on", "due_on", "total", "paid_total", "number", "status"]

    def get_serializer_class(self):
        return InvoiceListSerializer if self.action == "list" else InvoiceSerializer

    def get_queryset(self):
        qs = _invoices(self.request)
        if self.action == "retrieve":
            qs = qs.prefetch_related("lines", "payments__invoice__student__person", "payments__recorded_by")
        return qs.order_by("-issued_on", "-number")

    def list(self, request, *args, **kwargs):
        services.mark_overdue(date.today(), request=request)   # lazy status refresh; cheap (indexed on status)
        qs = self.filter_queryset(self.get_queryset())
        if request.query_params.get("open") in ("1", "true"):
            qs = qs.filter(status__in=Invoice.OPEN_STATUSES)
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(InvoiceListSerializer(page, many=True).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        services.mark_overdue(date.today(), request=request)
        return Response(services.summary(_invoices(request)))

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Bulk monthly run: {period_label: 'YYYY-MM'} → creates missing invoices for every active monthly assignment."""
        period = (request.data.get("period_label") or "").strip()
        if not period:
            raise DomainError("period_label is required.")
        services.period_bounds(period)
        created = services.generate_monthly_invoices(period, request=request)
        AuditLog.record(request, "invoice.bulk_generated", "Invoice", "", after={"period": period, "count": len(created)})
        return Response({"period_label": period, "created": len(created), "invoices": InvoiceListSerializer(created, many=True).data},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        inv = services.void_invoice(self.get_object(), reason=request.data.get("reason", ""), request=request)
        return Response(InvoiceSerializer(Invoice.objects.prefetch_related("lines", "payments").get(pk=inv.pk)).data)


# ---- payments ------------------------------------------------------------------------------
class PaymentIn(serializers.Serializer):
    invoice = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    method = serializers.ChoiceField(choices=[k for k, _ in Payment.METHOD], default="cash")
    reference = serializers.CharField(required=False, allow_blank=True, default="", max_length=120)
    received_on = serializers.DateField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class PaymentViewSet(viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [CapabilityPermission]
    required_module = "finance.payments"
    required_permission = {"list": "finance.payments.read", "retrieve": "finance.payments.read", "create": "finance.payments.record",
                           "refund": "finance.payments.refund"}
    filterset_fields = ["invoice", "method", "status", "invoice__student"]
    search_fields = ["receipt_number", "reference", "invoice__number", "invoice__student__person__display_name_ar"]
    ordering_fields = ["received_on", "amount", "created_at"]

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice__student__person", "recorded_by")
        return scoped(self.request, qs, branch_field="invoice__student__branch_id", student_field="invoice__student_id",
                      person_field="invoice__student__person_id").order_by("-received_on", "-created_at")

    def list(self, request):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        return self.get_paginated_response(PaymentSerializer(page, many=True).data)

    def retrieve(self, request, pk=None):
        return Response(PaymentSerializer(self.get_object()).data)

    def create(self, request):
        s = PaymentIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        inv = _invoices(request).filter(pk=d["invoice"]).first()
        if inv is None:
            return Response({"code": "not_found", "detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        p = services.record_payment(inv, d["amount"], method=d["method"], reference=d["reference"], received_on=d.get("received_on"),
                                    note=d["note"], request=request)
        return Response(PaymentSerializer(p).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        p = services.refund_payment(self.get_object(), reason=request.data.get("reason", ""), request=request)
        return Response(PaymentSerializer(p).data)
