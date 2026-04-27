from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from baza import poluchit_bazu
from modeli import Polzovatel
from shemy import PolzovatelSozdanie, PolzovatelOtvet, Token
from bezopasnost import (
    poluchit_hesh_parolya, 
    proverit_parol, 
    sozdat_token_dostupa, 
    poluchit_tekushego_polzovatelya
)

# Создаем "Роутер" - это как бы мини-приложение, которое объединяет маршруты
router = APIRouter(prefix="/auth", tags=["Авторизация"])

# ==========================================
# 1. Регистрация нового пользователя
# ==========================================
@router.post("/register", response_model=PolzovatelOtvet, status_code=status.HTTP_201_CREATED)
def zaregistrirovatsya(
    dannie_polzovatelya: PolzovatelSozdanie, 
    baza: Session = Depends(poluchit_bazu)
):
    """Регистрирует нового пользователя в базе."""
    # Шаг 1: Проверяем, нет ли уже такого email в базе
    sushestvuyushiy_polzovatel = baza.query(Polzovatel).filter(
        Polzovatel.email == dannie_polzovatelya.email
    ).first()
    
    if sushestvuyushiy_polzovatel:
        raise HTTPException(
            status_code=400, 
            detail="Этот Email уже зарегистрирован!"
        )

    # Шаг 2: Хэшируем пароль
    zashishennyi_parol = poluchit_hesh_parolya(dannie_polzovatelya.parol)

    # Шаг 3: Создаем пользователя в базе (пароль заменяем на хэш)
    novyi_polzovatel = Polzovatel(
        email=dannie_polzovatelya.email,
        hesh_parolya=zashishennyi_parol,
        gorod=dannie_polzovatelya.gorod
    )

    # Шаг 4: Сохраняем в базу данных
    baza.add(novyi_polzovatel) # добавляем запись
    baza.commit() # подтверждаем изменения
    baza.refresh(novyi_polzovatel) # обновляем данные, чтобы получить присвоенный ID

    # Шаг 5: Возвращаем профиль пользователя (схема PolzovatelOtvet сама скроет пароль)
    return novyi_polzovatel

# ==========================================
# 2. Вход (Логин) и получение токена
# ==========================================
@router.post("/login", response_model=Token)
def voiti(
    forma_vkhoda: OAuth2PasswordRequestForm = Depends(), 
    baza: Session = Depends(poluchit_bazu)
):
    """
    Проверяет логин/пароль и выдает JWT токен.
    ВАЖНО: По стандарту OAuth2, мы используем поле `username` в форме входа. 
    Но в нашем случае `username` - это будет Email пользователя.
    """
    # Шаг 1: Ищем пользователя по email (он лежит в поле username формы)
    polzovatel = baza.query(Polzovatel).filter(
        Polzovatel.email == forma_vkhoda.username
    ).first()

    # Шаг 2: Проверяем, существует ли пользователь и правильный ли пароль
    if not polzovatel or not proverit_parol(forma_vkhoda.password, polzovatel.hesh_parolya):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный Email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Шаг 3: Если всё верно, создаем токен. 
    # В токен мы прячем email пользователя (поле 'sub' - subject)
    token = sozdat_token_dostupa(dannie={"sub": polzovatel.email})

    # Возвращаем токен клиенту
    return {"access_token": token, "token_type": "bearer"}

# ==========================================
# 3. Получение своего профиля (Требуется авторизация!)
# ==========================================
@router.get("/me", response_model=PolzovatelOtvet)
def poluchit_svoi_profil(
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """
    Возвращает профиль текущего пользователя.
    Эта функция работает ТОЛЬКО если пользователь отправил правильный токен.
    За проверку токена отвечает функция `poluchit_tekushego_polzovatelya`.
    """
    # Если токен верный, функция просто возвращает пользователя
    return tekushiy_polzovatel
