import os
import time
import logging
from logging.handlers import RotatingFileHandler
from http import HTTPStatus


import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    RequestApiError, HTTPStatusError, JSONDecodeError,
    ResponseAPIError, ResponseApiStatus, InvalidTokenException

)

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_logger.log',
                              encoding='UTF-8',
                              maxBytes=50000000,
                              backupCount=5
                              )
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(funcName)s, %(lineno)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.
    Которые необходимы для работы программы.
    Если отсутствует хотя бы одна переменная окружения -
    возвращает False.
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.
    Чат задан переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса Bot и
    строку с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(
            f'Бот отправил сообщение в чат {TELEGRAM_CHAT_ID}: {message}'
        )
    except telegram.TelegramError as error:
        logger.error(
            f'Ошибка отправки сообщения в телеграм: {error}'
        )


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    timestamp = int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        raise RequestApiError(f'Ошибка при запросе к основному API: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        status_code = homework_statuses.status_code
        logging.error(f'Ответ API: {status_code}')
        raise HTTPStatusError(
            f'Ошибка доступа к API, код ответа: {status_code}'
        )
    try:
        return homework_statuses.json()
    except JSONDecodeError as error:
        logger.error(f'Ошибка декодирования формата JSON: {error}')
        raise JSONDecodeError(f'Ошибка декодирования формата JSON: {error}')


def check_response(response: dict) -> dict:
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API, приведенный к типам
    данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise ResponseAPIError('Ошибка словаря по ключу homeworks')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком')
    if not homeworks:
        raise ResponseApiStatus('Новых статусов нет')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает всего один элемент из списка домашних
    работ. В случае успеха, функция возвращает подготовленную для отправки в
    Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    """
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ResponseApiStatus(
            f'Неизвестный статус работы: {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют одна или несколько переменных окружения')
        raise InvalidTokenException(
            'Отсутствуют одна или несколько переменных окружения'
        )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''
    last_error = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            status = parse_status(homeworks[0])
            if status != last_status:
                send_message(bot, status)
                last_status = status
            else:
                logger.info('В ответе отсутствуют новые статусы работ')
            timestamp = response['current_date']
        except (ResponseAPIError, TypeError, KeyError) as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_error:
                send_message(bot, message)
                last_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
