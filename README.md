# QueenVi

Площадка для обмена контентом внутри фан-сообщества Twitch-стримера. Повышает вовлечённость аудитории и взаимодействие со стримером.

Проект представляет собой **MVP бэкенда с API**, развернутый на сервере и доступный по ссылке: https://queenvi.ru/api/v1/.


## Стек технологий

Backend: **Python**, **Django**, **Django REST Framework**, **PostgreSQL**, **Pytest**, **Requests**.

Deployment: **Docker**, **GitHub CI/CD**, **Nginx**, **Gunicorn**, **Linux-сервер**.


## Возможности

### Пользователи

* аутентификация происходит через **Twitch OAuth** и **Django-сессию (Cookie)**;
* в профиле используются **ник и аватар из Twitch**, но пользователь может **изменить аватар** на другой.

### Предложка

Пользователи могут:

* **предлагать видео из YouTube** для просмотра на стриме (вставить ссылку);
* указывать категорию (смешные, трукрайм, познавательные, трейлеры, разные);
* **голосовать** за видео из предложки.

Для ленты предусмотрена **сортировка по дате создания**, а также **фильтрация по категории**.

### Посты

Пользователи могут:

* публиковать фото, видео, аудио (максимальный размер поста — **до 500 МБ**);
* добавлять название и описание;
* публиковать в ленте **«для стрима»** и **«не для стрима»**;
* просматривать ленту постов;
* ставить **лайки** и **комментировать**;
* **жаловаться** на публикации.

Для ленты предусмотрена **сортировка по лайкам и комментариям**, а также **фильтрация по периоду создания публикаций, типу медиа, "для стрима"**.

### Модерация

На площадке может быть **один стример** и **несколько модераторов**. Назначать модераторов может только стример. Модераторы же могут рассматривать жалобы и блокировать пользовательский контент.

В приложении также **настроена админка**. Администратор поддерживает работу проекта и обновляет его.

## Документация Swagger

Документация разработана на основе **drf-spectacular (Swagger)** и доступна по ссылке: https://queenvi.ru/api/v1/docs/.

В ней можно посмотреть и потестировать все эндпоинты.

## Структура проекта

