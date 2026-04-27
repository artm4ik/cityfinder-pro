// 1. Проверка авторизации
const token = localStorage.getItem("token");
if (!token) {
    // Если токена нет, выбрасываем пользователя на страницу входа
    window.location.href = "/frontend/index.html";
}

// Общие заголовки для запросов, чтобы не писать каждый раз
const zagolovkiAuth = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
};

// 2. Выход из аккаунта
document.getElementById("knopka-vyhoda").addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/frontend/index.html";
});

// Глобальные переменные
let karta, markerVybora;

// 3. Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", async () => {
    await zagruzitProfil();
    await zagruzitStatistiku();
    
    // Ждем загрузки API Яндекс.Карт, затем инициализируем карту и места
    ymaps.ready(async () => {
        initsializirovatKartu();
        await zagruzitMesta();
    });
});

// ==========================================
// Логика работы с профилем и статистикой
// ==========================================
async function zagruzitProfil() {
    try {
        const otvet = await fetch("/auth/me", { headers: zagolovkiAuth });
        if (otvet.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/frontend/index.html";
        }
        
        const profil = await otvet.json();
        document.getElementById("imya-polzovatelya").textContent = profil.email;
        
        // Показываем значок PRO и кнопку экспорта, если версия куплена
        if (profil.est_pro_versiya) {
            document.getElementById("znak-pro").style.display = "inline-block";
            document.getElementById("blok-pokupki-pro").style.display = "none";
            document.getElementById("knopka-eksporta").style.display = "inline-block";
        }
    } catch (e) {
        console.error("Ошибка загрузки профиля", e);
    }
}

async function zagruzitStatistiku() {
    try {
        const otvet = await fetch("/stats/", { headers: zagolovkiAuth });
        const statistika = await otvet.json();
        
        const blok = document.getElementById("blok-statistiki");
        
        let html = `
            <p class="mb-1"><strong>Всего мест:</strong> ${statistika.vsego_mest}</p>
            <p class="mb-1"><strong>Средний рейтинг:</strong> ${statistika.sredniy_reiting} ⭐️</p>
        `;
        
        if (statistika.pro_versiya_aktivna) {
            html += `<hr><p class="mb-1"><strong>Распределение:</strong></p><ul>`;
            for (const [kategoriya, kolichestvo] of Object.entries(statistika.raspredelenie_po_kategoriyam)) {
                html += `<li>${kategoriya}: ${kolichestvo}</li>`;
            }
            html += `</ul><p class="text-muted small mt-2"><i>${statistika.rekomendaciya}</i></p>`;
        }
        
        blok.innerHTML = html;
        
    } catch (e) {
        console.error("Ошибка загрузки статистики", e);
    }
}

// Кнопка покупки Pro
document.getElementById("knopka-kupit-pro").addEventListener("click", async () => {
    if(confirm("Активировать Pro-версию? (Тестовая покупка)")) {
        const otvet = await fetch("/stats/upgrade", { method: "POST", headers: zagolovkiAuth });
        if (otvet.ok) {
            alert("Pro-версия активирована!");
            location.reload(); // Перезагружаем страницу, чтобы обновить статистику и профиль
        }
    }
});

// Кнопка скачивания CSV
document.getElementById("knopka-eksporta").addEventListener("click", async () => {
    try {
        const otvet = await fetch("/export/csv", { headers: zagolovkiAuth });
        
        if (!otvet.ok) {
            alert("Ошибка при выгрузке. Доступно только в Pro.");
            return;
        }
        
        // Магия для скачивания файла через браузер
        const text_csv = await otvet.text();
        const bl = new Blob(["\ufeff", text_csv], { type: 'text/csv;charset=utf-8;' }); // \ufeff нужен чтобы Excel правильно читал русский язык (BOM)
        const url = window.URL.createObjectURL(bl);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Moi_Mesta_CityFinder.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        
    } catch (e) {
        console.error("Ошибка при скачивании CSV", e);
        alert("Не удалось скачать файл.");
    }
});


// ==========================================
// Логика работы с Яндекс Картами
// ==========================================
function initsializirovatKartu() {
    // Создаем карту. Координаты центра: Москва.
    karta = new ymaps.Map('karta', {
        center: [55.751244, 37.618423],
        zoom: 11,
        controls: ['zoomControl', 'fullscreenControl']
    });

    // Слушатель клика по карте (чтобы ставить маркер для нового места)
    karta.events.add('click', function(e) {
        const coords = e.get('coords');
        
        // Если маркер уже есть, перемещаем его, иначе создаем
        if (markerVybora) {
            markerVybora.geometry.setCoordinates(coords);
        } else {
            markerVybora = new ymaps.Placemark(coords, {}, {
                preset: 'islands#redIcon'
            });
            karta.geoObjects.add(markerVybora);
        }
        
        // Записываем координаты в скрытые поля формы
        document.getElementById('mesto-shirota').value = coords[0];
        document.getElementById('mesto-dolgota').value = coords[1];
    });
}

