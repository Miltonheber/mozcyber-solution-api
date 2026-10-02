from django.urls import path

from .views import ActionLogListView

urlpatterns = [path("", ActionLogListView.as_view(), name="log-list")]
