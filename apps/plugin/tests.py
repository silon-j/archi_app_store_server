import json
import random
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from apps.account.models import Account
from apps.plugin.models import OperationLog, Plugin, PluginCategory, PluginVersion

def get_token_by_account(account):
    return get_or_create_super_account(account=account).access_token

def get_or_create_super_account(account):
    accountObj = Account.objects.filter(username=account).first()
    if accountObj is None:
        accountObj = Account.objects.create(
            username=account,
            fullname=account,
            department='1',
            email=1,
            can_admin=True,
            is_super=True,
            password_hash=Account.make_password(account),
            access_token= uuid.uuid4().hex,
            token_expired = timezone.now() + timedelta(seconds=settings.AUTHENTICATION_EXPIRE_TIME)
        )
    return accountObj

def get_or_create_normal_account(account):
    accountObj = Account.objects.filter(username=account).first()
    if accountObj is None:
        accountObj = Account.objects.create(
            username=account,
            fullname=account,
            department='1',
            email=1,
            can_admin=False,
            is_super=False,
            password_hash=Account.make_password(account),
            access_token= uuid.uuid4().hex,
            token_expired = timezone.now() + timedelta(seconds=settings.AUTHENTICATION_EXPIRE_TIME)
        )
    return accountObj

def get_first_category_and_children():
    categoryObj = PluginCategory.objects.filter(name='建筑').first()
    if categoryObj is None:
        categoryObj = PluginCategory.objects.create(name='建筑')
        PluginCategory.objects.create(name='建筑通用',parent=categoryObj)
    return {
        'id':categoryObj.id,
        'name':categoryObj.name,
        'children_id': categoryObj.children.first().id
    }

def generate_random_plugin_version_data(category):
    return {"name":f'Test{random.randint(1000,9999)}',
                "icon_url":"http://test.com/12345.png",
                "category_ids":[category['children_id']],
                "version_no":"0.0.1.test",
                "description":"this is for unit test",
                "type":Plugin.TYPE_LINK,
                "attachment_url":"http://test.com/12345.zip",
                "execution_file_path":"",
                "authors":[{"name":"Test", "email":"test@eee.com"}],
                "tags":["test"]
                }

class PluginCatagoryViewTests(TestCase):
    def test_post_and_get_plugin(self):
        token = get_token_by_account(account="Lucas")
        headers = {'X-Token': token}
        response = self.client.get(reverse('plugin-category'),headers=headers)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        type_count = len(response_json['data'])
        data = {'name':f'建筑分类{random.randint(1000,9999)}'}
        json_data = json.dumps(data)
        response = self.client.post(reverse('plugin-category'), headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        data = {'name':f'建筑分类{random.randint(1000,9999)}','parent_id':response_json['data'] }
        json_data = json.dumps(data)
        response = self.client.post(reverse('plugin-category'), headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])

