import json
from dataclasses import dataclass
from typing import Any, Callable, Type
from enum import Enum
from libs.boost.extend import AttrDict
from libs.boost.types import JsonParserExtendSettings


class ParseError(BaseException):
    """自定义解析异常
    """
    def __init__(self, message):
        self.message = message


@dataclass
class Argument(object):
    """需要校验的参数对象，用来解析对象内容是否满足后端设定需求
    """
    name: str
    default: Any = None
    data_type: Type = str
    required: bool = True
    nullable: bool = False
    filter_func: Callable | None = None
    handler_func: Callable | None = None
    data_help: str = None

    def parse(self, has_key, value):
        """解析参数
        """
        self._check_kv(has_key, value)
        self._check_type(value)
        if self.filter_func:
            if not self.filter_func(value):
                raise ParseError(
                    self.help or 'Value Error: %s filter_func check failed' % self.name)
        if self.handler_func:
            value = self.handler(value)
        
        return value

    def _check_kv(self, has_key, value):
        """检查key和value
        """
        if not has_key:
            if self.required and self.default is None:
                raise ParseError(
                    self.data_help or 'Required Error: %s is required' % self.name)
            else:
                return self.default
        elif value is None:
            if not self.nullable:
                raise ParseError(
                    self.data_help or 'Nullable Error: %s is not nullable' % self.name)
            else:
                return None

    def _check_type(self, value):
        """检查value类型，并尝试进行类型转换
        """
        try:
            if self.data_type in (list, dict) and isinstance(value, str):
                value = json.loads(value)
                assert isinstance(value, self.data_type)
            elif self.data_type == bool and isinstance(value, str):
                value = value.lower() in ('true', 'false')
                value = value.lower() == 'true'
            elif not isinstance(value, self.data_type):
                value = self.data_type(value)
        except (TypeError, ValueError, AssertionError):
            raise ParseError(
                self.help or 'Type Error: %s type must be %s' % (self.name, self.data_type))



class BaseParser(object):
    """参数解析器基类"""
    def __init__(self, *args):
        self.args = []
        for e in args:
            if isinstance(e, str):
                e = Argument(e)
            elif not isinstance(e, Argument):
                raise TypeError('%r is not instance of Argument' % e)
            self.args.append(e)

    def _get(self, key):
        raise NotImplementedError

    def _init(self, data):
        raise NotImplementedError

    def add_argument(self, **kwargs):
        self.args.append(Argument(**kwargs))

    def parse(self, data=None, clear=False):
        rst = AttrDict()
        try:
            self._init(data)
            for e in self.args:
                has_key, value = self._get(e.name)
                if clear and has_key is False and e.required is False:
                    continue
                rst[e.name] = e.parse(has_key, value)
        except ParseError as err:
            return None, err.message
        return rst, None


class JsonParser(BaseParser):
    """Json解析器"""
    def __init__(self, *args):
        self.__data = None
        super(JsonParser, self).__init__(*args)

    def _get(self, key):
        return key in self.__data, self.__data.get(key)

    def _init(self, data):
        try:
            if isinstance(data, (str, bytes)):
                self.__data = json.loads(data) if data else {}
            else:
                assert hasattr(data, '__contains__')
                assert hasattr(data, 'get')
                assert callable(data.get)
                self.__data = data
        except (ValueError, AssertionError):
            raise ParseError('Invalid data type')
        
    def extend(self, settings:JsonParserExtendSettings):
        paginate = settings.get('paginate', False)
        if paginate == True:
            arg_current_page = Argument('current', type=str, required=True, help='请提供目标页数')
            arg_page_size = Argument('page_size', type=int, required=False, default=10)

            self.add_argument(arg_current_page)
            self.add_argument(arg_page_size)
            return self
        