```bash
.
├── .github                  # Директория GitHub Actions
│   └── workflows            # Директории для workflows
│       └── deploy.yml       # Готовый workflow
├── .gitignore               # Игнорирование файлов для Git
├── README.md                # Документация проекта (текущий файл)
├── docs                     # Директория документации Swagger
│   └── QueenVi.yaml         # Актуальная документация Swagger
├── queenvi_project          # Django-проект
    ├── .dockerignore        # Игнорирование файлов для Docker
    ├── .env                 # Переменные окружения (только локально)
    ├── Dockerfile           # Сборка образа бэкенда (Django-проекта)
    ├── api                  # API-слой
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── constants.py     # Константы API-слоя
    │   ├── mixins.py        # Миксины API-слоя
    │   ├── serializers.py   # Сериализаторы API-слоя
    │   ├── urls.py          # Эндпоинты API-слоя
    │   └── views.py         # Представления API-слоя
    ├── conftest.py          # Общие фикстуры Pytest
    ├── core                 # Общие компоненты проекта
    │   ├── __init__.py
    │   ├── constants.py     # Общие константы
    │   ├── errors.py        # Общие исключения
    │   ├── mixins.py        # Общие миксины
    │   ├── utils.py         # Общие вспомогательные функции
    │   └── validators.py    # Общие валидаторы
    ├── docker-compose.prod.yml   # Оркестрация для продакшена (db, backend, nginx)
    ├── docker-compose.yml   # Оркестрация для локальной разработки (db)
    ├── logs                 # Директория с логами (только локально)
    │   └── django.log       # Логи (только локально)
    ├── manage.py            
    ├── media                # Директория медиа (только локально)
    ├── nginx                # Директория с nginx
    │   ├── Dockerfile       # Сборка образа конфигурации nginx
    │   └── nginx.conf       # Конфигурация nginx
    ├── post                 # Приложение публикаций
    │   ├── __init__.py
    │   ├── admin.py         # Админка для публикаций
    │   ├── apps.py
    │   ├── constants.py     # Константы публикаций
    │   ├── errors.py        # Исключения публикаций
    │   ├── filters.py       # Фильтры публикаций
    │   ├── migrations       # Миграции публикаций
    │   ├── models.py        # Модели публикаций
    │   ├── tests            # Тесты публикаций
    │   ├── utils.py         # Вспомогательные функции публикаций
    │   └── validators.py    # Валидаторы публикаций
    ├── pytest.ini           # Конфигурация Pytest
    ├── queenvi_project      # Директория конфигурации Django-проекта
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py      # Конфигурация Django-проекта
    │   ├── urls.py          # Основные эндпоинты
    │   └── wsgi.py
    ├── requirements.txt     # Зависимости
    ├── user                 # Приложение пользователей
    │   ├── __init__.py
    │   ├── admin.py         # Админка для пользователей
    │   ├── apps.py
    │   ├── constants.py     # Константы пользователей 
    │   ├── errors.py        # Исключения пользователей
    │   ├── migrations       # Миграции пользователей
    │   ├── models.py        # Модели пользователей
    │   ├── permissions.py   # Пермишены пользователей
    │   ├── services.py      # Аутентификация через Twitch OAuth
    │   ├── tests            # Тесты пользователей
    │   ├── utils.py         # Вспомогательные функции пользователей
    │   └── validators.py    # Валидаторы пользователей
    └── youtube_suggestion   # Приложение предложки
        ├── __init__.py
        ├── admin.py         # Админка для предложки
        ├── apps.py
        ├── constants.py     # Константы предложки
        ├── errors.py        # Исключения предложки
        ├── migrations       # Миграции предложки
        ├── models.py        # Модели предложки
        ├── services.py      # YouTube API
        └── tests            # Тесты предложки
```


## Развёртывание

Для локального запуска потребуется: **Python**, **Docker** и **Git**.

### 1. Клонирование репозитория

```bash
git clone https://github.com/TimurBikmaev/queenvi_project.git
cd queenvi_project  # Перейдите в директорию проекта
```

### 2. Создание окружения и установка зависимостей

```bash
python -m venv venv
. venv/Scripts/activate
cd queenvi_project  # Перейдите в директорию Django-проекта
pip install -r requirements.txt
```

### 3. Генерация секретного ключа Django

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Если Django не сможет прочитать ключ, то пересоздайте его.

### 4. Настройка переменных окружения

Переименуйте файл `.env.example` на `.env`. Откройте его и укажите значение переменной:

```env
DJANGO_SECRET_KEY=<сгенерированный секретный ключ>
```

Закройте файл и продолжайте работать в терминале.

### 5. Запуск Docker Compose (запустит только PostgreSQL)

```bash
docker compose up -d
```

### 6. Применение миграций

```bash
python manage.py migrate
```

### 7. Создание администратора

```bash
python manage.py createsuperuser
```

Админка доступна по адресу: http://localhost:8000/admin/

### 8. Запуск сервера разработки

```bash
python manage.py runserver
```

### 9. Выполнение авторизованных запросов в Swagger локально

#### ***Аутентификация через интеграцию Twitch API***

**ВНИМАНИЕ**: Если у вашего Twitch-аккаунта включена двухфакторная аутентификация, используйте аутентификацию через Twitch. В противном случае используйте альтернативную аутентификацию (см. ниже):
1. Перейдите на https://dev.twitch.tv/;
2. Авторизуйтесь и перейдите в консоль (вверху справа);
3. Справа нажмите `Подать заявку`, заполните данные и нажмите `Создать`:
```text
Название: <ваше_название>
OAuth Redirect URL: http://localhost:8000/api/v1/profile/twitch_callback/
Категория: Website Integration
Тип клиента: Конфиденциально
```
4. Перейдите в `Функции` заявки;
5. Нажмите `Новый секретный код`;
6. Скопируйте значения `Идентификатор клиента`, `Новый секретный код` и вставьте их в `.env`:
```env
TWITCH_CLIENT_ID=<идентификатор клиента>
TWITCH_CLIENT_SECRET=<новый секретный код>
``` 

