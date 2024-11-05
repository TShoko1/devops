import telebot
from datetime import datetime
from telebot import types
from sqlalchemy.orm import Session
from models import Task, SessionLocal
import configparser

# Чтение конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

# Получение токена из файла конфигурации
BOT_TOKEN = config['telegram']['token']

bot = telebot.TeleBot(BOT_TOKEN)

# Функция для логирования действий
def log_action(user_id, action, task_text=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] User {user_id}: {action} - {task_text}")

# Создаем функцию для инициализации сессии при каждом запросе
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Главное меню команд
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton("➕ Добавить задачу"),
               types.KeyboardButton("📋 Показать задачи"))
    markup.add(types.KeyboardButton("✅ Завершить задачу"),
               types.KeyboardButton("❌ Удалить задачу"))
    markup.add(types.KeyboardButton("✏️ Изменить задачу"))
    return markup

# Команда /start с отправкой меню
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я TaskFlowBot.\nВыберите команду из меню ниже:", reply_markup=main_menu())
    log_action(message.from_user.id, "started bot")

# Обработка кнопок меню для различных команд
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == "➕ Добавить задачу":
        msg = bot.reply_to(message, "Введите текст задачи для добавления:")
        bot.register_next_step_handler(msg, add_task)
    elif message.text == "📋 Показать задачи":
        list_tasks(message)
    elif message.text == "✅ Завершить задачу":
        msg = bot.reply_to(message, "Введите номер задачи для завершения:")
        bot.register_next_step_handler(msg, complete_task_step)
    elif message.text == "❌ Удалить задачу":
        msg = bot.reply_to(message, "Введите номер задачи для удаления:")
        bot.register_next_step_handler(msg, delete_task_step)
    elif message.text == "✏️ Изменить задачу":
        msg = bot.reply_to(message, "Введите номер задачи для изменения:")
        bot.register_next_step_handler(msg, edit_task_step_number)

# Функция для добавления задачи
def add_task(message):
    task_text = message.text.strip()
    user_id = message.from_user.id
    if task_text:
        db = next(get_db())  # Инициализация сессии
        new_task = Task(user_id=user_id, text=task_text, completed=False, created_at=datetime.now())
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        bot.reply_to(message, f"Задача '{task_text}' добавлена!")
        log_action(user_id, "added task", task_text)
    else:
        bot.reply_to(message, "Введите текст задачи для добавления")

# Просмотр задач
def list_tasks(message):
    user_id = message.from_user.id
    db = next(get_db())  # Инициализация сессии
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    
    if tasks:
        response = "Ваши задачи:\n"
        for index, task in enumerate(tasks, start=1):
            status = "✔️" if task.completed else "❌"
            response += f"{index}. {task.text} - {status}\n"  # Нумерация задач для конкретного пользователя
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "У вас нет задач!")
    log_action(user_id, "listed tasks")

# Завершение задачи по номеру
def complete_task_step(message):
    try:
        task_number = int(message.text.strip())
        user_id = message.from_user.id
        db = next(get_db())  # Инициализация сессии
        
        tasks = db.query(Task).filter(Task.user_id == user_id).order_by(Task.id).all()
        
        if 1 <= task_number <= len(tasks):
            task = tasks[task_number - 1]
            if not task.completed:
                task.completed = True
                db.commit()
                bot.reply_to(message, f"Задача {task_number} отмечена как выполненная!")
                log_action(user_id, "completed task", f"ID {task.id}")
            else:
                bot.reply_to(message, f"Задача {task_number} уже выполнена.")
        else:
            bot.reply_to(message, "Неправильный номер задачи.")
    except ValueError:
        msg = bot.reply_to(message, "Пожалуйста, введите корректный номер задачи.")
        bot.register_next_step_handler(msg, complete_task_step)

# Удаление задачи по номеру
def delete_task_step(message):
    try:
        task_number = int(message.text.strip())
        user_id = message.from_user.id
        db = next(get_db())  # Инициализация сессии
        
        tasks = db.query(Task).filter(Task.user_id == user_id).order_by(Task.id).all()
        
        if 1 <= task_number <= len(tasks):
            task = tasks[task_number - 1]
            db.delete(task)
            db.commit()
            bot.reply_to(message, f"Задача {task_number} удалена!")
            log_action(user_id, "deleted task", f"ID {task.id}")
        else:
            bot.reply_to(message, "Неправильный номер задачи.")
    except ValueError:
        msg = bot.reply_to(message, "Пожалуйста, введите корректный номер задачи.")
        bot.register_next_step_handler(msg, delete_task_step)

# Редактирование задачи по номеру
def edit_task_step_number(message):
    try:
        task_number = int(message.text.strip())
        user_id = message.from_user.id
        db = next(get_db())  # Инициализация сессии
        
        tasks = db.query(Task).filter(Task.user_id == user_id).order_by(Task.id).all()
        
        if 1 <= task_number <= len(tasks):
            task = tasks[task_number - 1]
            bot.reply_to(message, "Введите новый текст для задачи:")
            bot.register_next_step_handler(message, edit_task_step_text, task.id)
        else:
            raise ValueError("Номер задачи не существует.")
    except ValueError:
        msg = bot.reply_to(message, "Введите корректный номер задачи.")
        bot.register_next_step_handler(msg, edit_task_step_number)

# Второй шаг — запрос нового текста для задачи
def edit_task_step_text(message, task_id):
    new_text = message.text.strip()
    db = next(get_db())  # Инициализация сессии

    if new_text:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.text = new_text
            db.commit()
            bot.reply_to(message, f"Текст задачи обновлен на: '{new_text}'")
            log_action(message.from_user.id, "edited task", f"ID {task_id} to '{new_text}'")
        else:
            bot.reply_to(message, "Задача не найдена.")
    else:
        msg = bot.reply_to(message, "Текст задачи не может быть пустым. Введите новый текст:")
        bot.register_next_step_handler(msg, edit_task_step_text, task_id)

# Запуск бота
bot.polling()
