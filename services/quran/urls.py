from django.urls import path

from .views import RecitersView, AyahView, ManifestView, PageView, RangeView, SurahListView, UnitsView

urlpatterns = [
    path("manifest", ManifestView.as_view()),
    path("reciters", RecitersView.as_view()),
    path("<slug:riwayah>/surahs", SurahListView.as_view()),
    path("<slug:riwayah>/ayah/<str:key>", AyahView.as_view()),
    path("<slug:riwayah>/range", RangeView.as_view()),
    path("<slug:riwayah>/page/<int:page>", PageView.as_view()),
    path("<slug:riwayah>/units/<slug:unit_type>", UnitsView.as_view()),
]
