from django.test import TestCase
from django.urls import reverse
from apps.account.models import Account, AccountEmailAuthCode, EmailAuthCodeChoice
from django.utils import timezone
from datetime import timedelta

class AccountTestCase(TestCase):

    def setUp(self):
        self.new_user_email: str = "newuser@ecadi.com"
        self.register_code = "987654" 
        # 创建一个示例用户
        self.user = Account.objects.create(
            username='testuser',
            fullname='Test User',
            department='IT',
            email='test@ecadi.com',
            password_hash=Account.make_password('testpassword')
        )

        # 创建一个密码的验证码
        self.verify_code_password = AccountEmailAuthCode.objects.create(
            email=self.user.email,
            code='123456',
            code_choice=EmailAuthCodeChoice.PASSWORD,
            expired=timezone.now() + timedelta(minutes=5),
            is_valid=True,
            is_success=False
        )

        # 创建一个注册的验证码
        self.verify_code_register = AccountEmailAuthCode.objects.create(
            email=self.new_user_email,
            code=self.register_code,
            code_choice=EmailAuthCodeChoice.REGISTER,
            expired=timezone.now() + timedelta(minutes=5),
            is_valid=True,
            is_success=False
        )

    def test_change_password_success(self):
        # 模拟发送请求
        response = self.client.post(reverse('change_password'), {
            'username': self.user.username,
            'password': 'newpassword',
            'verify_code': self.verify_code_password.code,
        }, content_type='application/json')

        # 检查响应状态码
        self.assertEqual(response.status_code, 201)
        # 检查响应数据
        self.assertEqual(response.json()['data'], "密码修改成功")
        # 检查密码是否更新
        self.user.refresh_from_db()
        self.assertTrue(self.user.verify_password('newpassword'))

    def test_register_success(self):
        # 模拟发送请求
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'fullname': 'New User',
            'department': 'HR',
            'email': self.new_user_email,
            'password': 'newpassword',
            'verify_code': self.register_code,
        }, content_type='application/json')

        # 检查响应状态码
        self.assertEqual(response.status_code, 201)
        # 检查响应数据
        self.assertEqual(response.json()['data'], "注册成功")
        # 检查新用户是否创建
        new_user = Account.objects.filter(username='newuser').exists()
        self.assertTrue(new_user)

    def test_login_success(self):
        # 模拟登录请求
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'testpassword',
        }, content_type='application/json')

        # 检查响应状态码
        self.assertEqual(response.status_code, 201)
        # 检查响应数据是否为生成的 token
        token = response.json()['data']['token']
        user_state = Account.objects.filter(username=self.user.username).first()
        self.assertEqual(token, user_state.access_token)

    def test_login_fail(self):
        # 模拟发送请求（错误的密码）
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'wrongpassword',
        }, content_type='application/json')

        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        # 检查响应数据
        self.assertEqual(response.json()['errorType'][0], 20102)
