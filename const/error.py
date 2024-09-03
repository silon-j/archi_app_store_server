from libs.boost.error import ErrorType as ErrorTypeBase

class ErrorType(ErrorTypeBase):
    """Error types for the application."""
    REQUEST_ILLEGAL = (10014, '非法请求')
    REQUEST_PARSE_ERROR = (10015, '请求参数不合要求')
    FILE_EXTENSION_ERROR = (10016, '上传文件类型错误')
    FILE_PROCESS_ERROR = (10017, '上传文件解析失败')

    # 请求用户相关错误
    ACCOUNT_ID_EMPTY = (20001, '账户id为空')
    ACCOUNT_DISABLED = (20002, '账户已被禁用')
    ACCOUNT_NOT_EXIST = (20003, '账户不存在')
    ACCOUNT_LOGIN_FAILED = (20004, '用户名或密码错误，30分钟内连续5次错误账户将会被禁用')
    ACCOUNT_EXIST = (20005, '用户已存在')
    ACCOUNT_MAIL_EXIST = (20006, '邮箱已存在')
    ACCOUNT_MAIL_DONT_EXIST = (20007, '邮箱不存在')

    AUTH_FAILED = (20101, '身份认证失败')
    LOGIN_FAILED = (20102, '用户名或密码错误，连续多次错误账户将会被禁用')
    LOGIN_RATE_LIMIT = (20103, '账户密码认证超过请求限制')
    TOKEN_EXPIRED = (20104, '认证已失效，请重新登录')
    PERMIT_FAILED = (20105, '权限不足')
    VERIFY_CODE_ERROR = (20106, '验证码错误或过期')

    # 业务操作错误
    OBJECT_NOT_FOUND = (30001, '操作对象不存在')
    OBJECT_EXISTS = (30002, '操作对象已存在')