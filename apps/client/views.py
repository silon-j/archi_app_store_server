from django.views import View
from django.http import HttpRequest
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus, JsonResponse
from .models import ClientVersion 

class DesktopClientVersionView(View):

    def get(self, request: HttpRequest):
        form, error = JsonParser(
            Argument('current_version', data_type=str, required=True)
        ).parse(request.GET)
        if error:
            return JsonResponse(status_code=HttpStatus.HTTP_400_BAD_REQUEST, error_message=error)
        client_info = ClientVersion.objects.filter(version_str=form.current_version).first()
        if not client_info:
            return JsonResponse(status_code=HttpStatus.HTTP_404_NOT_FOUND, error_message='客户端版本不存在')
        if client_info.is_latest:
            # 已经是新版本了
            response_data = {
                "current_version": client_info.version_str,
                "latest_version": client_info.version_str,
                "release_notes": None,
                "update_available": False,
                "download_url": client_info.cos_dir,
                "pub_date": client_info.created_at,
                "critical": False
            }
            return JsonResponse(data=response_data)
        else:
            #需要更新
            client_latest = ClientVersion.objects.filter(is_latest=True).first()
            response_data = {
                "current_version": client_info.version_str,
                "latest_version": client_latest.version_str,
                "release_notes": client_latest.description,
                "update_available": True,
                "download_url": client_latest.cos_dir,
                "pub_date": client_latest.created_at,
                "critical": False if client_info.is_active else True
            }
            return JsonResponse(data=response_data)