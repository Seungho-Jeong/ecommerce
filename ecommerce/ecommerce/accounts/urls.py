from django.urls import path

from .views import (
    AccountConfirmationView,
    AccountRegisterView,
    TokenCreateView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("signup/", AccountRegisterView.as_view(), name="signup"),
    path("signin/", TokenCreateView.as_view(), name="signin"),
    path("confirm/", AccountConfirmationView.as_view(), name="confirm"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
