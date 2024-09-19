from django.urls import path
from .views.admin_get_accounts import AdminGetAllAccounts
from .views.admin_modify_account import AdminChangeAccountPassword, AdminModifyAccount
from .views.admin_suspend_account import AdminActivateAccount, AdminSuspendAccount, AdminDeleteAccount


urlpatterns = [
    path('/all-accounts', AdminGetAllAccounts.as_view(), name='get_all_accounts'),
    path('/change-password', AdminChangeAccountPassword.as_view(), name='change_password'),
    path('/modify-account', AdminModifyAccount.as_view(), name='modify_account'),
    path('/activate-account', AdminActivateAccount.as_view(), name='activate_account'),
    path('/suspend-account', AdminSuspendAccount.as_view(), name='suspend_account'),
    path('/delete-account', AdminDeleteAccount.as_view(), name='delete_account'),
]