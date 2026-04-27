from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from baza import poluchit_bazu
from modeli import Polzovatel

# ==========================================
# 1. Настройки безопасности (Токены и Пароли)
# ==========================================

# Секретный ключ для создания токенов (в реальном проекте его прячут в .env файл)
SEKRETNYI_KLYUCH = "super_sekretnyi_klyuch_dlya_cityfinder_pro_2026"
ALGORITM = "HS256"
VREMYA_ZIZNI_TOKENA_MINUTY = 60 * 24 * 7 # Токен живет 7 дней

# Инструмент для хэширования паролей (чтобы в базе хранилась "абракадабра", а не реальный пароль)
kontekst_parolei = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Указываем FastAPI, где находится путь для получения токена (авторизации)
# Это нужно для встроенной документации Swagger (/docs)
oauth2_shema = OAuth2PasswordBearer(tokenUrl="auth/login")

# ==========================================
# 2. Функции для работы с паролями
# ==========================================

def proverit_parol(obychnyi_parol: str, hesh_parolya: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хэшем в базе."""
    return kontekst_parolei.verify(obychnyi_parol, hesh_parolya)

def poluchit_hesh_parolya(parol: str) -> str:
    """Превращает обычный пароль в защищенный хэш."""
    return kontekst_parolei.hash(parol)

# ==========================================
# 3. Функции для работы с токенами (JWT)
# ==========================================

def sozdat_token_dostupa(dannie: dict) -> str:
    """Создает JWT токен для пользователя после успешного входа."""
    dannie_dlya_tokena = dannie.copy()
    
    # Устанавливаем время, когда токен протухнет (умрет)
    vremya_istecheniya = datetime.utcnow() + timedelta(minutes=VREMYA_ZIZNI_TOKENA_MINUTY)
    dannie_dlya_tokena.update({"exp": vremya_istecheniya})
    
    # Создаем сам токен, зашифровав данные нашим секретным ключом
    token = jwt.encode(dannie_dlya_tokena, SEKRETNYI_KLYUCH, algorithm=ALGORITM)
    return token

# ==========================================
# 4. Функция для проверки, кто сейчас авторизован
# ==========================================

def poluchit_tekushego_polzovatelya(
    token: str = Depends(oauth2_shema), 
    baza: Session = Depends(poluchit_bazu)
) -> Polzovatel:
    """
    Эта функция автоматически проверяет токен пользователя.
    Если токен верный, она находит пользователя в базе и возвращает его.
    Если токен неверный или протух, она выдает ошибку 401 (Не авторизован).
    """
    oshibka_avtorizacii = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные (неверный токен)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Пытаемся расшифровать токен
        rasshifrovannye_dannie = jwt.decode(token, SEKRETNYI_KLYUCH, algorithms=[ALGORITM])
        email: str = rasshifrovannye_dannie.get("sub")
        if email is None:
            raise oshibka_avtorizacii
    except JWTError:
        # Если токен поддельный или протух
        raise oshibka_avtorizacii
        
    # Ищем пользователя в базе по email из токена
    polzovatel = baza.query(Polzovatel).filter(Polzovatel.email == email).first()
    if polzovatel is None:
        raise oshibka_avtorizacii
        
    return polzovatel
