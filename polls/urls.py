from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("status/<str:reference>/", views.status, name="status"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/approve/<int:pk>/", views.approve, name="approve"),
    path("dashboard/reject/<int:pk>/", views.reject, name="reject"),
]
