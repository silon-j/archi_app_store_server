from django.views import View
from django.http import HttpRequest, JsonResponse, HttpResponse
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus
from .models import ClientVersion
import yaml

class DesktopClientVersionView(View):

    def get(self, request: HttpRequest):
        # form, error = JsonParser(
        #     Argument('current_version', data_type=str, required=True)
        # ).parse(request.GET)
        # if error:
        #     return JsonResponse(data = {'error_message': '非法请求'}, status=HttpStatus.HTTP_400_BAD_REQUEST.value)
        # client_info = ClientVersion.objects.filter(version_str=form.current_version).first()
        # if not client_info:
        #     return JsonResponse(data = {'error_message': '客户端版本不存在'}, status=HttpStatus.HTTP_404_NOT_FOUND.value)
        latest_info =  ClientVersion.objects.filter(is_latest=True).first()
        yaml_data = {
            'version': latest_info.version_str,
            'files': [
                {
                    'url': latest_info.cos_dir,
                    'sha512': latest_info.sha512_hash,
                    'size': latest_info.size
                }
            ],
            'path': latest_info.cos_dir,
            'sha512': latest_info.sha512_hash,
            'releaseDate': latest_info.created_at.strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
        }
        yaml_content = yaml.safe_dump(yaml_data, default_flow_style=False, sort_keys=False, indent=2, allow_unicode=True)
        response = HttpResponse(yaml_content, content_type="application/octet-stream")
        response["Content-Disposition"] = 'inline; filename="latest.yml"'
        return response