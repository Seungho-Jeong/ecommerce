from django.urls import path

from .views import AccountConfirmationView, AccountRegisterView

urlpatterns = [
    path("signup/", AccountRegisterView.as_view(), name="signup"),
    path("confirm/", AccountConfirmationView.as_view(), name="confirm"),
]
