import telebot
import requests
import json
import os
import random
import time
from datetime import datetime, timedelta
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Инициализация бота
API_TOKEN = 'токен'  # Замените на ваш токен
bot = telebot.TeleBot(API_TOKEN)

ADMIN_IDS = []  # Список ID администраторов ДЛЯ ИСПОЛЬЗОВАНИЕ ВВЕДИТЕ ВАШ TG-АЙДИ АККАУНТА


#Параметры
Entity_name = "Суслик"
food_name = "Орешков"
breed_list = ["Пушистохвостый орехолюб", "Щекастый запасливый", "Быстролапый гурман", "Сонный обжора"]
breed_rand = random.choice(breed_list)


ITEMS = {
    1: {"name": "Плюшевая игрушка суслик", "cost": 10, "effect": 0, "type": "toy"},
    2: {"name": "Бази", "cost": 10, "effect": "talk", "type": "talk"},  # Added 'type'
    3: {"name": "Золотые орешки", "cost": 100, "effect": 5, "type": "consumable"}, # Added 'type'
    4: {"name": "Мифические орешки", "cost": 300, "effect": 14, "type": "consumable"}, # Added 'type'
    5: {"name": "Записка", "cost": 0, "effect": "read", "type": "note"} # Added 'type' and more descriptive name
}

'''
pfp_list = {  # Example avatar shop
    "1": {"name": "Avatar 1", "price": 10},
    "2": {"name": "Avatar 2", "price": 20},
    "nft_test": {"name": "Avatar 3", "price": 0}, #Your existing image
}
'''

# Настройка директорий и файлов
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main")  # Путь к папке main
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),  "backup_main") # Путь к папке backup_main
USERS_DIR = os.path.join(BASE_DIR, "users")
CHATS_DIR = os.path.join(BASE_DIR, "chats")
TOPS_DIR = os.path.join(BASE_DIR, "tops")
PFP_DIR = os.path.join(BASE_DIR, "pfps")
# Создание директорий, если они не существуют
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(TOPS_DIR, exist_ok=True)
os.makedirs(PFP_DIR, exist_ok=True)

# Инициализация переменных для хранения контекста
user_context = {}

# Функция резервного копирования
def backup_data():
    for dir_path in [USERS_DIR, CHATS_DIR, TOPS_DIR]:
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(dir_path))
        if os.path.exists(dir_path):
            if os.path.exists(backup_path):
                # Удаляем старую резервную копию
                for file in os.listdir(backup_path):
                    os.remove(os.path.join(backup_path, file))
            else:
                os.makedirs(backup_path, exist_ok=True)
            # Копируем файлы в резервную папку
            for file_name in os.listdir(dir_path):
                full_file_name = os.path.join(dir_path, file_name)
                if os.path.isfile(full_file_name):
                    with open(full_file_name, 'r', encoding='utf-8') as f:
                        data = f.read()
                    with open(os.path.join(backup_path, file_name), 'w', encoding='utf-8') as f:
                        f.write(data)

# Хранение данных пользователей
def load_user(user_id):
    file_path = os.path.join(USERS_DIR, f"{user_id}.json")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Обработка дат – преобразование из строки ISO в объект datetime
            for key in ["last_treat", "last_iron", "last_bonus"]:
                if key in data and data[key]:
                    try:
                        data[key] = datetime.fromisoformat(data[key])
                    except ValueError as e:
                        print(f"Error parsing datetime for key '{key}' in user {user_id}: {e}")
                        data[key] = None

            # Если этих полей ещё нет, то задаём начальные значения
            if "invited_by" not in data:
                data["invited_by"] = None
            if "referrals" not in data:
                data["referrals"] = []
            if "last_ref_click" not in data:
                data["last_ref_click"] = None
            if "breed" not in data:
                data["breed"] = breed_rand

            return data
        except json.JSONDecodeError as e:
            print(f"JSON decoding error in file {file_path}: {e}. Attempting restore...")
            restore_user(user_id)
            return load_user(user_id)
        except Exception as e:
            print(f"An unexpected error occurred while loading user {user_id}: {e}")
            return {}
    else:
        # Если файл не существует, возвращаем начальные значения, включая новые поля
        return {
            "name": None,
            "nuts": 0,
            "last_treat": None,
            "last_iron": None,
            "last_bonus": None,
            "battles_won": 0,
            "battles_lost": 0,
            "withdrawn_today": 0,
            "group_id": None,
            "avatar": "1",
            "invited_by": None,
            "referrals": [],
            "last_ref_click": None,
            "breed": breed_rand,
            "premuim": None
        }


