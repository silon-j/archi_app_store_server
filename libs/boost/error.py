from enum import Enum, unique

@unique
class ShowType(Enum):
    """错误显示类型，用于前端展示错误信息，与接口规范同步
    """
    SILENT = 0
    MESSAGE_WARNING = 1 # 橙色感叹号
    MESSAGE_ERROR = 2   # 红色叉号
    NOTIFICATION = 4    # 右上角通知框
    PAGE = 9            # 页面跳转


@unique
class ErrorType(Enum):
    """用于view层json返回错误类型，可自行根据业务添加或继承进行拓展"""
    # 示例系统200后处理错误
    # REQUEST_ILLEGAL = (10014, '非法请求')

    @property
    def code(self):
        return self.value[0]
    
    @property
    def message(self):
        return self.value[1]