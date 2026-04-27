import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from baza import poluchit_bazu
from modeli import Polzovatel, Mesto
from bezopasnost import poluchit_tekushego_polzovatelya

router = APIRouter(prefix="/export", tags=["Экспорт данных"])

# ==========================================
# Экспорт мест в CSV (Только для PRO)
# ==========================================
@router.get("/csv")
def eksportirovat_v_csv(
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """
    Генерирует CSV-файл со всеми местами пользователя.
    Доступно только для пользователей с Pro-версией.
    """
    
    # Проверяем, есть ли Pro-версия
    if not tekushiy_polzovatel.est_pro_versiya:
        raise HTTPException(
            status_code=403, 
            detail="Экспорт в CSV доступен только в Pro-версии."
        )

    # Получаем все места пользователя
    mesta = baza.query(Mesto).filter(Mesto.id_polzovatelya == tekushiy_polzovatel.id).all()

    # Создаем виртуальный файл в оперативной памяти (чтобы не сохранять на жесткий диск)
    fayl_v_pamyati = io.StringIO()
    
    # Настраиваем писателя CSV
    pisatel = csv.writer(fayl_v_pamyati, delimiter=';')
    
    # Пишем заголовки колонок
    pisatel.writerow(['Название', 'Категория', 'Адрес', 'Рейтинг', 'Цена', 'Заметки', 'Дата добавления'])
    
    # Пишем данные каждого места
    for mesto in mesta:
        data_krasivaya = mesto.data_dobavleniya.strftime("%d.%m.%Y %H:%M") if mesto.data_dobavleniya else ""
        pisatel.writerow([
            mesto.nazvanie,
            mesto.kategoriya,
            mesto.adres,
            mesto.reiting,
            mesto.cena,
            mesto.zametki or "",
            data_krasivaya
        ])

    # Возвращаемся в начало виртуального файла, чтобы FastAPI мог его прочитать и отправить
    fayl_v_pamyati.seek(0)

    # Возвращаем файл как StreamingResponse (поток данных), чтобы браузер начал его скачивать
    return StreamingResponse(
        iter([fayl_v_pamyati.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cityfinder_places.csv"}
    )
