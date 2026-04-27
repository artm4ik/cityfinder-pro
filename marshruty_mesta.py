from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from baza import poluchit_bazu
from modeli import Polzovatel, Mesto
from shemy import MestoSozdanie, MestoOtvet
from bezopasnost import poluchit_tekushego_polzovatelya

router = APIRouter(prefix="/places", tags=["Места"])

# ==========================================
# 1. Получить список своих мест
# ==========================================
@router.get("/", response_model=List[MestoOtvet])
def poluchit_moi_mesta(
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """Возвращает все места, добавленные текущим авторизованным пользователем."""
    # Ищем в базе все места, где id_polzovatelya совпадает с id текущего юзера
    mesta = baza.query(Mesto).filter(Mesto.id_polzovatelya == tekushiy_polzovatel.id).all()
    return mesta

# ==========================================
# 2. Добавить новое место
# ==========================================
@router.post("/", response_model=MestoOtvet, status_code=status.HTTP_201_CREATED)
def dobavit_mesto(
    dannie_mesta: MestoSozdanie,
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """Добавляет новое место в личный каталог."""
    
    # Создаем объект места из присланных данных
    novoe_mesto = Mesto(
        nazvanie=dannie_mesta.nazvanie,
        kategoriya=dannie_mesta.kategoriya,
        adres=dannie_mesta.adres,
        shirota=dannie_mesta.shirota,
        dolgota=dannie_mesta.dolgota,
        reiting=dannie_mesta.reiting,
        cena=dannie_mesta.cena,
        zametki=dannie_mesta.zametki,
        id_polzovatelya=tekushiy_polzovatel.id # Привязываем место к текущему юзеру!
    )
    
    # Сохраняем в базу
    baza.add(novoe_mesto)
    baza.commit()
    baza.refresh(novoe_mesto)
    
    return novoe_mesto

# ==========================================
# 3. Удалить место
# ==========================================
@router.delete("/{id_mesta}", status_code=status.HTTP_204_NO_CONTENT)
def udalit_mesto(
    id_mesta: int,
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """Удаляет место по его ID. Удалить можно только СВОЁ место."""
    # Ищем место, где id совпадает с запрашиваемым И владелец - текущий юзер
    mesto = baza.query(Mesto).filter(
        Mesto.id == id_mesta,
        Mesto.id_polzovatelya == tekushiy_polzovatel.id
    ).first()
    
    if not mesto:
        raise HTTPException(status_code=404, detail="Место не найдено или это не ваше место")
        
    # Удаляем и сохраняем изменения
    baza.delete(mesto)
    baza.commit()
    return None