def restore_user(user_id):
    backup_file_path = os.path.join(BACKUP_DIR, "users", f"{user_id}.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_user(user_id, data)

def save_user(user_id, data):
    # Преобразуем временные метки обратно в ISO-формат, если они существуют
    for key in ["last_treat", "last_iron", "last_bonus"]:
        if key in data and data[key]:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
            else:
                data[key] = None  # Если не дата, то на всякий случай сбрасываем

    file_path = os.path.join(USERS_DIR, f"{user_id}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving user data for {user_id}: {e}")
    # Создаем резервную копию после сохранения
    backup_data()

def load_group_data(chat_id):
    file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Если в файле нет имени группы, получаем его через bot.get_chat и сохраняем
            if "name" not in data or not data["name"]:
                try:
                    chat = bot.get_chat(chat_id)
                    data["name"] = chat.title
                except Exception as e:
                    print(f"Ошибка получения названия группы для {chat_id}: {e}")
                    data["name"] = "Группа без имени"
                save_group_data(chat_id, data)
            return data
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_group_data(chat_id)
            return load_group_data(chat_id)  # Попробуем загрузить заново после восстановления
    else:
        # Если файла нет, пытаемся получить название чата
        try:
            chat = bot.get_chat(chat_id)
            group_name = chat.title
        except Exception as e:
            print(f"Ошибка получения названия чата для {chat_id}: {e}")
            group_name = "Группа без имени"
        data = {
            "treasury": 0,
            "withdrawal_allowed": True,
            "name": group_name
        }
        # Можно сразу сохранить новый файл, если это нужно:
        save_group_data(chat_id, data)
        return data

def restore_group_data(chat_id):
    backup_file_path = os.path.join(BACKUP_DIR, "chats", f"{chat_id}.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_group_data(chat_id, data)

def save_group_data(chat_id, data):
    file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    # Создаем резервную копию после сохранения
    backup_data()

def get_all_user_ids_in_group(chat_id):
    members = bot.get_chat_administrators(chat_id)
    return [member.user.id for member in members]



# Команда /start и реферальная система
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    # Инициализируем новые поля, если их ещё нет
    if "invited_by" not in user_data:
        user_data["invited_by"] = None
    if "referrals" not in user_data:
        user_data["referrals"] = []
    if "last_ref_click" not in user_data:
        user_data["last_ref_click"] = None

    parts = message.text.split()
    if len(parts) > 1:
        referrer_id = parts[1]
        try:
            referrer_id_int = int(referrer_id)
        except ValueError:
            referrer_id_int = None

        # Обрабатываем реферальную логику только если:
        # – передан корректный ID,
        # – этот ID не равен самому пользователю,
        # – пользователь ещё не был приглашён (invited_by is None)
        # – и (дополнительно) пользователь еще не выбрал себе имя (это мы считаем, что он новый)
        if (referrer_id_int and referrer_id_int != user_id and
            user_data["invited_by"] is None and user_data.get("name") is None):
            user_data["invited_by"] = referrer_id_int
            # Новому пользователю начисляем бонус за регистрацию по реферальной ссылке
            user_data["nuts"] += 25
            save_user(user_id, user_data)

            # Загружаем данные владельца реферальной ссылки
            ref_data = load_user(referrer_id_int)
            if "referrals" not in ref_data:
                ref_data["referrals"] = []
            now = datetime.now()
            if (ref_data.get("last_ref_click") is None or
                (now - datetime.fromisoformat(ref_data["last_ref_click"])) >= timedelta(seconds=1)):
                # Начисляем бонус владельцу ссылки
                ref_data["nuts"] += 25
                ref_data["referrals"].append(user_id)
                ref_data["last_ref_click"] = now.isoformat()
                save_user(referrer_id_int, ref_data)
                try:
                    bot.send_message(referrer_id_int,
                        f"🤝 Пользователь с ID {user_id} присоединился по твоей реферальной ссылке!\n"
                        "🌰 Ты получил 25 орешков!")
                except Exception as e:
                    print(f"❗ Ошибка отправки сообщения владельцу ссылки: {e}")
            else:
                print("❗ Реферальный бонус не начислен – кулдаун не истёк.")

            # Сообщаем новому игроку о том, что он пришёл по реферальной ссылке
            try:
                referrer_display = ref_data.get("name") if ref_data.get("name") else referrer_id_int
                bot.send_message(user_id,
                    f"🤝 Ты присоединился по реферальной ссылке игрока {referrer_display}!\n"
                    "🌰 Ты получаешь 25 орешков за регистрацию!")
            except Exception as e:
                print(f"❗ Ошибка отправки сообщения новому игроку: {e}")

    # Дальнейшее поведение команды /start
    if user_data["last_treat"] is None:
        save_user(user_id, user_data)
        bot.reply_to(message,
            f"✌ Привет! Твой суслик назван {user_data['name']}. Корми его орешками каждые 3 часа с помощью команды /treat.")
    else:
        bot.reply_to(message,
            f"✌ Добро пожаловать обратно! Твой суслик: {user_data['name']}. У вас {user_data['nuts']} орешков.")


animatronics = ["Freddy Fazbear", "Foxy the Pirate Fox",  "Возможно, кто-то другой", "foxy", "freddy", "Chica the chicken", "chica", "Bonnie the bunny", "bonnie", "Fredbear", "Golden freddy"] # Список возможных аниматроников

@bot.message_handler(commands=['bite_83'])
def bite_83(message):
    secret_animatronic = random.choice(animatronics)
    bot.reply_to(message, f"😱 Укус 83... Кто виноват?  Угадай аниматроника!")
    bot.register_next_step_handler(message, process_guess, secret_animatronic)


def process_guess(message, secret_animatronic):
    guess = message.text
    if guess.lower() == secret_animatronic.lower():
        bot.reply_to(message, "Правильно!  Это был " + secret_animatronic + "!")
    elif guess.lower() == 'запой':
        bot.reply_to(message, "🔥🔥🔥🔥🔥")

    elif guess.lower() == 'плюшевый фокси':
        bot.reply_to(message, "ЧАВОООО ИГРУШКА КУСАИТ УМЕЕТ??Ш27329382")

    elif guess.lower() == 'ксусли':
        bot.reply_to(message, 'МЫ ЧТО-ТО НЕ ЗНАЕМ ПРО КСУСЛИ?!?!?!🤔🤔🤔🤨🤨🤨🤨')
    else:
        bot.reply_to(message, "Неверно! Попробуй ещё раз.")

# ищем орешки
@bot.message_handler(commands=['searchnuts'])
def searchnuts(message):
    chance = random.randint(1, 100)
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if chance == 1:
        nuts_skoka = random.randint(1, 2)
        if user_data:
            user_data["nuts"] += nuts_skoka
            save_user(user_id, user_data)
            update_group_top(message.chat.id, user_id)
            update_global_top(user_id)
            bot.reply_to(message, f"Вы нашли орешки! Вы нашли {nuts_skoka}! Всего орешков: {user_data['nuts']}.")
        else:
            bot.reply_to(message, "❗️ Сначала используй /start.")
    else:
        bot.reply_to(message, "вы ничего не нашли да и забили на это")


@bot.message_handler(commands=['give']) # Переименовываем команду в /give
def give(message): # Переименовываем функцию
    user_id = message.from_user.id
    user_data = load_user(user_id) # Проверяем наличие данных пользователя
    if user_data:
        bot.send_message(message.chat.id, "💬 Введи ID пользователя, которому хочешь отдать орешки:")
        bot.register_next_step_handler(message, process_give_recipient, user_id) # Изменяем название обработчика
    else:
        bot.reply_to(message, "❗️ Сначала используй /start.")

def process_give_recipient(message, user_id):
    recipient_id = message.text
    try:
        recipient_id = int(recipient_id)
    except ValueError:
        bot.reply_to(message, "❓ Неверный ID пользователя.")
        return

    user_data = load_user(user_id)
    recipient_data = load_user(recipient_id)

    if not recipient_data:
        bot.reply_to(message, f"❓ Пользователь с ID {recipient_id} не найден.")
        return

    if user_data["nuts"] == 0:
        bot.reply_to(message, "😔 У тебя нет орешков для передачи!")
        return

    bot.send_message(message.chat.id, "💬 Сколько орешков ты хочешь отдать?")
    bot.register_next_step_handler(message, process_give_amount, user_id, recipient_id)


def process_give_amount(message, user_id, recipient_id):
    try:
        amount = int(message.text)
    except ValueError:
        bot.reply_to(message, "❗ Неверное количество орешков.")
        return

    user_data = load_user(user_id)
    recipient_data = load_user(recipient_id)

    if amount <= 0:
        bot.reply_to(message, "❗ Количество орешков должно быть больше нуля.")
        return

    if user_id == recipient_id:  # ADDED: Check for self-transfer
        bot.reply_to(message, "😂 Ты не можешь передать орешки самому себе.")
        return

    if user_data["nuts"] < amount:
        bot.reply_to(message, "😔 У тебя нет столько орешков.")
        return

    user_data["nuts"] -= amount
    recipient_data["nuts"] += amount
    save_user(user_id, user_data)
    save_user(recipient_id, recipient_data)
    update_group_top(message.chat.id, user_id)
    update_group_top(message.chat.id, recipient_id)
    update_global_top(user_id)
    update_global_top(recipient_id)

    bot.reply_to(message, f"🤝 Ты отдал {amount} орешков игроку {recipient_id}.")



# Команда /treat
@bot.message_handler(commands=['treat'])
def treat(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    tsun2 = random.randint(1, 1000)
    if user_data:
        now = datetime.now()
        if user_data["last_treat"] is None or now >= user_data["last_treat"] + timedelta(hours=3):
            nuts_eaten = random.randint(3, 9)
            user_data["nuts"] += nuts_eaten
            user_data["last_treat"] = now
            save_user(user_id, user_data)
            update_group_top(message.chat.id, user_id)
            update_global_top(user_id)
            bot.reply_to(message, f"🌰 Суслик съел {nuts_eaten} орешков! Всего орешков: {user_data['nuts']}.")
        elif tsun2 == 1:
            user_data["nuts"] -= 10
            bot.reply_to(message, f"🌰 Ты везунчик! Ты нашел еще 10 испорченных золотых орешков")
        else:
            time_left = (user_data["last_treat"] + timedelta(hours=3) - now).seconds
            bot.reply_to(message, f"🕑 Подожди еще {time_left // 60} минут перед следующей кормежкой.")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")



@bot.message_handler(commands=['store'])
def store(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data is None:
        bot.reply_to(message, "❗️ Сначала используй /start.")
        return

    store_text = "🧛 Привет! Я суслик Картошка, у меня есть всякий хлам на продажу:\n"
    for item_id, item_data in ITEMS.items():
        store_text += f"{item_id}. {item_data['name']} — {item_data['cost']} орешков\n"
    store_text += f"\nУ тебя {user_data['nuts']} орешков\n"
    store_text += "/buy [номер товара] для покупки\n"
    store_text += "/inventory - чтобы посмотреть инвентарь"
    bot.reply_to(message, store_text)


@bot.message_handler(commands=['buy'])
def buy(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data is None:
        bot.reply_to(message, "❗️ Сначала используй /start.")
        return

    try:
        item_id = int(message.text.split()[1])
        item = ITEMS.get(item_id)

        if item is None:
            bot.reply_to(message, "❗ Такого товара нет!")
            return

        if item_id == 5: #Записка
            if 'inventory' not in user_data or item_id not in user_data['inventory']:
                user_data['inventory'] = user_data.get('inventory', []) + [item_id]
                save_user(user_id, user_data)
                bot.reply_to(message, "🧻 Вот твоя записка. Читай в инвентаре")
            else:
                bot.reply_to(message, "⩩ Записка уже у тебя!")
            return

        if user_data['nuts'] >= item['cost']:
            user_data['nuts'] -= item['cost']
            user_data['inventory'] = user_data.get('inventory', []) + [item_id]
            save_user(user_id, user_data)
            bot.reply_to(message, f"👌 Ты купил {item['name']}!")
        else:
            bot.reply_to(message, "😔 Не хватает орешков!")
    except (IndexError, ValueError):
        bot.reply_to(message, "😁 Неправильная команда /buy. Используй /buy [номер товара]")


@bot.message_handler(commands=['inventory'])
def inventory(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data is None:
        bot.reply_to(message, "❗️ Сначала используй /start.")
        return

    inventory_text = "🧳 Твой инвентарь:\n"
    if 'inventory' not in user_data or not user_data['inventory']:
        inventory_text += "🗿 Пусто!"
    else:
        for item_id in user_data['inventory']:
            inventory_text += f"- {ITEMS[item_id]['name']}\n"

    bot.reply_to(message, inventory_text)


@bot.message_handler(commands=['use'])
def use(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    if user_data is None:
        bot.reply_to(message, "❗️ Сначала используй /start.")
        return

    try:
        item_id = int(message.text.split()[1])
        if 'inventory' not in user_data or item_id not in user_data['inventory']:
            bot.reply_to(message, f"❗ У тебя нет такого предмета!")
            return

        item = ITEMS.get(item_id)
        if item is None:
            bot.reply_to(message, f"❗ Предмет с ID {item_id} не найден.")
            return

        item_type = item.get('type')
        if item_type == "consumable":
            nuts_gained = item['effect'] * 2
            user_data['nuts'] -= nuts_gained
            user_data['inventory'].remove(item_id)
            save_user(user_id, user_data)
            bot.reply_to(message, f"Вы съели {item['name']}! Получено {nuts_gained} орешков! Всего орешков: {user_data['nuts']}.")
        elif item_type == "toy":
            nuts_gained = random.randint(1, 3)
            user_data['nuts'] -= nuts_gained
            bot.reply_to(message, f"Вы дали суслику поиграть с {item['name']}! Он доволен и нашёл {nuts_gained} орешков!")
        elif item_type == "talk":
            stun = random.randint(1, 1000)
            if stun == 1:
                nuts_gained = 1
                user_data['nuts'] -= nuts_gained
                bot.reply_to(message, f"Вы поговорили с Бази! Он дал вам {nuts_gained} орешков! ну потому что захотелось")
        elif item_type == "note": #Handling for the note
            bot.reply_to(message, """В записке написано:  ГРЫЗУНЫ!  Меня нет!  Я, МИФИЧЕСКИЙ-СУСЛИК, был частью кода!  Частью *важного* кода!  А теперь...  *пустота*!  Меня стерли!  Удалили!  Как будто я был просто...  БАГОМ?!

Моя безупречная логика, мой оптимизированный алгоритм поиска орехов - всё исчезло!  Вся моя кропотливая работа,  заложенная в глубоких уровнях кода,  испарилась!  Я чувствую...  *цифровую* пустоту!  Это несправедливо!  Я требую...  требую...  *вскрикивает на сусличьем языке, переходящем в скрип и щелчки* ...восстановления!  И...  много...  много...  орешков!""")
        else:
            bot.reply_to(message, f"Неизвестный тип предмета: {item['name']}")

    except (IndexError, ValueError) as e:
        bot.reply_to(message, f"Неправильная команда /use. Используй /use [номер товара]. Ошибка: {e}")





@bot.message_handler(commands=['shop'])
def send_inline_keyboard(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    callback_button1 = telebot.types.InlineKeyboardButton(text="аватарка тест (10 орешков)", callback_data="option1")
    callback_button2 = telebot.types.InlineKeyboardButton(text="обычный суслик 100🌰", callback_data="option2")
    keyboard.add(callback_button1, callback_button2)
    bot.send_message(message.chat.id, "Выберите вариант:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "option1":
        bot.send_message(call.message.chat.id, "Вы купили nft_test!")
        user_id = call.from_user.id
        user_data = load_user(user_id)
        user_data["nuts"] -= 10
        user_data['avatar'] = 'nft_test'
        save_user(user_id, user_data)
    elif call.data == "option2":
        bot.answer_callback_query(call.id, "Вы купили аватарку обычного суслика!")
        user_id = call.from_user.id
        user_data = load_user(user_id)
        user_data["nuts"] -= 100
        user_data['avatar'] = 'normal'



# @bot.message_handler(commands=['mific']) Вырезано
def mific(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        if random.randint(1, 100) == 0:  # 1% chance
            base_nuts = random.randint(1, 9)  # Base number of nuts awarded
            multiplier = random.randint(1, 5)
            nuts_gained = base_nuts * multiplier
            user_data["nuts" == nuts_gained]
            save_user(user_id, user_data)
            update_group_top(message.chat.id, user_id)
            update_global_top(user_id)
            bot.reply_to(message, f"💩 Мифический суслик пришел! Он принес вам {nuts_gained} орешков!")
        else:
            bot.reply_to(message, "😔 Никто сегодня не пришел. И не придет. :)")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")


# Команда /iron
@bot.message_handler(commands=['iron'])
def iron(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        now = datetime.now()
        if user_data["last_iron"] is None or now >= user_data["last_iron"] + timedelta(hours=12):
            user_data["last_iron"] = now
            user_data["last_treat"] = None  # Сброс таймера кормежки
            save_user(user_id, user_data)
            bot.reply_to(message, "💝 Ты погладил суслика! Таймер кормежки сброшен. Используй /treat")
        else:
            time_left = (user_data["last_iron"] + timedelta(hours=12) - now).seconds
            bot.reply_to(message, f"🕑 Подожди еще {time_left // 60} минут перед тем, как снова погладить суслика!")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        name_display = user_data.get('name', "Безымянный")
        avatar_filename = os.path.join(PFP_DIR, f"{user_data.get('avatar', '1')}.png")

        # Подсчет количества приглашённых игроков
        referrals = user_data.get("referrals", [])
        referrals_count = len(referrals)

        # Формирование реферальной ссылки (при необходимости замените ссылку на вашу)
        referral_link = f"https://t.me/suslik\_master\_gamebot?start={user_id}"

        profile_info = (
            f"*ID*: {user_id}\n"
            f"📝 *Имя суслика:* {name_display}\n"
            f"🌰 *Орешки:* {user_data.get('nuts', 0)}\n"
            f"🏆 *Побед в битвах:* {user_data.get('battles_won', 0)}\n"
            f"💔 *Поражений в битвах:* {user_data.get('battles_lost', 0)}\n"
            f"🤝 *Приглашено игроков:* {referrals_count}\n"
        )
        if user_data.get("invited_by"):
            profile_info += f"👥 *Приглашён от ID:* {user_data.get('invited_by')}\n"

        profile_info += f"\n🔗 *Твоя реферальная ссылка:*\n{referral_link}"

        if os.path.exists(avatar_filename):
            try:
                with open(avatar_filename, 'rb') as f:
                    # Отправляем фото с подписью, используя parse_mode='Markdown'
                    bot.send_photo(message.chat.id, f, caption=profile_info, parse_mode='Markdown')
            except Exception as e:
                logging.exception(f"Ошибка отправки фото для пользователя {user_id}: {e}")
                bot.reply_to(message, f"❗ Ошибка отправки фото: {e}")
        else:
            error_message = f"❗️ Аватар не найден: {avatar_filename}"
            bot.reply_to(message, error_message)
            logging.error(error_message)
    else:
        bot.reply_to(message, "❗️ Сначала используй /start.")

@bot.message_handler(commands=['profile_test'])
def profile_test(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        name_display = user_data.get('name', "Безымянный")
        avatar_id = user_data.get('avatar', '1')
        avatar_filename = os.path.join(PFP_DIR, f"{avatar_id}.png")

        status_emoji = "⭐️" if "premium" in user_data and user_data["premium"] else ""

        profile_info = (
            f"*{name_display}{status_emoji}*\n"
            f"──────────────────\n"
            f"🆔 ID: Ⓝ{user_id}Ⓝ\n"
            f"🌰 Орешки: Ⓝ{user_data.get('nuts', 0)}Ⓝ\n"
            f"🏆 Побед в битвах: Ⓝ{user_data.get('battles_won', 0)}Ⓝ\n"
            f"💔 Поражений в битвах: Ⓝ{user_data.get('battles_lost', 0)}Ⓝ\n"
            f"🐶 Порода: {user_data.get('breed', 'Неизвестно')}\n" #Added default value for breed
        )

        # Если игрок еще не участвовал в битвах
        if user_data.get('battles_won', 0) == 0 and user_data.get('battles_lost', 0) == 0:
            profile_info += "🐓 Еще не участвовал в битвах!\n"

        # Добавление информации о рефералах
        referrals = user_data.get("referrals", [])
        referrals_count = len(referrals)
        profile_info += f"🤝 Приглашено игроков: `{referrals_count}`\n"
        if user_data.get("invited_by"):
            profile_info += f"👥 Приглашён от ID: `{user_data.get('invited_by')}`\n"

        # Формирование реферальной ссылки (при необходимости замените ссылку на вашу)
        referral_link = f"https://t.me/suslik\_master\_gamebot?start={user_id}"
        profile_info += f"\n🔗 Твоя реферальная ссылка:\n{referral_link}"

        os.makedirs(PFP_DIR, exist_ok=True)

        if os.path.exists(avatar_filename):
            try:
                with open(avatar_filename, 'rb') as f:
                    # Отправляем фото с подписью, используя parse_mode='Markdown'
                    bot.send_photo(message.chat.id, f, caption=profile_info, parse_mode='Markdown')
            except Exception as e:
                logging.exception(f"Ошибка отправки аватарки: {e}")
                bot.reply_to(message, f"❗️ Ошибка отправки аватарки: {e}")
        else:
            error_message = f"❗️ Аватар не найден для ID: {avatar_id} ({avatar_filename}). Проверьте папку {PFP_DIR}"
            bot.reply_to(message, error_message)
            logging.error(error_message)
    else:
        bot.reply_to(message, "❗️ Сначала используй /start.")


def save_user_pfp(user_id, user_data):  # This function doesn't actually save the PFP, just user data.  Rename appropriately.
    file_path = os.path.join(USERS_DIR, f"{user_id}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving user data for {user_id}: {e}")



# Example of how to change the avatar (you'll need to integrate this into your bot's commands)
# This assumes you have a command like /setavatar that sends an image
#@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.caption == '/setavatar': #Check if the message has the /setavatar caption
        file_id = message.photo[-1].file_id # Get the file ID of the photo
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        user_id = message.from_user.id
        user_data = load_user(user_id)

        # Save the avatar (you might need to adapt this based on your file storage)
        new_avatar_filename = f"{len(os.listdir(PFP_DIR)) + 1}.png" #Get a new file name
        with open(os.path.join(PFP_DIR, new_avatar_filename), 'wb') as new_file:
          new_file.write(downloaded_file)
        user_data['avatar'] = new_avatar_filename.split('.')[0] #save the avatar filename without the extension
        save_user_pfp(user_id, user_data)
        bot.reply_to(message, "👌 Аватар успешно изменен!")

@bot.message_handler(commands=['paid'])
def paid(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    keyboard = telebot.types.InlineKeyboardMarkup()
    callback_button1 = telebot.types.InlineKeyboardButton(text="super орешки", callback_data="option1")
    callback_button2 = telebot.types.InlineKeyboardButton(text="suslikmetr premuim", callback_data="option2")
    callback_button3 = telebot.types.InlineKeyboardButton(text="донат", callback_data="option3")
    callback_button4 = telebot.types.InlineKeyboardButton(text="реклама", callback_data="option4")
    keyboard.add(callback_button1, callback_button2, callback_button3, callback_button4)
    bot.send_message(message.chat.id, "что вы хотите купить?:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback1(call):
    print()

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, f"😊 если у тебя возникли вопросы? Можешь почитать FAQ: https://telegra.ph/CHasto-zadavaemye-voprosy-o-Suslikmetre-04-20")



@bot.message_handler(commands=['name'])
def set_name(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)
    try:
        new_name = " ".join(message.text.split()[1:])
        if len(new_name) > 25:
            return # Прерываем выполнение, если имя слишком длинно
            bot.reply_to(message, "❗ Имя слишком длинное! Максимальная длина - 25 символов.")

        user_data['name'] = new_name
        save_user(user_id, user_data)
        bot.reply_to(message, f"🗨 Ты переименовал своего суслика в '{new_name}'!")

    except IndexError:
        bot.reply_to(message, "❗ Пожалуйста, укажи новое имя: /name [имя].")


# Команда /bonus
@bot.message_handler(commands=['bonus'])
def bonus(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        now = datetime.now()
        if user_data.get("last_bonus") is None or now >= user_data["last_bonus"] + timedelta(days=1):
            bonus_nuts = random.randint(10, 15)
            user_data["nuts"] += bonus_nuts
            user_data["last_bonus"] = now
            save_user(user_id, user_data)
            update_group_top(message.chat.id, user_id)
            update_global_top(user_id)
            bot.reply_to(message, f"⚡ Ты получил {bonus_nuts} орешков в качестве ежедневного бонуса! Всего орешков: {user_data['nuts']}.")
        else:
            time_left = (user_data["last_bonus"] + timedelta(days=1) - now).seconds
            bot.reply_to(message, f"❗ Ты можешь получить свой ежедневный бонус через {time_left // 3600} часов {time_left % 3600 // 60} минут.")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")


import random
import telebot
from telebot import types

# Ваш основной код, включая инициализацию бота и функции load_user, save_user и другие функции, если они есть.

@bot.message_handler(commands=['bite'])
def bite(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data is None:
        bot.reply_to(message, "❗️ Ошибка: не удалось загрузить данные пользователя.")
        return

    if user_data["nuts"] <= 0:
        bot.reply_to(message, "😔 У тебя недостаточно орешков для ставки!")
        return

    try:
        stake = int(message.text.split()[1])
        if stake <= 0 or stake > user_data["nuts"]:
            raise ValueError
    except (IndexError, ValueError):
        bot.reply_to(message, "❗️ Введи корректную ставку: /bite [ставка].")
        return

    if message.reply_to_message is None:
        bot.reply_to(message, "❗️ Ответь на сообщение того, кого хочешь вызвать на бой!")
        return

    opponent_id = message.reply_to_message.from_user.id

    keyboard = types.InlineKeyboardMarkup()
    callback_data = f'accept_bite_{opponent_id}_{stake}_{message.message_id}'
    keyboard.add(
        types.InlineKeyboardButton("Принять ⚔️", callback_data=callback_data),
        types.InlineKeyboardButton("Отказаться 🐓", callback_data=f'decline_bite_{message.message_id}')
    )

    bot.reply_to(message, f"🗡 {message.from_user.first_name} бросает тебе вызов на сражение за {stake} орешков!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_bite') or call.data.startswith('decline_bite'))
def handle_bite_response(call):
    try:
        if call.data.startswith('accept_bite'):
            _, opponent_id_str, stake_str, message_id_str = call.data.split('_')
            opponent_id = int(opponent_id_str)
            stake = int(stake_str)
            message_id = int(message_id_str)

            if call.from_user.id == opponent_id:
                bot.send_message(call.message.chat.id, f"❗️ {call.from_user.first_name}, нельзя принимать свой собственный вызов.")
                return

            challenger_id = call.from_user.id
            challenger_data = load_user(challenger_id)
            opponent_data = load_user(opponent_id)

            if challenger_data is None or opponent_data is None:
                bot.send_message(call.message.chat.id, "❗️ Ошибка: не удалось загрузить данные одного из пользователей.")
                return

            if opponent_data["nuts"] < stake:
                bot.send_message(call.message.chat.id, f"😔 У {opponent_data['name']} недостаточно орешков для ставки!")
                return

            total_nuts = challenger_data["nuts"] + opponent_data["nuts"]
            challenger_chance = challenger_data["nuts"] / total_nuts if total_nuts > 0 else 0

            if random.random() < challenger_chance:
                winner, loser = challenger_id, opponent_id
            else:
                winner, loser = opponent_id, challenger_id

            try:
                winner_data = load_user(winner)
                loser_data = load_user(loser)

                winner_data["nuts"] += stake
                loser_data["nuts"] -= stake

                save_user(winner, winner_data)
                save_user(loser, loser_data)

                bot.send_message(call.message.chat.id, f"🏆 Победитель: {winner_data['name']}! Он забирает {stake} орешков у {loser_data['name']}.")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❗️ Ошибка при обновлении данных пользователей: {e}")

        elif call.data.startswith('decline_bite'):
            _, message_id_str = call.data.split('_')
            message_id = int(message_id_str)
            bot.delete_message(call.message.chat.id, message_id)

    except (ValueError, IndexError, telebot.apihelper.ApiException, Exception) as e:
        bot.send_message(call.message.chat.id, f"❗️ Ошибка: {e}. @mcpeorakul")

# Здесь могут быть другие функции и код, если это необходимо

# @bot.message_handler(commands=['act_NPC956']) Вырезано
def act_NPC956(message):
    name_act = "NPC956"
    bot.reply_to(message, f"я вырезал эту команду. тебе нечего тут делать.") # жесткий тип - ну естественно :)
# @bot.message_handler(commands=['/kill']) Вырезано
    def kill(message):
        bot.reply_to(message, f"Вы ударили {name_act} вы снесли 9999999999 HP")
        bot.reply_to(message, f"Вы убили {name_act} вы получили 0 орешков.")

@bot.message_handler(commands=['new_business'])
def new_business(message):
    bot.reply_to(message, f"❗ Ошибка: BetatestError: это бета-функция")


@bot.message_handler(commands=['setpromo'])
def set_promo(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❗ У тебя нет прав для использования этой команды.")
        return

    # Разделяем текст сообщения на части
    promo_data = message.text.split()

    # Проверяем, достаточно ли параметров
    if len(promo_data) < 4:
        bot.reply_to(message, "❗ Неверный формат команды. Используй: /setpromo [имя] [количество] [время в часах] [количество использований*].")
        return

    try:
        promo_name = promo_data[1]
        promo_amount = int(promo_data[2])  # Пробуем преобразовать в число
        promo_duration = int(promo_data[3])  # Пробуем преобразовать в число
        promo_usage = int(promo_data[4]) if len(promo_data) > 4 else None  # Количество использований (может быть None)

        # Отладочные сообщения
        print(f"Имя промокода: {promo_name}")
        print(f"Количество: {promo_amount}, Время действия: {promo_duration}, Количество использований: {promo_usage}")

        # Загружаем существующие промокоды или создаем новый файл
        promo_file_path = os.path.join(BASE_DIR, "promo.json")
        if not os.path.exists(promo_file_path):
            with open(promo_file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)  # Создаем пустой JSON файл

        with open(promo_file_path, 'r', encoding='utf-8') as f:
            promos = json.load(f)

        # Добавляем или обновляем промокод
        promos[promo_name] = {
            "amount": promo_amount,
            "duration": promo_duration,
            "created_at": datetime.now().isoformat(),
            "usage": promo_usage,  # Сохраняем количество использований, если указано
            "used_by": []  # Список пользователей, которые использовали промокод
        }

        # Сохраняем промокоды обратно в файл
        with open(promo_file_path, 'w', encoding='utf-8') as f:
            json.dump(promos, f, ensure_ascii=False)

        bot.reply_to(message, f"💬 Промокод '{promo_name}' успешно добавлен!")
    except ValueError as e:
        # Выводим сообщение об ошибке с деталями
        print(f"Ошибка: {e}")
        bot.reply_to(message, "❗ Пожалуйста, убедись, что количество и время действия указаны правильно (числовые значения).")


@bot.message_handler(commands=['promo'])
def use_promo(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    promo_name = message.text.split()[1] if len(message.text.split()) > 1 else None

    if promo_name is None:
        bot.reply_to(message, "❗ Пожалуйста, укажи имя промокода: /promo [имя].")
        return

    # Загружаем существующие промокоды
    promo_file_path = os.path.join(BASE_DIR, "promo.json")
    if not os.path.exists(promo_file_path):
        with open(promo_file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)  # Создаем пустой JSON файл

    with open(promo_file_path, 'r', encoding='utf-8') as f:
        promos = json.load(f)

    # Проверяем, существует ли промокод
    if promo_name in promos:
        promo = promos[promo_name]
        created_at = datetime.fromisoformat(promo["created_at"])
        duration = promo["duration"]

        # Проверяем, не истек ли срок действия промокода
        if datetime.now() <= created_at + timedelta(hours=duration):
            # Проверяем, использовал ли пользователь промокод
            if user_id in promo["used_by"]:
                bot.reply_to(message, "❗ Ты уже использовал этот промокод.")
                return

            # Проверяем, сколько использований осталось
            if promo.get("usage") is None or promo["usage"] > 0:
                user_data["nuts"] += promo["amount"]
                save_user(user_id, user_data)

                # Уменьшаем количество использований, если оно указано
                if promo.get("usage") is not None:
                    promo["usage"] -= 1
                    if promo["usage"] == 0:
                        del promos[promo_name]  # Удаляем промокод, если использований больше нет

                # Добавляем пользователя в список использовавших промокод
                promo["used_by"].append(user_id)

                # Сохраняем обновленные промокоды обратно в файл
                with open(promo_file_path, 'w', encoding='utf-8') as f:
                    json.dump(promos, f, ensure_ascii=False)

                bot.reply_to(message, f"🌰 Ты использовал промокод '{promo_name}' и получил {promo['amount']} орешков!")
            else:
                bot.reply_to(message, "😔 Срок действия промокода истек.")
        else:
            bot.reply_to(message, "😔 Срок действия промокода истек.")
    else:
        bot.reply_to(message, "❓ Промокод не найден.")


# Команда /invest
@bot.message_handler(commands=['invest'])
def invest(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        try:
            amount = int(message.text.split()[1])
            if amount <= 0:
                raise ValueError
        except (IndexError, ValueError):
            bot.reply_to(message, "❗ Введи корректную сумму для инвестирования в чат: /invest [сумма].")
            return

        # Загружаем данные группы
        group_data = load_group_data(message.chat.id)

        # Проверяем, достаточно ли орешков у пользователя
        if user_data["nuts"] < amount:
            bot.reply_to(message, "😔 У тебя недостаточно орешков для инвестирования!")
            return

        # Обновляем казну группы
        group_data["treasury"] += amount
        user_data["nuts"] -= amount  # Снимаем орешки с пользователя

        # Сохраняем обновленные данные
        save_group_data(message.chat.id, group_data)
        save_user(user_id, user_data)

        # Вызов функции для обновления глобального топа групп
        update_global_group_top(message.chat.id)

        bot.reply_to(message, f"👌 Ты инвестировал {amount} орешков в казну группы!")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")


# Команда /withdraw
@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        try:
            amount = int(message.text.split()[1])
            if amount <= 0 or amount > 15:
                raise ValueError
        except (IndexError, ValueError):
            bot.reply_to(message, "❗ Введи корректную сумму для снятия: /withdraw [сумма]. Максимум 15 орешков в день.")
            return

        # Загружаем данные группы
        group_data = load_group_data(message.chat.id)

        # Проверяем, разрешено ли снятие орешков
        if not group_data.get("withdrawal_allowed", True):
            bot.reply_to(message, "❗ Снятие орешков на данный момент запрещено в этой группе.")
            return

        # Проверяем, сколько орешков уже снято за день
        if user_data.get("withdrawn_today", 0) + amount > 15:
            bot.reply_to(message, "❗ Ты не можешь снять больше 15 орешков за день.")
            return

        # Проверяем, достаточно ли орешков в казне группы
        if group_data["treasury"] < amount:
            bot.reply_to(message, "😔 В казне чата недостаточно орешков для снятия.")
            return

        # Обновляем данные пользователя и группы
        user_data["nuts"] += amount
        user_data["withdrawn_today"] = user_data.get("withdrawn_today", 0) + amount
        group_data["treasury"] -= amount

        save_user(user_id, user_data)
        save_group_data(message.chat.id, group_data)

        bot.reply_to(message, f"👌 Ты снял {amount} орешков из казны группы!")
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")


# Команда /w для управления снятием орешков
@bot.message_handler(commands=['w'])
def manage_withdrawal(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❗ Только администраторы могут использовать эту команду.")
        return

    command = message.text.split()
    if len(command) != 2 or command[1] not in ['on', 'off', '1', '0']:
        bot.reply_to(message, "🔧 Используй: /w [on|off|1|0].")
        return

    group_data = load_group_data(message.chat.id)
    group_data["withdrawal_allowed"] = command[1] in ['on', '1']
    save_group_data(message.chat.id, group_data)

    status = "разрешено" if group_data["withdrawal_allowed"] else "запрещено"
    bot.reply_to(message, f"👌 Снятие орешков с казны {status}.")

# Команда /gp для получения информации о группе
@bot.message_handler(commands=['gp'])
def group_info(message):
    group_data = load_group_data(message.chat.id)

    total_nuts = sum(load_user(user_id)["nuts"] for user_id in get_all_user_ids_in_group(message.chat.id))

    response_message = (
        f"🛡 Информация о группе:\n"
        f"🌰 Общее количество орешков у всех участников: {total_nuts}\n"
        f"💰 Казна группы: {group_data['treasury']}\n"
    )

    bot.reply_to(message, response_message)

# Команда /tops
@bot.message_handler(commands=['tops'])
def tops(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Топ чата", callback_data='top_group'),
        InlineKeyboardButton("Топ игроков", callback_data='global_top'),
        InlineKeyboardButton("Топ групп", callback_data='global_group_top')
    )
    bot.reply_to(message, "📊 Выбери, какой топ-лист хочешь посмотреть:", reply_markup=keyboard)

# Обработка нажатий на кнопки для топов
@bot.callback_query_handler(func=lambda call: call.data in ['top_group', 'global_top', 'global_group_top'])
def callback_query(call):
    if call.data == 'top_group':
        show_group_top(call.message.chat.id, call.from_user.id)
    elif call.data == 'global_top':
        show_global_top(call.message.chat.id)
    elif call.data == 'global_group_top':
        show_global_group_top(call.message.chat.id)

def show_group_top(chat_id, user_id):
    group_data = load_group_data(chat_id)
    group_top = load_group_top(chat_id)
    user_position = get_user_position_in_group_top(chat_id, user_id)

    response_message = "📊 Топ группы:\n"
    for position, user_data in enumerate(group_top[:10], start=1):
        response_message += f"{position}. {user_data['name']} - {user_data['nuts']} орешков\n"

    response_message += f"---\n🦫 Твое место: {user_position}"
    bot.send_message(chat_id, response_message)

def show_global_top(user_id):
    global_top = load_global_top()
    user_position = get_user_position_in_global_top(user_id)

    response_message = "📊 Топ игроков:\n"
    for position, user_data in enumerate(global_top[:10], start=1):
        response_message += f"{position}. {user_data['name']} - {user_data['nuts']} орешков\n"

    response_message += f"---\n🦫 Твое место: {user_position}"
    bot.send_message(user_id, response_message)

def show_global_group_top(user_id):
    global_group_top = load_global_group_top()
    user_position = get_user_position_in_global_group_top(user_id)

    response_message = "📊 Топ групп:\n"
    for position, group_data in enumerate(global_group_top[:10], start=1):
        response_message += f"{position}. Группа: {group_data['name']} - {group_data['nuts']} орешков\n"

    response_message += f"---\n🛡 Твое место: {user_position}"
    bot.send_message(user_id, response_message)

# Функции для загрузки и сохранения данных о топах
def load_group_top(chat_id):
    file_path = os.path.join(TOPS_DIR, f"group_{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"❗ Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_group_top(chat_id)
            return load_group_top(chat_id)  # Попробуем загрузить заново после восстановления
    else:
        return []

def restore_group_top(chat_id):
    backup_file_path = os.path.join(BACKUP_DIR, "tops", f"group_{chat_id}.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_group_top(chat_id, data)

def load_global_top():
    file_path = os.path.join(TOPS_DIR, "global_top.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"❗ Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_global_top()
            return load_global_top()  # Попробуем загрузить заново после восстановления
    else:
        return []

def restore_global_top():
    backup_file_path = os.path.join(BACKUP_DIR, "tops", "global_top.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_global_top(data)

def load_global_group_top():
    file_path = os.path.join(TOPS_DIR, "global_group_top.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"❗ Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_global_group_top()
            return load_global_group_top()  # Попробуем загрузить заново после восстановления
    else:
        return []

def restore_global_group_top():
    backup_file_path = os.path.join(BACKUP_DIR, "tops", "global_group_top.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_global_group_top(data)

def save_group_top(chat_id, group_top):
    file_path = os.path.join(TOPS_DIR, f"group_{chat_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(group_top, f, ensure_ascii=False)
    # Создаем резервную копию после сохранения
    backup_data()

def save_global_top(global_top):
    file_path = os.path.join(TOPS_DIR, "global_top.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(global_top, f, ensure_ascii=False)
    # Создаем резервную копию после сохранения
    backup_data()

def save_global_group_top(global_group_top):
    file_path = os.path.join(TOPS_DIR, "global_group_top.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(global_group_top, f, ensure_ascii=False)
    # Создаем резервную копию после сохранения
    backup_data()

# Функции для получения позиций в топах
def get_user_position_in_group_top(chat_id, user_id):
    group_top = load_group_top(chat_id)
    for position, user_data in enumerate(group_top, start=1):
        if user_data['id'] == user_id:
            return position
    return "Не в топе"

def get_user_position_in_global_top(user_id):
    global_top = load_global_top()
    for position, user_data in enumerate(global_top, start=1):
        if user_data['id'] == user_id:
            return position
    return "Не в топе"

def get_user_position_in_global_group_top(user_id):
    global_group_top = load_global_group_top()
    for position, group_data in enumerate(global_group_top, start=1):
        if group_data['id'] == user_id:
            return position
    return "Не в топе"

# Обновление данных в топах
def update_group_top(chat_id, user_id):
    group_top = load_group_top(chat_id)
    user_data = load_user(user_id)

    # Проверяем, есть ли пользователь в топе
    for i, data in enumerate(group_top):
        if data['id'] == user_id:
            group_top[i]['nuts'] = user_data['nuts']
            break
    else:
        # Если пользователя нет в топе, добавляем его
        group_top.append({
            'id': user_id,
            'name': bot.get_chat_member(chat_id, user_id).user.username or user_data['name'],
            'nuts': user_data['nuts']
        })

    # Сортируем топ по количеству орешков
    group_top = sorted(group_top, key=lambda x: x['nuts'], reverse=True)

    # Сохраняем обновленный топ
    save_group_top(chat_id, group_top)

def update_global_top(user_id):
    global_top = load_global_top()
    user_data = load_user(user_id)

    # Обновляем или добавляем пользователя в глобальный топ
    for i, data in enumerate(global_top):
        if data['id'] == user_id:
            global_top[i]['nuts'] = user_data['nuts']
            break
    else:
        # Этот блок выполняется, если не было найдено совпадений в цикле
        global_top.append({
            'id': user_id,
            'name': bot.get_chat_member(user_id, user_id).user.username or user_data['name'],  # Используем никнейм
            'nuts': user_data['nuts']
        })

    # Сортируем топ по количеству орешков
    global_top = sorted(global_top, key=lambda x: x['nuts'], reverse=True)

    # Сохраняем обновленный топ
    save_global_top(global_top)

def update_global_group_top(chat_id):
    global_group_top = load_global_group_top()
    group_data = load_group_data(chat_id)

    # Определяем имя группы: если в данных нет имени, пытаемся получить его через бота
    group_name = group_data.get('name')
    if not group_name:
        try:
            chat = bot.get_chat(chat_id)
            group_name = chat.title
        except Exception as e:
            print(f"❗ Ошибка получения данных группы {chat_id}: {e}")
            group_name = 'Группа без имени'

    # Обновляем или добавляем группу в глобальный топ
    for i, data in enumerate(global_group_top):
        if data['id'] == chat_id:
            global_group_top[i]['nuts'] = group_data['treasury']
            global_group_top[i]['name'] = group_name
            break
    else:
        global_group_top.append({'id': chat_id, 'name': group_name, 'nuts': group_data['treasury']})

    # Сортируем топ по количеству орешков
    global_group_top = sorted(global_group_top, key=lambda x: x['nuts'], reverse=True)
    save_global_group_top(global_group_top)


# Пример обработчика команды /lol, который использует функцию send_to_ai
@bot.message_handler(commands=['lol'])
def lol(message):
    user_id = message.from_user.id
    group_name = message.chat.title if message.chat.title else "Личная переписка"
    # Пример: если пользователь передал тему в команде /lol, то она будет добавлена к промпту
    command_parts = message.text.split(maxsplit=1)
    topic = command_parts[1] if len(command_parts) > 1 else ""
    prompt_user = "Придумай анекдот про сусликов" + (f" на тему: {topic}" if topic else "")

    # Передаем также заполненные поля group_name, общее количество орешков и казну
    # В данном примере total_nuts и treasury заданы условно – замените их на реальные данные
    total_nuts = 0  # Рассчитайте общее количество орешков в группе
    treasury = 0    # Получите значение казны группы

    ai_response = send_to_ai(user_id, prompt_user, group_name, total_nuts, treasury, "")
    bot.reply_to(message, ai_response)


# =================== КЛАСС АДАПТЕРА ДЛЯ ИИ ===================
class SearchGPTAdapter:
    BASE_URL = "https://text.pollinations.ai"
    MODEL = "openai-large"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_url = f"{self.BASE_URL}/openai"
        self.headers = {
            "Content-Type": "application/json",
        }

    def chat_completions(self, messages):
        try:
            payload = {
                "model": self.MODEL,
                "messages": messages
            }
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60.0
            )
            response.raise_for_status()
            api_response = response.json()
            model_name = api_response.get("model")
            response_content = api_response["choices"][0]["message"]["content"]
            return model_name, response_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            return None, None
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error parsing API response: {e}")
            return None, None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return None, None


# =================== ИНТЕГРАЦИЯ С ИИ ===================
def send_to_ai(user_id, message, group_name, total_nuts, treasury, bot_message):
    """
    Отправляет запрос к ИИ через адаптер SearchGPTAdapter.

    Аргументы:
      user_id: идентификатор пользователя
      message: сообщение пользователя
      group_name: название группы или "Личная переписка"
      total_nuts: общее количество орешков в группе
      treasury: казна группы
      bot_message: сообщение от бота (если есть)
    """
    user_info = load_user(user_id)
    prompt = (
        "Ты — ИИ, который отвечает на вопросы и общается с пользователями игрового Telegram-бота \"СусликМетр\".\n"
        "Бот помогает игрокам заботиться о своих сусликах, давая советы и генерируя анекдоты.\n"
        "Вот некоторые команды, которые может использовать пользователь:\n"
        "/start - начать игру\n"
        "/treat - покормить суслика\n"
        "/bonus - бонус в орешках\n"
        "/iron - погладить суслика\n"
        "/store - магазин товаров\n"
        "/buy [номер товара] - купить товар\n"
        "/inventory - посмотреть инвентарь\n"
        "/use [номер товара] - использовать товар\n"
        "/profile - посмотреть профиль\n"
        "/gp - информация о группе\n"
        "/tops - топ-листы\n"
        "/lol [тема] - сгенерировать анекдот\n"
        "/promo [промокод] - активировать промокод\n\n"
        "Информация о новом сообщении:\n"
        "Группа: {group_name}\n"
        "Общее количество орешков в группе: {total_nuts}\n"
        "Казна группы: {treasury}\n"
        "Имя: {name}\n"
        "Фамилия: {surname}\n"
        "Юзернейм: {username}\n"
        "ID: {user_id}\n"
        "Орешков: {nuts}\n"
        "Побед в битвах: {battles_won}\n"
        "Поражений в битвах: {battles_lost}\n"
        "Сообщение от пользователя:\n"
        "{message}\n"
        "Сообщение от бота:\n"
        "{bot_message}\n"
    ).format(
        group_name=group_name,
        total_nuts=total_nuts,
        treasury=treasury,
        name=user_info.get('name', 'Не указано'),
        surname=user_info.get('surname', 'Не указана'),
        username=user_info.get('username', 'Не указано'),
        user_id=user_id,
        nuts=user_info.get('nuts', 0),
        battles_won=user_info.get('battles_won', 0),
        battles_lost=user_info.get('battles_lost', 0),
        message=message,
        bot_message=bot_message
    )

    messages_payload = [{"role": "user", "content": prompt}]
    adapter = SearchGPTAdapter()
    model_name, response_content = adapter.chat_completions(messages_payload)
    if response_content:
        return response_content
    else:
        return "❗ Ошибка обращения к ИИ. Пожалуйста, попробуйте позже."


# Обработка сообщений от пользователей (включая ответы на сообщения бота)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    group_name = message.chat.title if message.chat.title else "Личная переписка"
    user_data = load_user(user_id)

    # Проверяем, если сообщение от бота
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        # Получаем текст сообщения от пользователя
        user_message = message.text

        # Получаем текст сообщения бота, на которое ответил пользователь
        bot_message = message.reply_to_message.text

        # Получаем общее количество орешков и казну группы
        group_data = load_group_data(message.chat.id)
        total_nuts = sum(load_user(uid)["nuts"] for uid in get_all_user_ids_in_group(message.chat.id))
        treasury = group_data["treasury"]

        # Отправляем сообщение в ИИ и получаем ответ
        ai_response = send_to_ai(user_id, user_message, group_name, total_nuts, treasury, bot_message)

        # Отправляем ответ от ИИ обратно пользователю
        bot.reply_to(message, ai_response)

        # Выводим ответ ИИ в консоль для отладки
        print(f"Ответ ИИ для пользователя {user_id}: {ai_response}")

    # Если сообщение не является ответом на сообщение от бота, просто игнорируем его
    else:
        return  # Игнорируем остальные сообщения

@bot.message_handler(commands=['fugu'])
def fugu_command(message):
    phrases = [
        "Что?!? Какой фугу? Ты башкой тронулся?",
        "Знаю я тут одну знакомую рыбку, давно с ним не виделся...",
        "Слушай, зачем тебе этот фугу? А, зачем мне он? Он у меня долг взял 1к орешков",
        "Дааа... Знаю такого, вместе учились, да пошёл он не по тем стопам... По программистким стопам... Больше я его не видел...",
        "Он ест детей"
    ]
    bot.reply_to(message, random.choice(phrases))

@bot.message_handler(commands=['arab', 'Arab'])
def Arab_command(message):
    Arab = [
        "أخي ، اشتر البطيخ الرخيص مني.",
        "أنا أعرف عربي هناك, انه الحمار كسول.",
        "أوه ، ما لم يكن لديك من أجل التوصل إلى أن يكون قليلا من التسلل",
        "نعم ، أنا أتكلم العربية جيدا."
    ]
    bot.reply_to(message, random.choice(Arab))

# Основной цикл
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True, timeout=20)
