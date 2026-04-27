from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Ссылка для подключения к базе данных. Используем SQLite (файл cityfinder.db).
URL_BAZY_DANNYH = "sqlite:///./cityfinder.db"

# 2. Создаем "движок" базы данных.
# check_same_thread=False нужно только для SQLite, чтобы FastAPI работал без ошибок.
dvizhok = create_engine(
    URL_BAZY_DANNYH, connect_args={"check_same_thread": False}
)

# 3. Создаем фабрику сессий. Сессия - это временное подключение к базе для отправки запросов.
FabrikaSessiy = sessionmaker(autocommit=False, autoflush=False, bind=dvizhok)

# 4. Создаем базовый класс. От него будут наследоваться все наши модели (таблицы).
BazovayaModel = declarative_base()

# 5. Функция для получения сессии базы данных в маршрутах (API).
def poluchit_bazu():
    baza = FabrikaSessiy()
    try:
        yield baza
    finally:
        baza.close()
