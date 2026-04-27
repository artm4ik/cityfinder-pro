// Функция для обработки Входа (Login)
const formaVkhoda = document.getElementById("forma-vkhoda");
if (formaVkhoda) {
    formaVkhoda.addEventListener("submit", async function(sobytie) {
        // Отменяем стандартное поведение формы (перезагрузку страницы)
        sobytie.preventDefault();
        
        const email = document.getElementById("vkhod-email").value;
        const parol = document.getElementById("vkhod-parol").value;
        const oshibka = document.getElementById("vkhod-oshibka");

        try {
            // Формируем данные в формате URL-encoded (так требует стандарт OAuth2)
            const dannie = new URLSearchParams();
            dannie.append('username', email); // FastAPI ожидает именно username, а не email
            dannie.append('password', parol);

            // Отправляем запрос на сервер
            const otvet = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: dannie
            });

            const rezultat = await otvet.json();

            if (otvet.ok) {
                // Если всё успешно, сохраняем токен в память браузера (localStorage)
                localStorage.setItem("token", rezultat.access_token);
                // И перенаправляем на страницу дашборда (которую мы скоро создадим)
                window.location.href = "/frontend/dashboard.html";
            } else {
                // Показываем ошибку (например, "Неверный пароль")
                oshibka.textContent = rezultat.detail;
                oshibka.style.display = "block";
            }
        } catch (e) {
            oshibka.textContent = "Ошибка соединения с сервером";
            oshibka.style.display = "block";
        }
    });
}

// Функция для обработки Регистрации
const formaRegistracii = document.getElementById("forma-registracii");
if (formaRegistracii) {
    formaRegistracii.addEventListener("submit", async function(sobytie) {
        sobytie.preventDefault();
        
        const email = document.getElementById("reg-email").value;
        const parol = document.getElementById("reg-parol").value;
        const gorod = document.getElementById("reg-gorod").value;
        const oshibka = document.getElementById("reg-oshibka");

        try {
            // Отправляем данные в формате JSON (так ожидает наш Pydantic)
            const otvet = await fetch("/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email: email, parol: parol, gorod: gorod })
            });

            const rezultat = await otvet.json();

            if (otvet.ok) {
                // После успешной регистрации, сразу автоматически логинимся (чтобы получить токен)
                const dannieVkhoda = new URLSearchParams();
                dannieVkhoda.append('username', email);
                dannieVkhoda.append('password', parol);
                
                const otvetVkhoda = await fetch("/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: dannieVkhoda
                });
                
                const rezultatVkhoda = await otvetVkhoda.json();
                if (otvetVkhoda.ok) {
                    localStorage.setItem("token", rezultatVkhoda.access_token);
                    window.location.href = "/frontend/dashboard.html";
                }
            } else {
                oshibka.textContent = rezultat.detail || "Ошибка регистрации";
                oshibka.style.display = "block";
            }
        } catch (e) {
            oshibka.textContent = "Ошибка соединения с сервером";
            oshibka.style.display = "block";
        }
    });
}
