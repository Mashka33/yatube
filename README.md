# **Социальная сеть YaTube**

[![Build and Test](https://github.com/Mashka33/yatube/actions/workflows/python-app.yml/badge.svg)](https://github.com/Mashka33/yatube/actions/workflows/python-app.yml)

- YaTube - социальная сеть для публикации дневников пользователей. + UnitTests (Python3, Django2.2, Pytest, SQLite)
Социальная сеть позволяет зарегестрированным пользователям создавать, редактировать и удалять постов. Также Yatube позволяет просматривать и комментировать записи других авторов. Незарегистрированным пользователям доступен просмотр чужих постов и комментариев.

___

## Установка на локальной машине.

### Cистемные требования:
    python==3.8.6
    Django==2.2.6

### Порядок установки.
1) Клонировать
2) Установить зависимости
3) Запустить

```
git clone https://github.com/Mashka33/yatube.git
pip install -r requirements.txt
python manage.py runserver
```

Проект запускается сервере разработчика на порте 8000.
Проект хранит данные в предустановленной базе SQLite.


Ключевое приложение проекта - __.posts__
> модели (models.py):
>> User - стандартная модель get_user_model библиотеки django.contrib.auth;
>> <br /> Post - пост;
>> <br /> Group - группа постов;
>> <br /> Comment - комментарий;
>> <br /> Follow - подписчики;

> админ-зона (admin.py):
>> управление объектами - можно публиковать новые записи или редактировать/удалять существующие;
>> для создания админа:
```
   python manage.py createsuperuser
```

> тесты в /tests.

Все классы тестов из пакета *django.test*.
для запуска тестов:
```
python3 manage.py test
```
Впоследствие проект был реализован на API, найти его можно по ссылке https://github.com/Mashka33/api_final_yatube.git

*Проект выполнен в рамках обучения Яндекс.Практикум Степановой Марией*
