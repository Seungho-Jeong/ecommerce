from django.urls import path

from .views import (
    AccountConfirmationView,
    AccountRegisterView,
    TokenCreateView,
)

urlpatterns = [
    path("signup/", AccountRegisterView.as_view(), name="signup"),
    path("signin/", TokenCreateView.as_view(), name="signin"),
    path("confirm/", AccountConfirmationView.as_view(), name="confirm"),
]
