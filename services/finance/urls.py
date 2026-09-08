from rest_framework.routers import DefaultRouter

from .views import FeePlanViewSet, InvoiceViewSet, PaymentViewSet, StudentFeePlanViewSet

router = DefaultRouter(trailing_slash=False)
router.register("fee-plans", FeePlanViewSet, basename="fee-plan")
router.register("student-plans", StudentFeePlanViewSet, basename="student-plan")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls
