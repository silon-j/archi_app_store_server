from django.urls import path
from .views.acount_view import LoginView, RegisterView, ChangePasswordView
from .views.verify_code_view import RegisterVerifyCode, ChangePasswordVerifyCode


urlpatterns = [
    path('registerverify', RegisterVerifyCode.as_view(), name='register_verify'),
    path('passwordverify', ChangePasswordVerifyCode.as_view(), name='password_verify'),
    path('login', LoginView.as_view(), name='login'),
    path('register', RegisterView.as_view(), name='register'),
    path('changepassword', ChangePasswordView.as_view(), name='change_password')
]