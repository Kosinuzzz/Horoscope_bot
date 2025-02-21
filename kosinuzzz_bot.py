from dotenv import load_dotenv
from googletrans import Translator
import os
import telebot
import requests
import re  # Добавляем импорт модуля re для работы с регулярными выражениями
import logging  # Импортируем модуль logging

load_dotenv()  # Загружаем переменные из .env
token = os.getenv("TELEGRAM_BOT_TOKEN")  # Получаем токен бота из переменных окружения

if not token:
    raise ValueError("Не удалось получить токен Telegram. Проверьте файл .env.")  # Проверка наличия токена

bot = telebot.TeleBot(token)  # Инициализация бота с токеном

# Настраиваем базовую конфигурацию логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bot.log', filemode='a')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я корги-астролог. \nПиши /horoscope и узнай свой гороскоп.")  # Ответ на команду /start

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Вот список доступных команд: /start, /help, /horoscope, /tatka")  # Ответ на команду /help

@bot.message_handler(commands=['tatka'])
def send_tatka_message(message):
    bot.reply_to(message, "Привет, Татка=))")  # Ответ на команду /tatka

@bot.message_handler(commands=['horoscope'])
def sign_handler(message):
    text = "Какой ты знак зодиака?\nВведи по-английски: *Aries*, *Taurus*, *Gemini*, *Cancer,* *Leo*, *Virgo*, *Libra*, *Scorpio*, *Sagittarius*, *Capricorn*, *Aquarius*, and *Pisces*."
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")  # Запрос знака зодиака
    bot.register_next_step_handler(sent_msg, day_handler)  # Переход к следующему шагу без проверки

def day_handler(message):
    sign = message.text.capitalize()  # Предполагаем, что пользователь ввел корректный знак
    sent_msg = bot.send_message(
        message.chat.id, "Введите день: TODAY, TOMORROW, YESTERDAY или дату в формате YYYY-MM-DD.", parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, fetch_horoscope, sign)  # Переход к получению гороскопа

def fetch_horoscope(message, sign):
    day = message.text
    horoscope = get_daily_horoscope(sign, day)  # Получение гороскопа
    if not horoscope or "error" in horoscope:
        bot.send_message(message.chat.id, "Проблема с источником гороскопа. Проверь введенные данные и попробуй позже.")
        return

    data = horoscope.get("data")
    if not data:
        bot.send_message(message.chat.id, "Ошибка в данных гороскопа. Проверь введенные данные и попробуй позже.")
        return

    # Создаем объект Translator
    translator = Translator()
    
    # Переводим текст гороскопа на русский
    translated_horoscope = translator.translate(data.get("horoscope_data", ""), dest='ru').text
    
    horoscope_message = f'{translated_horoscope}\n*Знак зодиака:* {sign}\n*День:* {data.get("date", "")}'
    bot.send_message(message.chat.id, "Вот твой гороскоп!")  # Отправка сообщения с гороскопом
    bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")

def get_daily_horoscope(sign: str, day: str) -> dict:
    """Get daily horoscope for a zodiac sign.
    Keyword arguments:
    sign:str - Zodiac sign
    day:str - Date in format (YYYY-MM-DD) OR TODAY OR TOMORROW OR YESTERDAY
    Return:dict - JSON data
    """
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    try:
        response = requests.get(url, params, timeout=15)  # Установлен таймаут в 15 секунд
        return response.json()
    except requests.Timeout:
        return {"error": "timeout"}
    except requests.RequestException:
        return {}

@bot.message_handler(func=lambda message: True)
def log_all_messages(message):
    # Логируем сообщение
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")
    bot.reply_to(message, "Ваше сообщение было получено и записано в лог.")  # Ответ на любое сообщение

try:
    bot.polling()  # Запуск бота
except Exception:
    pass