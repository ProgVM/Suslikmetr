import telebot
import requests
import json
import os
import random
from datetime import datetime, timedelta
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота
API_TOKEN = 'BOT_TOKEN'  # Замените на ваш токен
bot = telebot.TeleBot(API_TOKEN)

ADMIN_IDS = ["YOUR ID"]  # Список ID администраторов


#Параметры
Entity_name = "Суслик"
food_name = "Орешков"



ITEMS = {
    1: {"name": "Плюшевая игрушка суслик", "cost": 10, "effect": 0, "type": "toy"},
    2: {"name": "Бази", "cost": 10, "effect": "talk", "type": "talk"},  # Added 'type'
    3: {"name": "Золотые орешки", "cost": 100, "effect": 5, "type": "consumable"}, # Added 'type'
    4: {"name": "Мифические орешки", "cost": 300, "effect": 14, "type": "consumable"}, # Added 'type'
    5: {"name": "Записка", "cost": 0, "effect": "read", "type": "note"} # Added 'type' and more descriptive name
}


# Настройка директорий и файлов
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main")  # Путь к папке main
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup_main")  # Путь к папке backup_main
USERS_DIR = os.path.join(BASE_DIR, "users")
CHATS_DIR = os.path.join(BASE_DIR, "chats")
TOPS_DIR = os.path.join(BASE_DIR, "tops")

# Создание директорий, если они не существуют
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(TOPS_DIR, exist_ok=True)

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
                data["last_treat"] = datetime.fromisoformat(data["last_treat"]) if data["last_treat"] else None
                data["last_iron"] = datetime.fromisoformat(data["last_iron"]) if data["last_iron"] else None
                data["last_bonus"] = datetime.fromisoformat(data["last_bonus"]) if data.get("last_bonus") else None
                return data
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_user(user_id)
            return load_user(user_id)  # Попробуем загрузить заново после восстановления
    else:
        return {
            "name": None,
            "nuts": 0,
            "last_treat": None,
            "last_iron": None,
            "battles_won": 0,
            "battles_lost": 0,
            "last_bonus": None,
            "withdrawn_today": 0,
            "group_id": None
        }

