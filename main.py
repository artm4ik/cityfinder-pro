from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from baza import dvizhok, BazovayaModel
from modeli import Polzovatel, Mesto

import marshruty_polzovateli
import marshruty_mesta
import marshruty_foto
import marshruty_statistika
import marshruty_eksport # Импортируем маршрут для выгрузки CSV

# ==========================================
# 1. Инициализация базы данных
# ==========================================
# Эта строчка автоматически создает все таблицы (пользователи, места), 
# если они еще не существуют в файле cityfinder.db
BazovayaModel.metadata.create_all(bind=dvizhok)

# ==========================================
# 2. Создание приложения FastAPI
# ==========================================
app = FastAPI(title="CityFinder Pro", description="Личный каталог полезных городских мест")

# Настройки CORS (чтобы браузер не блокировал запросы к API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты для пользователей (регистрация, логин)
app.include_router(marshruty_polzovateli.router)

# Подключаем маршруты для мест (добавление, просмотр, удаление)
app.include_router(marshruty_mesta.router)

# Подключаем маршруты для загрузки фотографий
app.include_router(marshruty_foto.router)

# Подключаем маршруты статистики
app.include_router(marshruty_statistika.router)

# Подключаем маршруты экспорта CSV
app.include_router(marshruty_eksport.router)

# ==========================================
# 3. Подключение статических файлов (фронтенд и картинки)
# ==========================================
# Папка static будет хранить загруженные фото (по адресу /static/имя_фото.jpg)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Папка frontend будет хранить HTML/JS/CSS (по адресу /frontend/index.html)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ==========================================
# 4. Базовый тестовый маршрут (чтобы проверить, что всё работает)
# ==========================================
@app.get("/")
def proverka_raboty():
    return {"soobshenie": "Сервер CityFinder Pro работает! Открой /docs для проверки API."}