class PluginVersionViewTests(TestCase):
    def test_post_and_get_plugin(self):
        token = get_token_by_account(account="Lucas")
        plugin_url = reverse('plugin')
        headers = {'X-Token': token}
        category = get_first_category_and_children()
        data = generate_random_plugin_version_data(category)
        json_data = json.dumps(data)
        response = self.client.post(plugin_url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        response = self.client.get(reverse('plugin-detail'), headers=headers, data = {'version_id': response_json['data']})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        self.assertEqual(response_json['data']['name'], data['name'])
        data = {'name': data['name'], 'category_id':category['id']}
        response = self.client.get(reverse('plugin-version'), headers=headers, data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        self.assertEqual(1, len(response_json['data']))
        self.assertEqual(response_json['data'][0]['name'], data['name'])
        data = {'version_id': response_json['data'][0]['versionId']}
        response = self.client.get(reverse('plugin-detail'), headers=headers, data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])

class OperationLogViewTests(TestCase):
    def setUp(self):
        # 准备测试数据，例如创建一个插件实例
        account = get_or_create_super_account(account="Lucas")
        self.plugin = Plugin.objects.create(name='Test',icon_url='dddd',type=Plugin.TYPE_LINK,created_user=account)
        self.plugin_version =  PluginVersion.objects.create(
                    plugin=self.plugin,
                    version_no='1.0.0',
                    description='Test',
                    attachment_url='plugin.attachment_url',
                    execution_file_path='plugin.execution_file_path',
                    created_user=account
                )
        
    def test_post_and_get_log(self):
        token = get_token_by_account(account="Lucas")
        headers = {'X-Token': token}
        data = {'version_id': self.plugin_version.id}
        url = reverse('plugin-log')
        response = self.client.get(url, headers=headers, data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        count = len(response_json['data'])
        data = {'type':OperationLog.TYPE_OPEN,'version_id': self.plugin_version.id }
        json_data = json.dumps(data)
        response = self.client.post(url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        response = self.client.get(url, headers=headers, data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        self.assertEqual(count + 1, len(response_json['data']))

class AdminRequiredTest(TestCase):
    def setUp(self):
        # 准备测试数据，例如创建一个插件实例
        self.super_user = get_or_create_super_account(account="SuperUser")
        self.normal_user = get_or_create_normal_account(account="NormalUser")
    
    def test_plugin_list_view(self):
        token = self.normal_user.access_token 
        headers = {'X-Token': token}
        url = reverse('plugin-list')
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 403)
        token = self.super_user.access_token 
        headers = {'X-Token': token}
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_plugin_version_list_view(self):
        token = self.normal_user.access_token 
        headers = {'X-Token': token}
        url = reverse('plugin-version-list')
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 403)
        token = self.super_user.access_token 
        headers = {'X-Token': token}
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_plugin_category_list_view(self):
        token = self.normal_user.access_token 
        headers = {'X-Token': token}
        url = reverse('category-list')
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 403)
        token = self.super_user.access_token 
        headers = {'X-Token': token}
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_plugin_category_create_and_patch(self):
        token = self.normal_user.access_token 
        headers = {'X-Token': token}
        url = reverse('plugin-category')
        data = {'name':f'建筑分类{random.randint(1000,9999)}'}
        json_data = json.dumps(data)
        response = self.client.post(url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        token = self.super_user.access_token 
        headers = {'X-Token': token}
        response = self.client.post(url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        data = {'name':f'建筑分类{random.randint(1000,9999)}','id':response_json['data'] }
        response = self.client.post(url, headers=headers, data=json_data, content_type='application/json')
        json_data = json.dumps(data)
        self.assertEqual(response.status_code, 200)

    def test_plugin_and_version_patch(self):
        token = self.normal_user.access_token 
        headers = {'X-Token': token}
        plugin_url = reverse('plugin')
        category = get_first_category_and_children()
        json_data = json.dumps(generate_random_plugin_version_data(category))
        response = self.client.post(plugin_url, headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        version_id = response_json['data']
        json_data = json.dumps({'version_no':f'0.0.1.{random.randint(10,99)}', 'description':'测试修改','id':version_id })
        response = self.client.patch(reverse('plugin-version'), headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        plugin_detail_url = reverse('plugin-detail')
        response = self.client.get(f'{plugin_detail_url}?versionId={version_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.success, True, response_json['errorMessage'])
        plugin_id = response_json['data']['id']
        json_data_plugin = json.dumps({'iconUrl':f'11111', 'name':'测试修改','id':plugin_id })
        response = self.client.patch(reverse('plugin'), headers=headers, data=json_data_plugin, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        token = self.super_user.access_token 
        headers = {'X-Token': token}
        response = self.client.patch(reverse('plugin-version'), headers=headers, data=json_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(reverse('plugin'), headers=headers, data=json_data_plugin, content_type='application/json')
        self.assertEqual(response.status_code, 200)