#### ***Альтернативная аутентификация***
1. Остановите работу сервера разработки (`Ctrl+C`). Cоздайте пользователя в терминале (поочередно вводите команды):
```bash
python manage.py shell
```
```bash
from django.contrib.auth import get_user_model
```
```bash
User = get_user_model()
```
```bash
user = User.objects.create(
    username='<введите username>',
    password='<введите любой пароль>', 
    role='<выберите роль из user/moder/streamer>', 
    twitch_id='<любое уникальное значение>',
    twitch_avatar='test'
)
```
```bash
exit
```
2. Перейдите в  `api` - `views.py`. Сделайте импорт `from django.contrib.auth import login` (добавьте строку в начало модуля);
3. Найдите `UserViewSet` - action `twitch_login`. Переопределите action:
```
def twitch_login(self, request):
    user = self.get_queryset().get(username='<username созданного вами пользователя>')
    login(request, user)
    serializer = self.get_serializer(user)
    return Response(serializer.data, HTTPStatus.OK)
```  

#### ***После подготовки к аутентификации***

при запущенном сервере разработки пройдите аутентификацию по адресу http://localhost:8000/api/v1/profile/twitch_login/. Перейдите в `DevTools (F12)`, выберите `Application` сверху и `Cookies` слева. Скопируйте значения `sessionid`, `csrftoken` и вставьте их в форму авторизации Swagger (http://localhost:8000/api/v1/docs/):
```text
cookieAuth: <sessionid>
csrfAuth: <csrftoken>
```

Подробнее об авторизации: https://queenvi.ru/api/v1/docs/#/%D0%90%D1%83%D1%82%D0%B5%D0%BD%D1%82%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%86%D0%B8%D1%8F/profile_twitch_login_retrieve.

### 10. Загрузка YouTube-видео в предложку локально

Чтобы загружать видео из YouTube локально, необходимо интегрировать YouTube API в приложении:
1. Перейдите на https://console.cloud.google.com/;
2. Создайте новый проект (кнопка вверху справа) и выберите его;
3. Откройте `APIs & Services` слева и выберите `Library`;
4. В поиске найдите `YouTube Data API v3` и нажмите `Enable`;
5. Откройте `APIs & Services` и выберите слева вкладку `Credentials`;
6. Нажмите вверху `Create credentials` и выберите `API key`. Нажмите `Create`:
```text
name: <ваше_название>
Select API restrictions: YouTube Data API v3
Application restrictions: None
```
7. Нажмите `Show key`, скопируйте значение и вставьте в `.env`:
```env
GOOGLE_API_KEY=<ваш API key>
```
Перезапустите локальный сервер разработки.


## Тестирование

Для автоматизированного тестирования используется **Pytest**. Если вы используете **альтернативную аутентификацию**, то **тесты не пройдут**.

Запуск тестов:

```bash
pytest
```


## CI/CD

Для автоматического обновления проекта на сервере используется GitHub Actions. Pipeline запускается при push в ветку main. В pipeline входит:
1. Запуск автоматических тестов на **Pytest**;
2. **Build** и **push** Docker-образов (backend + nginx) в Docker Hub;
3. Запуск **docker-compose.prod.yml (db, backend, nginx)** на сервере.


## Перспективы

Проект планируется расширять и поддерживать. В дальнейшем планируется реализовать: 
* frontend-часть;
* улучшение модерации (автоматизация банов за жалобы, отчетность перед стримером);
* улучшение комментариев (возможность ответить на другой комментарий, написать и поставить реакцию);
* внедрение новых реакций на публикации.

## Автор: Тимур Бикмаев, backend-разработчик на Python

Telegram: https://t.me/w_NeVeR_w

Почта: bikma2004@gmail.com

Портфолио: https://github.com/TimurBikmaev

