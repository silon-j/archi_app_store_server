from django.core.management.base import BaseCommand
from apps.account.models import Account


class Command(BaseCommand):
    help = '账户管理'

    def add_arguments(self, parser):
        parser.add_argument('action', data_type=str, help='执行动作')
        parser.add_argument('-u', required=False, help='用户名')
        parser.add_argument('-p', required=False, help='账户密码')
        parser.add_argument('-n', required=False, help='账户昵称')
        parser.add_argument('-s', default=False,
                            action='store_true', help='是否是超级用户（默认否）')

    def echo_success(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def echo_error(self, msg):
        self.stderr.write(self.style.ERROR(msg))

    def print_help(self, *args):
        message = '''
        账户管理命令用法：
            account add    创建账户，例如：account add -u admin -p 123 -n 管理员 -s
            account reset  重置账户密码，例如：account reset -u admin -p 123
            account enable 启用被禁用的账户，例如：account enable -u admin
        '''
        self.stdout.write(message)

    def handle(self, *args, **options):
        action = options['action']
        if action == 'add':
            if not all((options['u'], options['p'], options['n'])):
                self.echo_error('缺少参数')
                self.print_help()
            elif Account.objects.filter(username=options['u'], deleted_at__isnull=True).exists():
                self.echo_error(f'已存在用户名为【{options["u"]}】的用户')
            else:
                Account.objects.create(
                    username=options['u'],
                    nickname=options['n'],
                    password_hash=Account.make_password(options['p']),
                    is_super=options['s'],
                    can_admin=options['s']
                )
                self.echo_success('创建用户成功')
        elif action == 'enable':
            if not options['u']:
                self.echo_error('缺少参数')
                self.print_help()
            account = Account.objects.filter(
                username=options['u'], deleted_at__isnull=True).first()
            if not account:
                return self.echo_error(f'未找到登录名为【{options["u"]}】的账户')
            account.is_active = True
            account.save()
            self.echo_success('账户已启用')
        elif action == 'reset':
            if not all((options['u'], options['p'])):
                self.echo_error('缺少参数')
                self.print_help()
            account = Account.objects.filter(
                username=options['u'], deleted_at__isnull=True).first()
            if not account:
                return self.echo_error(f'未找到登录名为【{options["u"]}】的账户')
            account.password_hash = Account.make_password(options['p'])
            account.save()
            self.echo_success('账户密码已重置')
        else:
            self.echo_error('未识别的操作')
            self.print_help()