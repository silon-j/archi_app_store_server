import re

from django.core.files import File
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_str
from django.utils.functional import Promise
from typing import Match, Dict, Any, List


def underscore_to_camel(match: Match[str]) -> str:
    """
    将匹配的下划线分隔组转换为驼峰格式。
    
    参数:
        match: 表示匹配组的正则表达式匹配对象。
        
    返回:
        str: 转换后的驼峰格式字符串。
    """
    group = match.group()
    if len(group) == 3:
        return group[0] + group[2].upper()
    else:
        return group[1].upper()


def is_iterable(obj: Any) -> bool:
    """
    检查对象是否可迭代。
    
    参数:
        obj: 要检查是否可迭代的任意对象。
        
    返回:
        bool: 如果对象可迭代则返回True，否则返回False。
    """
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def get_underscoreize_re(options: Dict[str, Any]) -> re.Pattern:
    """
    获取用于将驼峰命名转换为下划线分隔格式的编译正则表达式模式。
    
    参数:
        options (dict): 用于配置正则表达式模式的选项字典。
        
    返回:
        re.Pattern: 编译后的正则表达式模式。
    """
    if options.get("no_underscore_before_number"):
        pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z](?=[a-z])))([A-Z])"
    else:
        pattern = (r"([a-z0-9]|[A-Z]?(?=[A-Z0-9](?=[a-z0-9]|(?<![A-Z])$)))([A-Z]|(?<=[a-z])[0-9]"
                   r"(?=[0-9A-Z]|$)|(?<=[A-Z])[0-9](?=[0-9]|$))")
    return re.compile(pattern)


def camel_to_underscore(name: str, **options: Any) -> str:
    """
    将驼峰命名字符串转换为下划线分隔格式。
    
    参数:
        name (str): 要转换的驼峰格式字符串。
        options (dict): 用于配置转换的可选关键字参数。
        
    返回:
        str: 转换后的下划线分隔字符串。
    """
    underscoreize_re = get_underscoreize_re(options)
    return underscoreize_re.sub(r"\1_\2", name).lower().lstrip("_")


def _get_iterable(data: QueryDict | Dict[str, Any]) -> List | Dict[str, Any]:
    """
    获取输入数据的可迭代表示形式。
    
    参数:
        data: 要转换为可迭代表示形式的输入数据。
        
    返回:
        list or dict: 输入数据的可迭代表示形式。
    """
    if isinstance(data, QueryDict):
        return data.lists()
    else:
        return data.items()


def camelize(data, **options):
    """
    将字典的键从下划线命名转换为驼峰命名。

    参数:
    - data: 要转换的字典或列表。
    - ignore_fields: 忽略转换的字段列表（默认为空）。
    - ignore_keys: 忽略转换的键列表（默认为空）。

    返回值:
    - 转换后的字典或列表。
    """
    # 从options中获取忽略字段和键的列表，默认为空列表。
    ignore_fields = options.get("ignore_fields") or ()
    ignore_keys = options.get("ignore_keys") or ()

    # 如果data是Promise类型，将其转换为字符串。
    if isinstance(data, Promise):
        data = force_str(data)

    # 如果data是字典类型，对其键值对进行转换。
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # 将键和值从可能的懒加载字符串转换为实际的字符串。
            if isinstance(key, Promise):
                key = force_str(key)

            # 判断键是否为字符串且包含下划线，如果是则转换为驼峰命名。
            if isinstance(key, str) and "_" in key:
                camelize_re = re.compile(r"[a-zA-Z0-9]?_[a-zA-Z0-9]")
                new_key = re.sub(camelize_re, underscore_to_camel, key)
            else:
                new_key = key

            # 根据是否在忽略列表中，决定是否对值进行递归转换。
            if key not in ignore_fields and new_key not in ignore_fields:
                result = camelize(value, **options)
            else:
                result = value

            # 根据原键或转换后的键是否在忽略键列表中，决定使用原键还是转换后的键。
            if key in ignore_keys or new_key in ignore_keys:
                new_dict[key] = result
            else:
                new_dict[new_key] = result
        return new_dict

    # 如果data是可迭代的且不是字符串类型，则对其每个元素进行转换。
    if is_iterable(data) and not isinstance(data, str):
        return [camelize(item, **options) for item in data]

    # 对于不符合上述条件的data，直接返回。
    return data


def underscoreize(data, **options):
    """
    将字典的键从驼峰命名转换为下划线命名。

    参数:
    - data: 待转换的数据，可以是字典、列表或其他迭代对象。
    - **options: 额外的选项参数，包括ignore_fields和ignore_keys，用于指定忽略转换的字段或键。

    返回值:
    - 转换后的数据，保持原数据类型不变。
    """
    # 获取忽略转换的字段和键
    ignore_fields = options.get("ignore_fields") or ()
    ignore_keys = options.get("ignore_keys") or ()

    # 如果数据是字典类型
    if isinstance(data, dict):
        new_dict = {}

        # 如果是MultiValueDict类型，进行特殊处理
        if isinstance(data, MultiValueDict):  # if type(data) == MultiValueDict:
            new_data = MultiValueDict()
            for key, value in data.items():
                new_data.setlist(camel_to_underscore(key, **options), data.getlist(key))
            return new_data

        # 遍历字典，转换键名为下划线命名
        for key, value in _get_iterable(data):
            if isinstance(key, str):
                new_key = camel_to_underscore(key, **options)
            else:
                new_key = key

            # 根据ignore_fields判断是否转换值
            if key not in ignore_fields and new_key not in ignore_fields:
                result = underscoreize(value, **options)
            else:
                result = value

            # 根据ignore_keys判断是否使用原键名
            if key in ignore_keys or new_key in ignore_keys:
                new_dict[key] = result
            else:
                new_dict[new_key] = result

        # 如果是QueryDict类型，进行特殊处理
        if isinstance(data, QueryDict):
            new_query = QueryDict(mutable=True)
            for key, value in new_dict.items():
                new_query.setlist(key, value)
            return new_query

        return new_dict

    # 如果数据是列表或其他迭代对象
    if is_iterable(data) and not isinstance(data, (str, File)):
        return [underscoreize(item, **options) for item in data]

    return data