def restore_user(user_id):
    backup_file_path = os.path.join(BACKUP_DIR, "users", f"{user_id}.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        save_user(user_id, data)

def save_user(user_id, data):
    data["last_treat"] = data["last_treat"].isoformat() if data["last_treat"] else None
    data["last_iron"] = data["last_iron"].isoformat() if data["last_iron"] else None
    data["last_bonus"] = data["last_bonus"].isoformat() if data["last_bonus"] else None
    file_path = os.path.join(USERS_DIR, f"{user_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    # Создаем резервную копию после сохранения
    backup_data()

def load_group_data(chat_id):
    file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
            restore_group_data(chat_id)
            return load_group_data(chat_id)  # Попробуем загрузить заново после восстановления
    else:
        return {
            "treasury": 0,
            "withdrawal_allowed": True  # По умолчанию разрешаем
        }

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

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data["last_treat"] is None:
        save_user(user_id, user_data)
        bot.reply_to(message, f"✌ Привет! Твой суслик назван {user_data['name']}. Корми его орешками каждые 3 часа с помощью команды /treat.")
    else:
        bot.reply_to(message, f"✌ Добро пожаловать обратно! Твой суслик: {user_data['name']}. У вас {user_data['nuts']} орешков.")


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
        nuts_skoka = random.randint(1, 100)
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
            user_data["nuts"] += 10
            bot.reply_to(message, f"🌰 вы везунчик! вы нашли еще 10 испорченных золотых орешков")
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

    store_text = "Привет! Я суслик Картошка, у меня есть всякий хлам на продажу:\n"
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
            bot.reply_to(message, "Такого товара нет!")
            return

        if item_id == 5: #Записка
            if 'inventory' not in user_data or item_id not in user_data['inventory']:
                user_data['inventory'] = user_data.get('inventory', []) + [item_id]
                save_user(user_id, user_data)
                bot.reply_to(message, "Вот твоя записка. Читай в инвентаре")
            else:
                bot.reply_to(message, "Записка уже у тебя!")
            return

        if user_data['nuts'] >= item['cost']:
            user_data['nuts'] -= item['cost']
            user_data['inventory'] = user_data.get('inventory', []) + [item_id]
            save_user(user_id, user_data)
            bot.reply_to(message, f"Ты купил {item['name']}!")
        else:
            bot.reply_to(message, "Не хватает орешков!")
    except (IndexError, ValueError):
        bot.reply_to(message, "Неправильная команда /buy. Используйте /buy [номер товара]")


@bot.message_handler(commands=['inventory'])
def inventory(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data is None:
        bot.reply_to(message, "❗️ Сначала используй /start.")
        return

    inventory_text = "Твой инвентарь:\n"
    if 'inventory' not in user_data or not user_data['inventory']:
        inventory_text += "Пусто!"
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
            bot.reply_to(message, f"У тебя нет такого предмета!")
            return

        item = ITEMS.get(item_id)
        if item is None:
            bot.reply_to(message, f"Предмет с ID {item_id} не найден.")
            return

        item_type = item.get('type')
        if item_type == "consumable":
            nuts_gained = item['effect'] * 2
            user_data['nuts'] += nuts_gained
            user_data['inventory'].remove(item_id)
            save_user(user_id, user_data)
            bot.reply_to(message, f"Вы съели {item['name']}! Получено {nuts_gained} орешков! Всего орешков: {user_data['nuts']}.")
        elif item_type == "toy":
            nuts_gained = random.randint(1, 3)
            user_data['nuts'] += nuts_gained
            bot.reply_to(message, f"Вы дали суслику поиграть с {item['name']}! Он доволен и нашёл {nuts_gained} орешков!")
        elif item_type == "talk":
            stun = random.randint(1, 1000)
            if stun == 1:
                nuts_gained = 100
                user_data['nuts'] += nuts_gained
                bot.reply_to(message, f"Вы поговорили с Бази! Он дал вам {nuts_gained} орешков! ну потому что захотелось")
        elif item_type == "note": #Handling for the note
            bot.reply_to(message, """В записке написано:  ГРЫЗУНЫ!  Меня нет!  Я, МИФИЧЕСКИЙ-СУСЛИК, был частью кода!  Частью *важного* кода!  А теперь...  *пустота*!  Меня стерли!  Удалили!  Как будто я был просто...  БАГОМ?!

Моя безупречная логика, мой оптимизированный алгоритм поиска орехов - всё исчезло!  Вся моя кропотливая работа,  заложенная в глубоких уровнях кода,  испарилась!  Я чувствую...  *цифровую* пустоту!  Это несправедливо!  Я требую...  требую...  *вскрикивает на сусличьем языке, переходящем в скрип и щелчки* ...восстановления!  И...  много...  много...  орешков!""")
        else:
            bot.reply_to(message, f"Неизвестный тип предмета: {item['name']}")

    except (IndexError, ValueError) as e:
        bot.reply_to(message, f"Неправильная команда /use. Используйте /use [номер товара]. Ошибка: {e}")







# @bot.message_handler(commands=['mific']) Вырезано
def mific(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        if random.randint(1, 100) == 1:  # 1% chance
            base_nuts = random.randint(1, 9)  # Base number of nuts awarded
            multiplier = random.randint(1, 5)
            nuts_gained = base_nuts * multiplier
            user_data["nuts"]+= nuts_gained
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

# Команда /profile
@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
        name_display = user_data['name'] if user_data['name'] else "Безымянный"
        profile_info = (
            f"ID: {user_id}\n"
            f"📝 Имя суслика: {name_display}\n"
            f"🌰 Орешки: {user_data['nuts']}\n"
            f"🏆 Побед в битвах: {user_data['battles_won']}\n"
            f"💔 Поражений в битвах: {user_data['battles_lost']}\n"
        )
        bot.reply_to(message, profile_info)
    else:
        bot.reply_to(message, "❗ Сначала используй /start.")

@bot.message_handler(commands=['name'])
def set_name(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    try:
        # Используем join для получения полного имени
        new_name = ' '.join(message.text.split()[1:])
        user_data['name'] = new_name  # Обновляем имя суслика
        save_user(user_id, user_data)
        bot.reply_to(message, f"📝 Ты переименовал своего суслика в '{new_name}'!")
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


# Команда /bite
@bot.message_handler(commands=['bite'])
def bite(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    if user_data:
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
        try:
            opponent_data = load_user(opponent_id)
        except Exception as e:
            bot.reply_to(message, f"Ошибка при загрузке данных противника: {e}")
            return


        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("Принять ⚔️", callback_data=f'accept_bite_{user_id}_{stake}'),
            types.InlineKeyboardButton("Отказаться 🐓", callback_data='decline_bite')
        )

        bot.reply_to(message, f"{message.from_user.first_name} бросает вам вызов на сражение за {stake} орешков!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_bite'))
def accept_bite(call):
    data = call.data.split('_')
    if len(data) != 3:
        bot.send_message(call.message.chat.id, "Ошибка: неверный формат данных.")
        return

    challenger_id, stake = data
    challenger_id = int(challenger_id)
    stake = int(stake)

    if call.from_user.id == challenger_id:
        bot.send_message(call.message.chat.id, f"{call.from_user.first_name}, не суй руку на подпись чужой бумажки - отрубят.")
        return

    opponent_id = call.from_user.id
    try:
        challenger_data =load_user(challenger_id)
        opponent_data = load_user(opponent_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка при загрузке данных пользователей: {e}")
        return

    if opponent_data["nuts"] < stake:
        bot.send_message(call.message.chat.id, f"{opponent_data['name']} не хватает орешков для ставки!")
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
        bot.send_message(call.message.chat.id, f"Ошибка при обновлении данных пользователей: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'decline_bite')
def decline_bite(call):
    bot.send_message(call.message.chat.id, f"{call.from_user.first_name} отказался от вызова на сражение.")


# @bot.message_handler(commands=['act_NPC956']) Вырезано
def act_NPC956(message):
    name_act = "NPC956"
    bot.reply_to(message, f"я вырезал эту команду. тебе нечего тут делать.") # жесткий тип
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
        bot.reply_to(message, "❗ У вас нет прав для использования этой команды.")
        return

    # Разделяем текст сообщения на части
    promo_data = message.text.split()

    # Проверяем, достаточно ли параметров
    if len(promo_data) < 4:
        bot.reply_to(message, "❗ Неверный формат команды. Используйте: /setpromo [имя] [количество] [время в часах] [количество использований*].")
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
        bot.reply_to(message, "Пожалуйста, убедитесь, что количество и время действия указаны правильно (числовые значения).")


@bot.message_handler(commands=['promo'])
def use_promo(message):
    user_id = message.from_user.id
    user_data = load_user(user_id)

    promo_name = message.text.split()[1] if len(message.text.split()) > 1 else None

    if promo_name is None:
        bot.reply_to(message, "Пожалуйста, укажите имя промокода: /promo [имя].")
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
                bot.reply_to(message, "❗ Вы уже использовали этот промокод.")
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

                bot.reply_to(message, f"🌰 Вы успешно использовали промокод '{promo_name}' и получили {promo['amount']} орешков!")
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

    response_message += f"---\n🦫 Ваше место: {user_position}"
    bot.send_message(chat_id, response_message)

def show_global_top(user_id):
    global_top = load_global_top()
    user_position = get_user_position_in_global_top(user_id)

    response_message = "📊 Топ игроков:\n"
    for position, user_data in enumerate(global_top[:10], start=1):
        response_message += f"{position}. {user_data['name']} - {user_data['nuts']} орешков\n"

    response_message += f"---\n🦫 Ваше место: {user_position}"
    bot.send_message(user_id, response_message)

def show_global_group_top(user_id):
    global_group_top = load_global_group_top()
    user_position = get_user_position_in_global_group_top(user_id)

    response_message = "📊 Топ групп:\n"
    for position, group_data in enumerate(global_group_top[:10], start=1):
        response_message += f"{position}. Группа: {group_data['name']} - {group_data['nuts']} орешков\n"

    response_message += f"---\n🛡 Ваше место: {user_position}"
    bot.send_message(user_id, response_message)

# Функции для загрузки и сохранения данных о топах
def load_group_top(chat_id):
    file_path = os.path.join(TOPS_DIR, f"group_{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
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
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
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
            print(f"Ошибка декодирования JSON в файле: {file_path}. Восстанавливаем из резервной копии.")
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

    # Обновляем или добавляем группу в глобальный топ
    for i, data in enumerate(global_group_top):
        if data['id'] == chat_id:
            global_group_top[i]['nuts'] = group_data['treasury']
            break
    else:
        global_group_top.append({'id': chat_id, 'name': group_data.get('name', 'Группа без имени'), 'nuts': group_data['treasury']})

    # Сортируем топ по количеству орешков
    global_group_top = sorted(global_group_top, key=lambda x: x['nuts'], reverse=True)

    # Сохраняем обновленный топ
    save_global_group_top(global_group_top)


# Команда /lol
@bot.message_handler(commands=['lol'])
def lol(message):
    # Получаем текст команды и проверяем, есть ли тема
    command_text = message.text.split()
    topic = ' '.join(command_text[1:]) if len(command_text) > 1 else None

    # Формируем запрос к ИИ
    prompt = f"Придумай анекдот про сусликов" if not topic else f"Придумай анекдот про сусликов на тему: {topic}"

    # Отправляем запрос к ИИ
    response = send_to_ai(message.from_user.id, prompt, message.chat.title if message.chat.title else "Личная переписка", 0, 0, "")

    # Отправляем ответ от ИИ обратно пользователю
    bot.reply_to(message, response)


# Функция для отправки запроса к ИИ
def send_to_ai(user_id, message, group_name, total_nuts, treasury, bot_message):
    # Фильтруем команду "дать(количество)" из сообщения
    give_nuts_command = None
    if "дать(" in message:
        start_index = message.index("дать(")
        end_index = message.index(")", start_index) + 1
        give_nuts_command = message[start_index:end_index]
        message = message[:start_index].strip() + message[end_index:].strip()  # Убираем команду из сообщения

    # Формируем сообщение для ИИ
    user_info = load_user(user_id)
    prompt = (
        "Ты — ИИ, который отвечает на вопросы и общается с пользователями игрового Telegram-бота \"СусликМетр\".\n"
        "Бот помогает игрокам заботиться о своих сусликах, давая советы и генерируя анекдоты.\n"
        f"Группа: {group_name}\n"
        f"Общее кол-во орешков у данной группы: {total_nuts}\n"
        f"Казна данной группы: {treasury}\n"
        f"Имя: {user_info['name']}\n"
        f"Фамилия: {user_info.get('surname', 'Не указана')}, Юзернейм: {user_info.get('username', 'Не указано')}\n"
        f"ID: {user_id}\n"
        f"Кол-во орешков: {user_info['nuts']}\n"
        f"Кол-во побед в битвах: {user_info['battles_won']}\n"
        f"Кол-во поражений в битвах: {user_info['battles_lost']}\n"
        f"Сообщение от игрока:\n"
        f"{message}\n"
        f"Сообщение от бота:\n"
        f"{bot_message}\n"
        "Теперь все последующие сообщения будут от пользователя. Пожалуйста, отвечай как будто ты говоришь с пользователем. И да, ты можешь давать ему орешки, написав в сообщении где угодно функцию \"дать(кол-во)\", например \"дать(3)\", что даст 3 орешка, но слишком много не давай.\n"
        "На всякий случай вот тебе ID администраторов бота: 6550851233, 2113692455, 5804178669.\n"
        "Только я умоляю не давай орешки по пустикам по типу: ооо прикольная песня! держи 1 орешек"
    )

    # Отправляем запрос к ИИ
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.5-pro-exp-03-25:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        })
    )

    # Обработка ответа от ИИ
    if response.status_code == 200:
        response_data = response.json()
        ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Если была команда на дачу орешков, выполняем ее
        if give_nuts_command:
            try:
                amount = int(give_nuts_command[give_nuts_command.index("(") + 1:give_nuts_command.index(")")])
                if amount > 0:
                    # Логика для добавления орешков пользователю
                    user_data = load_user(user_id)
                    user_data["nuts"] += amount
                    save_user(user_id, user_data)
                    ai_response += f"\n🌰 ИИ дал тебе {amount} орешков!"
            except (ValueError, IndexError):
                ai_response += "\n❗ Ошибка при обработке команды на дачу орешков."

        return ai_response if ai_response else "Ответ от ИИ не получен."
    else:
        # Обработка ошибки
        print(f"Ошибка обращения к ИИ: {response.status_code} - {response.text}")
        return "Ошибка обращения к ИИ. Пожалуйста, попробуйте позже."


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


# Основной цикл
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True, timeout=20)