// ==========================================
// Логика работы с Местами
// ==========================================
async function zagruzitMesta() {
    try {
        const otvet = await fetch("/places/", { headers: zagolovkiAuth });
        const mesta = await otvet.json();
        
        const spisok = document.getElementById("spisok-mest");
        spisok.innerHTML = ""; // Очищаем старые места
        
        if (mesta.length === 0) {
            spisok.innerHTML = `<div class="col-12 text-center text-muted mt-3"><p>Вы пока не добавили ни одного места. Кликните по карте и заполните форму справа!</p></div>`;
            return;
        }

        mesta.forEach(mesto => {
            // Рисуем карточку места
            const fotoUrl = mesto.put_k_foto ? mesto.put_k_foto : "https://via.placeholder.com/300x150?text=Нет+фото";
            
            const htmlKartochki = `
                <div class="col-md-6">
                    <div class="card shadow-sm border-0 kartochka-mesta h-100">
                        <img src="${fotoUrl}" class="card-img-top foto-mesta" alt="Фото">
                        <div class="card-body p-3">
                            <h6 class="card-title fw-bold mb-1">${mesto.nazvanie}</h6>
                            <p class="card-text text-muted small mb-1">📍 ${mesto.adres}</p>
                            <div class="d-flex justify-content-between mb-2">
                                <span class="badge bg-primary">${mesto.kategoriya}</span>
                                <span class="badge bg-secondary">💰 ${mesto.cena}</span>
                                <span class="badge bg-warning text-dark">⭐️ ${mesto.reiting}/5</span>
                            </div>
                            <p class="card-text small mb-2">${mesto.zametki || ""}</p>
                            <button onclick="udalitMesto(${mesto.id})" class="btn btn-outline-danger btn-sm w-100">Удалить</button>
                        </div>
                    </div>
                </div>
            `;
            spisok.innerHTML += htmlKartochki;

            // Ставим маркер этого места на Яндекс Карту
            if (mesto.shirota && mesto.dolgota) {
                const placemark = new ymaps.Placemark([mesto.shirota, mesto.dolgota], {
                    balloonContentHeader: `<b>${mesto.nazvanie}</b>`,
                    balloonContentBody: `${mesto.kategoriya}`
                }, {
                    preset: 'islands#blueIcon'
                });
                karta.geoObjects.add(placemark);
            }
        });
    } catch (e) {
        console.error("Ошибка загрузки мест", e);
    }
}

// Форма добавления нового места
document.getElementById("forma-dobavleniya-mesta").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const shirota = document.getElementById("mesto-shirota").value;
    const dolgota = document.getElementById("mesto-dolgota").value;
    
    // Если пользователь не кликнул по карте
    if (!shirota || !dolgota) {
        alert("Пожалуйста, кликните по карте, чтобы указать место!");
        return;
    }

    const dannieMesta = {
        nazvanie: document.getElementById("mesto-nazvanie").value,
        kategoriya: document.getElementById("mesto-kategoriya").value,
        adres: document.getElementById("mesto-adres").value,
        shirota: parseFloat(shirota),
        dolgota: parseFloat(dolgota),
        reiting: parseInt(document.getElementById("mesto-reiting").value),
        cena: document.getElementById("mesto-cena").value,
        zametki: document.getElementById("mesto-zametki").value
    };

    try {
        // Шаг 1: Создаем место (отправляем JSON)
        const otvetMesta = await fetch("/places/", {
            method: "POST",
            headers: zagolovkiAuth,
            body: JSON.stringify(dannieMesta)
        });
        
        if (!otvetMesta.ok) {
            alert("Ошибка при создании места"); return;
        }
        const novoeMesto = await otvetMesta.json();

        // Шаг 2: Загружаем фото (если пользователь его выбрал)
        const poleFoto = document.getElementById("mesto-foto");
        if (poleFoto.files.length > 0) {
            const formData = new FormData();
            formData.append("foto", poleFoto.files[0]);

            await fetch(`/places/${novoeMesto.id}/photo`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }, // Тут Content-Type не ставим, браузер сам добавит multipart/form-data
                body: formData
            });
        }

        alert("Место успешно добавлено!");
        location.reload(); // Перезагружаем, чтобы обновить всё (список, карту, стату)
        
    } catch (e) {
        console.error("Ошибка сохранения", e);
    }
});

// Удаление места
async function udalitMesto(id_mesta) {
    if (confirm("Точно удалить это место?")) {
        try {
            const otvet = await fetch(`/places/${id_mesta}`, {
                method: "DELETE",
                headers: zagolovkiAuth
            });
            if (otvet.ok) {
                location.reload();
            } else {
                alert("Ошибка удаления");
            }
        } catch (e) {
            console.error(e);
        }
    }
}
