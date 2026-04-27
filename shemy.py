from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ==========================================
# Схемы для Мест (Mesto)
# ==========================================

# Базовая схема, содержит общие поля
class MestoBaza(BaseModel):
    nazvanie: str
    kategoriya: str
    adres: str
    shirota: Optional[float] = None
    dolgota: Optional[float] = None
    reiting: Optional[int] = 5
    cena: Optional[str] = "Средне"
    zametki: Optional[str] = None

# Схема для создания нового места (пользователь отправляет эти данные)
class MestoSozdanie(MestoBaza):
    pass

# Схема для возврата данных о месте (сервер отправляет эти данные обратно)
class MestoOtvet(MestoBaza):
    id: int
    put_k_foto: Optional[str] = None
    data_dobavleniya: datetime
    id_polzovatelya: int

    # Эта настройка говорит Pydantic, что нужно читать данные из SQLAlchemy моделей
    class Config:
        from_attributes = True

# ==========================================
# Схемы для Пользователей (Polzovatel)
# ==========================================

# Базовая схема
class PolzovatelBaza(BaseModel):
    email: EmailStr # EmailStr проверяет, что это реальный формат почты
    gorod: Optional[str] = "Не указан"

# Схема для регистрации (пользователь отправляет пароль)
class PolzovatelSozdanie(PolzovatelBaza):
    parol: str

# Схема для возврата данных профиля (МЫ НЕ ВОЗВРАЩАЕМ ПАРОЛЬ!)
class PolzovatelOtvet(PolzovatelBaza):
    id: int
    est_pro_versiya: bool
    data_registracii: datetime
    # Список мест пользователя. Используем схему MestoOtvet
    mesta: List[MestoOtvet] = []

    class Config:
        from_attributes = True

# Схема для авторизации (вход по токену)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
