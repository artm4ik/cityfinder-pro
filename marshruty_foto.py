import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import shutil

from baza import poluchit_bazu
from modeli import Polzovatel, Mesto
from bezopasnost import poluchit_tekushego_polzovatelya

router = APIRouter(prefix="/places", tags=["Фото Мест"])

# ==========================================
# Загрузка фото для места
# ==========================================
@router.post("/{id_mesta}/photo")
def zagruzit_foto_mesta(
    id_mesta: int,
    foto: UploadFile = File(...),
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """
    Загружает фотографию для определенного места.
    Фото сохраняется в папку static/
    """
    
    # Проверяем, существует ли место и принадлежит ли оно текущему пользователю
    mesto = baza.query(Mesto).filter(
        Mesto.id == id_mesta,
        Mesto.id_polzovatelya == tekushiy_polzovatel.id
    ).first()
    
    if not mesto:
        raise HTTPException(status_code=404, detail="Место не найдено или это не ваше место")

    # Создаем уникальное имя файла, чтобы разные картинки не перезаписывали друг друга
    # Формат будет примерно такой: mesto_5_photo.jpg
    rasshirenie = foto.filename.split(".")[-1] # получаем jpg или png
    novoe_imya_fayla = f"mesto_{id_mesta}_photo.{rasshirenie}"
    
    # Путь для сохранения: папка static/название_файла
    put_sohraneniya = f"static/{novoe_imya_fayla}"
    
    # Сохраняем физический файл на жесткий диск (в папку static)
    with open(put_sohraneniya, "wb") as buffer:
        shutil.copyfileobj(foto.file, buffer)
        
    # Сохраняем ПУТЬ к фото в базе данных (чтобы потом показать его на сайте)
    mesto.put_k_foto = f"/{put_sohraneniya}"
    baza.commit()
    
    return {"soobshchenie": "Фото успешно загружено", "put_k_foto": mesto.put_k_foto}
