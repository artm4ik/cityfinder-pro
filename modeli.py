from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import relationship
import datetime

# Импортируем базовую модель, чтобы сказать SQLAlchemy, что это таблицы
from baza import BazovayaModel

# Таблица 1: Пользователи
class Polzovatel(BazovayaModel):
    __tablename__ = "polzovateli"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hesh_parolya = Column(String) # Мы не храним пароли в открытом виде!
    gorod = Column(String, default="Не указан")
    
    # Это наша "Pro" версия - просто галочка в базе данных.
    est_pro_versiya = Column(Boolean, default=False)
    
    data_registracii = Column(DateTime, default=datetime.datetime.utcnow)

    # Связь с местами. Один пользователь может добавить много мест.
    # Если пользователя удалят, его места тоже удалятся (cascade).
    mesta = relationship("Mesto", back_populates="vladelec", cascade="all, delete-orphan")

# Таблица 2: Места (кафе, сервисы, скрытые локации)
class Mesto(BazovayaModel):
    __tablename__ = "mesta"

    id = Column(Integer, primary_key=True, index=True)
    nazvanie = Column(String, index=True)
    kategoriya = Column(String, index=True) # еда, сервисы, покупки, отдых, акции
    adres = Column(String)
    
    # Координаты для карты (широта и долгота)
    shirota = Column(Float, nullable=True)
    dolgota = Column(Float, nullable=True)
    
    reiting = Column(Integer, default=5) # от 1 до 5
    cena = Column(String, default="Средне") # Дешево, Средне, Дорого
    zametki = Column(Text, nullable=True) # Текстовое описание
    
    # Путь к файлу фото. Если фото нет, будет None.
    put_k_foto = Column(String, nullable=True)
    
    data_dobavleniya = Column(DateTime, default=datetime.datetime.utcnow)

    # Внешний ключ, связывающий место с конкретным пользователем
    id_polzovatelya = Column(Integer, ForeignKey("polzovateli.id"))
    
    # Связь обратно к пользователю
    vladelec = relationship("Polzovatel", back_populates="mesta")
