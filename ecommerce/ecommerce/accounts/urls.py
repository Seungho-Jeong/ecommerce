from django.urls import path

from .views import AccountRegisterView

urlpatterns = [
    path("signup/", AccountRegisterView.as_view(), name="signup"),
]
