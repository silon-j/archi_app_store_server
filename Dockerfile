# 使用官方 Python 镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 将项目的 requirements.txt 复制到工作目录
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Django 项目代码到工作目录
COPY . .

# 暴露端口 8000
EXPOSE 8000

# 运行 Django 服务器
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]