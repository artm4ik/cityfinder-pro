from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from baza import poluchit_bazu
from modeli import Polzovatel, Mesto
from bezopasnost import poluchit_tekushego_polzovatelya

router = APIRouter(prefix="/stats", tags=["Статистика и Pro"])

# ==========================================
# 1. Получение статистики
# ==========================================
@router.get("/")
def poluchit_statistiku(
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """
    Возвращает статистику пользователя: 
    - общее количество мест
    - средний рейтинг
    - распределение по категориям (только для Pro)
    """
    
    # 1. Считаем общее количество мест пользователя
    vsego_mest = baza.query(Mesto).filter(Mesto.id_polzovatelya == tekushiy_polzovatel.id).count()
    
    # 2. Высчитываем средний рейтинг всех мест пользователя
    sredniy_reiting = baza.query(func.avg(Mesto.reiting)).filter(
        Mesto.id_polzovatelya == tekushiy_polzovatel.id
    ).scalar()
    
    # Если мест нет, рейтинг будет None, поэтому ставим 0.0. Иначе округляем до 1 знака.
    sredniy_reiting = round(sredniy_reiting, 1) if sredniy_reiting else 0.0

    # Базовый ответ для бесплатной версии
    otvet = {
        "vsego_mest": vsego_mest,
        "sredniy_reiting": sredniy_reiting,
        "pro_versiya_aktivna": tekushiy_polzovatel.est_pro_versiya
    }

    # 3. Если у пользователя куплена Pro-версия, даем расширенную аналитику
    if tekushiy_polzovatel.est_pro_versiya:
        # Группируем места по категориям и считаем их количество
        kategorii = baza.query(Mesto.kategoriya, func.count(Mesto.id)).filter(
            Mesto.id_polzovatelya == tekushiy_polzovatel.id
        ).group_by(Mesto.kategoriya).all()
        
        # Превращаем результат [('еда', 2), ('отдых', 1)] в словарь {'еда': 2, 'отдых': 1}
        raspredelenie = {kat: kolichestvo for kat, kolichestvo in kategorii}
        
        otvet["raspredelenie_po_kategoriyam"] = raspredelenie
        otvet["rekomendaciya"] = "У вас отличный вкус! Попробуйте добавить больше новых категорий."
    else:
        # Если версия бесплатная, скрываем эту статистику
        otvet["raspredelenie_po_kategoriyam"] = "Доступно только в Pro-версии"

    return otvet

# ==========================================
# 2. Имитация покупки Pro-версии
# ==========================================
@router.post("/upgrade")
def kupit_pro_versiyu(
    baza: Session = Depends(poluchit_bazu),
    tekushiy_polzovatel: Polzovatel = Depends(poluchit_tekushego_polzovatelya)
):
    """
    Меняет статус пользователя на Pro.
    В реальном проекте здесь была бы интеграция с Яндекс.Кассой или Stripe.
    """
    if tekushiy_polzovatel.est_pro_versiya:
        return {"soobshchenie": "У вас уже активирована Pro-версия!"}
        
    tekushiy_polzovatel.est_pro_versiya = True
    baza.commit()
    
    return {"soobshchenie": "Поздравляем! Pro-версия успешно активирована."}