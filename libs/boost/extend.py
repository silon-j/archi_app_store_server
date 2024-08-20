import arrow
import json
from datetime import datetime, date as datetime_date
from decimal import Decimal
from enum import Enum


class AttrDict(dict):
    """实现对dict通过.来操作赋值、获取元素，及 del 删除键值对
    """
    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __delattr__(self, item):
        self.__delitem__(item)


class JsonEncoder(json.JSONEncoder):
    """拓展json模块，支持datetime、arrow、decimal、Enum等类型
    """
    def default(self, o):
        if isinstance(o, arrow.Arrow):
            return o.format('YYYY-MM-DD HH:mm:ss')
        elif isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, datetime_date):
            return o.strftime('%Y-%m-%d')
        elif isinstance(o, Decimal):
            return float(o)
    
        elif isinstance(o, Enum):
            return o.value

