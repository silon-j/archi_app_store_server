from django.urls import path
from .views.account_view import LoginView, RegisterView, ChangePasswordView, UserInfoView
from .views.verify_code_view import RegisterVerifyCode, ChangePasswordVerifyCode
from .views.admin_get_accounts import AdminGetAllAccounts
from .views.admin_modify_account import AdminChangeAccountPassword, AdminModifyAccount
from .views.admin_suspend_account import AdminActivateAccount, AdminSuspendAccount, AdminDeleteAccount


urlpatterns = [
    path('/registerverify', RegisterVerifyCode.as_view(), name='register_verify'),
    path('/passwordverify', ChangePasswordVerifyCode.as_view(), name='password_verify'),
    path('/login', LoginView.as_view(), name='login'),
    path('/register', RegisterView.as_view(), name='register'),
    path('/changepassword', ChangePasswordView.as_view(), name='change_password'),
    # 管理后台接口
    path('/admin/userinfo', UserInfoView.as_view(), name='userinfo'),
    path('/admin/all-accounts', AdminGetAllAccounts.as_view(), name='get_all_accounts'),
    path('/admin/change-password', AdminChangeAccountPassword.as_view(), name='change_password'),
    path('/admin/modify-account', AdminModifyAccount.as_view(), name='modify_account'),
    path('/admin/activate-account', AdminActivateAccount.as_view(), name='activate_account'),
    path('/admin/suspend-account', AdminSuspendAccount.as_view(), name='suspend_account'),
    path('/admin/delete-account', AdminDeleteAccount.as_view(), name='delete_account'),
]