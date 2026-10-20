"""Бот без внешних библиотек: работает на любой версии Python 3.8+ (включая 3.15)."""
import json
import os
import time
import urllib.request

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER")
GAME_URL = os.getenv("GAME_URL", "https://ТВОЙ_САЙТ")  # обязательно https

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"


def call(method, **params):
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        API + method, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.loads(r.read().decode("utf-8"))


def top10_text():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return "Таблица лидеров ещё не настроена."
    req = urllib.request.Request(
        SUPABASE_URL + "/rest/v1/scores?select=name,score&order=score.desc&limit=10",
        headers={"apikey": SUPABASE_KEY, **({"Authorization": "Bearer " + SUPABASE_KEY} if SUPABASE_KEY.startswith("eyJ") else {})},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = json.loads(r.read().decode("utf-8"))
    if not rows:
        return "Пока никого нет. Стань первым!"
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{medals[i] if i < 3 else str(i + 1) + '.'} {x['name']} — {x['score']}" for i, x in enumerate(rows)]
    return "🏆 Топ 10 игроков:\n" + "\n".join(lines)


def main():
    # Кнопка «Играть» рядом с полем ввода
    call(
        "setChatMenuButton",
        menu_button={"type": "web_app", "text": "Играть", "web_app": {"url": GAME_URL}},
    )
    print("Бот запущен. Остановить: Ctrl+C")

    offset = 0
    while True:
        try:
            updates = call("getUpdates", offset=offset, timeout=30)["result"]
        except Exception as e:
            print("Ошибка связи:", e)
            time.sleep(3)
            continue

        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message")
            if not msg:
                continue
            try:
                handle(msg)
            except Exception as e:
                # Одна неудачная отправка (например, 403 — пользователь заблокировал бота)
                # больше не останавливает бота
                print("Не удалось ответить в чат", msg["chat"]["id"], "-", e)


def handle(msg):
    text = msg.get("text", "")
    chat_id = msg["chat"]["id"]
    if text.startswith("/top"):
        try:
            answer = top10_text()
        except Exception as e:
            answer = "Не удалось получить топ."
            print("Ошибка топа:", e)
        call("sendMessage", chat_id=chat_id, text=answer)
    elif text.startswith("/start"):
        call(
            "sendMessage",
            chat_id=chat_id,
            text="Выбери игру: башня из блоков или майнинг. "
                 "Жми кнопку ниже!",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "🎮 Играть", "web_app": {"url": GAME_URL}}],
                ]
            },
        )
        print("Ответил на /start в чате", chat_id)


if __name__ == "__main__":
    main()
