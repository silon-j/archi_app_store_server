import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from django.conf import settings as server_settings

from typing import List

class MailServer:
    # 发送人
    sender = None
    password = None

    # server
    server = None


    def __init__(
            self, 
            sender:str=server_settings.DEFAULT_EMAIL_ACCOUNT, 
            password:str=server_settings.DEFAULT_EMAIL_PASSWORD) -> None:
        """初始化邮箱server

        Args:
            sender (str): 用户邮箱
            password (str): 邮箱密码
        """
        self.sender = sender
        self.password = password

    def login(self):
        """连接到 SMTP 服务器
        """
        smtp_server = 'smtp.163.com'
        smtp_port = 465
        # self.server = smtplib.SMTP(smtp_server, smtp_port)
        self.server = smtplib.SMTP_SSL(smtp_server, smtp_port)

        # 登录邮箱账户
        self.server.login(self.sender, self.password)


    def send(self, receiver:List[str], subject:str, content:str, attachments:List[str]):
        """_summary_

        Args:
            receiver (list): 接收人邮箱列表
            subject (str): 邮件主题
            content (str): 邮件正文内容
            attachments (list): 附件文件路径列表
        """
        # 初始化多附件内容
        message = MIMEMultipart()
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = self.sender
        message['To'] = ','.join(receiver)

        # 添加纯文本正文内容
        main_text = MIMEText(content, 'html')
        message.attach(main_text)

        # 添加附件内容
        for attachment_path in attachments:
            filename = attachment_path.split(r'/')[-1]
            # 编码文件名，解决163邮箱不能识别中文文件名的问题
            encoded_filename = '=?UTF-8?B?' + base64.b64encode(filename.encode('utf-8')).decode() + '?='
            with open(attachment_path, 'rb') as file:
                attachment = MIMEApplication(file.read())

            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{encoded_filename}"'
            )
            message.attach(attachment)

        # 发送邮件
        self.server.sendmail(
            self.sender,
            receiver,
            message.as_string()
        )
        

    def quit(self):
        """关闭账号连接
        """
        self.server.quit()
