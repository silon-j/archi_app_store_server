import random
import string


def get_client_ip(request) -> str:
    """获取请求人的ip
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_random_str(length: int = 4, is_digits: bool = True) -> str:
    """_summary_: 生成随机字符串

    Args:
        length (int, optional): 生成长度. Defaults to 4.
        is_digits (bool, optional): 是否纯数字. Defaults to True.

    Returns:
        str: 随机字符串
    """
    words = string.digits if is_digits else string.ascii_letters + string.digits
    return ''.join(random.sample(words, length))