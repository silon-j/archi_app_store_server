import json
import socket
from django.http import HttpResponse as DjangoHttpResponse
from django.db.models import QuerySet
from django.core.paginator import Paginator
from dataclasses import dataclass, field
from typing import Any, Callable, Dict
from enum import Enum
from .error import ErrorType, ShowType
from .extend import JsonEncoder


class HttpStatus(Enum):
    HTTP_100_CONTINUE = 100
    HTTP_101_SWITCHING_PROTOCOLS = 101
    HTTP_102_PROCESSING = 102
    HTTP_103_EARLY_HINTS = 103
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_203_NON_AUTHORITATIVE_INFORMATION = 203
    HTTP_204_NO_CONTENT = 204
    HTTP_205_RESET_CONTENT = 205
    HTTP_206_PARTIAL_CONTENT = 206
    HTTP_207_MULTI_STATUS = 207
    HTTP_208_ALREADY_REPORTED = 208
    HTTP_226_IM_USED = 226
    HTTP_300_MULTIPLE_CHOICES = 300
    HTTP_301_MOVED_PERMANENTLY = 301
    HTTP_302_FOUND = 302
    HTTP_303_SEE_OTHER = 303
    HTTP_304_NOT_MODIFIED = 304
    HTTP_305_USE_PROXY = 305
    HTTP_306_RESERVED = 306
    HTTP_307_TEMPORARY_REDIRECT = 307
    HTTP_308_PERMANENT_REDIRECT = 308
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_402_PAYMENT_REQUIRED = 402
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_405_METHOD_NOT_ALLOWED = 405
    HTTP_406_NOT_ACCEPTABLE = 406
    HTTP_407_PROXY_AUTHENTICATION_REQUIRED = 407
    HTTP_408_REQUEST_TIMEOUT = 408
    HTTP_409_CONFLICT = 409
    HTTP_410_GONE = 410
    HTTP_411_LENGTH_REQUIRED = 411
    HTTP_412_PRECONDITION_FAILED = 412
    HTTP_413_REQUEST_ENTITY_TOO_LARGE = 413
    HTTP_414_REQUEST_URI_TOO_LONG = 414
    HTTP_415_UNSUPPORTED_MEDIA_TYPE = 415
    HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE = 416
    HTTP_417_EXPECTATION_FAILED = 417
    HTTP_418_IM_A_TEAPOT = 418
    HTTP_421_MISDIRECTED_REQUEST = 421
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_423_LOCKED = 423
    HTTP_424_FAILED_DEPENDENCY = 424
    HTTP_425_TOO_EARLY = 425
    HTTP_426_UPGRADE_REQUIRED = 426
    HTTP_428_PRECONDITION_REQUIRED = 428
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS = 451
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_501_NOT_IMPLEMENTED = 501
    HTTP_502_BAD_GATEWAY = 502
    HTTP_503_SERVICE_UNAVAILABLE = 503
    HTTP_504_GATEWAY_TIMEOUT = 504
    HTTP_505_HTTP_VERSION_NOT_SUPPORTED = 505
    HTTP_506_VARIANT_ALSO_NEGOTIATES = 506
    HTTP_507_INSUFFICIENT_STORAGE = 507
    HTTP_508_LOOP_DETECTED = 508
    HTTP_509_BANDWIDTH_LIMIT_EXCEEDED = 509
    HTTP_510_NOT_EXTENDED = 510
    HTTP_511_NETWORK_AUTHENTICATION_REQUIRED = 511

    @classmethod
    def is_valid_code(cls, code):
        return any(code == item.value for item in cls)

    @staticmethod
    def is_informational(code):
        return 100 <= code <= 199

    @staticmethod
    def is_success(code):
        return 200 <= code <= 299

    @staticmethod
    def is_redirect(code):
        return 300 <= code <= 399

    @staticmethod
    def is_client_error(code):
        return 400 <= code <= 499

    @staticmethod
    def is_server_error(code):
        return 500 <= code <= 599


@dataclass
class JsonResponse(DjangoHttpResponse):
    """自定义格式Json Response"""
    data: Any = None
    status_code: HttpStatus = HttpStatus.HTTP_200_OK
    error_type: ErrorType | None = None
    error_code: int | None = None
    error_message: str | None = None
    show_type: ShowType = ShowType.SILENT
    success: bool = field(init=False, default=True)
    host: str = field(default_factory=lambda: socket.gethostname())

    def __post_init__(self):
        if any([self.error_type, self.error_message]):
            self.success = False
            self.data = {}
            if not self.show_type:
                self.show_type = ShowType.MESSAGE_ERROR

        if self.error_type:
            self.error_code = self.error_type.code
            self.error_message = self.error_type.message

        """自动解析查询结果"""
        if hasattr(self.data, 'to_dict'):
            self.data = self.data.to_dict()
        elif isinstance(self.data, (list, QuerySet)) and all([hasattr(item, 'to_dict') for item in self.data]):
            self.data = [item.to_dict() for item in self.data]

        super().__init__(
            content=json.dumps(vars(self), cls=JsonEncoder, ensure_ascii=False),
            content_type='application/json',
            status=self.status_code.value if isinstance(self.status_code, HttpStatus) else self.status_code
        )


def paginate_data(data:QuerySet, current:int, page_size:int=10, item_handler:Callable=None) -> Dict[str, Any]:
    """根据分页参数，返回分页数据

    Args:
        data (QuerySet): 需要分页的数据
        current (int): 指定获取的分页页数
        page_size (int, optional): 每页数据量. Defaults to 10.
        item_handler (Callable, optional): 对每条数据进行处理的函数. Defaults to None.

    Returns:
        Dict[str, Any]: _description_
    """
    paginator = Paginator(data, page_size)

    total_count = paginator.count
    total_pages = paginator.num_pages

    paginated_data = paginator.page(current).object_list

    if item_handler:
        paginated_data = [item_handler(item) for item in paginated_data]

    return {
        'current': current,
        'list': paginated_data,
        'pageSize': page_size,
        'totalCount': total_count,
        'totalPages': total_pages
    }