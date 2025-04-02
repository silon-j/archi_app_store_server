from django.views import View
from django.http import HttpRequest, HttpResponse
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus
from libs.boost.http import JsonResponse 
from .models import ClientVersion
from const.error import ErrorType
import re


class DesktopClientVersionView(View):

    def get(self, request: HttpRequest):

        form, error = JsonParser(
            Argument('current_version', data_type=str, required=True)
        ).parse(request.GET)
        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL, status_code=HttpStatus.HTTP_400_BAD_REQUEST.value)
        client_info = ClientVersion.objects.filter(version_str=form.current_version).first()
        if not client_info:
            return JsonResponse(error_type=ErrorType.OBJECT_NOT_FOUND, status_code=HttpStatus.HTTP_404_NOT_FOUND.value)
        latest_info = client_info if client_info.is_latest else ClientVersion.objects.filter(is_latest=True).first()
        if not latest_info:
            return JsonResponse(error_type=ErrorType.OBJECT_NOT_FOUND, status_code=HttpStatus.HTTP_404_NOT_FOUND.value)
        update_info = {
            "need_update": not client_info.is_latest,
            "latest_version": latest_info.version_str,
            "current_version": client_info.version_str,
            "cos": latest_info.cos_dir,
            "description": self.split_numbered_string(latest_info.description),
            "force_update": not client_info.is_active,
        }
        return JsonResponse(data=update_info)
    
    def split_numbered_string(self, text):
        """
        将带编号的字符串分割成列表

        参数:
            text (str): 输入的字符串，包含编号行

        返回:
            list: 分割后的字符串列表
        """

            
        # 使用正则表达式匹配所有编号条目
        # 匹配模式：数字+点+空格+内容（直到下一个数字或字符串结束）
        pattern = r'(\d+\.\s[^\d]*)'
        matches = re.findall(pattern, text)

        # 清理结果，去除前后空格
        result = [match.strip() for match in matches if match.strip()]

        return result
