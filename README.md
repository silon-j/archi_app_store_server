# django-server-template
 基于 django 最新稳定版搭建的后端服务定制化框架，解决 django 原生部分功能不好用的问题，并提供定制化开发辅助，提升开发效率

# 开发需知

本项目采用当前最新 django LTS 版本 4.2 为基础进行搭建，请确保您的开发环境满足以下要求：

- Python 3.10 或更高版本
- Django 4.2 及补丁版本

[我应该使用哪个版本的 Python 来配合 Django](https://docs.djangoproject.com/zh-hans/4.2/faq/install/#faq-python-version-support)

以上要求为Django官方要求，本项目提供了一些Django拓展功能，如需完全支持，请使用python3.10或以上版本


## 依赖安装

```bash
pip install -r requirements.txt
```

## 数据库迁移

```shell
python manage.py makemigrations
python manage.py migrate
```

## 项目启动方式

项目使用 gunicorn 进行部署，启动命令如下：

```shell
gunicorn server.wsgi:application -c gunicorn_config.py --bind 0.0.0.0:8000
```


windows中不支持 gunicorn，开发调试可使用原始 `runserver` 命令运行

项目运行默认会使用 `settings.development` 配置文件，如需使用其他配置文件，请使用以下命令：

```shell
python manage.py runserver --settings=settings.local 0.0.0.0:8000
```

## 数据库连接

[连接数据库指引](https://docs.djangoproject.com/zh-hans/4.2/topics/install/#database-installation)

## 时间处理

项目中推荐使用[arrow](https://github.com/arrow-py/arrow)进行时间处理
