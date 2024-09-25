"""
gunicorn 配置
"""
# 绑定ip和端口号
bind = '0.0.0.0:8000'
# 指定Gunicorn处理请求的队列的最大长度，如果监听队列已满，新的请求将被拒绝或丢弃
backlog = 2048
# 超时时间，默认为30s，这个时间指的是处理请求的时间
timeout = 60
# 默认sync模式,使用gevent模式可更好解决处理时长较长的请求
worker_class = 'gevent'
# 进程数，一般填cpu核心数倍数
workers = 8
# 指定每个进程开启的线程数
threads = 2
# 日志级别，这个日志级别指的是错误日志的级别，而访问日志的级别无法设置
loglevel = 'warning'
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
accesslog = "logs/gunicorn/access.log"      # 访问日志文件
errorlog = "logs/gunicorn/error.log"


def pre_fork(server, worker):
    """在每个工作进程启动之前执行一次的可选 Python 函数"""
    pass


def post_worker_init(worker):
    """在每个工作进程退出时执行一次的可选 Python 函数"""
    pass


def worker_exit(server, worker):
    """每当工人完成其所有请求并关闭其连接时，都会调用此函数"""
    pass
