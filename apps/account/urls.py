from django.urls import path
from apps.account.views.login_view import LoginView
from apps.account.views.request_mail_verify_view import RequestMailVerifyView
from apps.account.views.register_view import RegisterView
from apps.account.views.change_password_view import ChangePasswordView

urlpatterns = [
    path('mailverify/', RequestMailVerifyView.as_view(), name='mail_request'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('changepassword/', ChangePasswordView.as_view(), name='change_password')
]