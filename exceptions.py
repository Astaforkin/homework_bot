class RequestApiError(Exception):
    """Ошибка при запросе к основному API."""


class HTTPStatusError(Exception):
    """Ошибка доступа к API, код ответа не 200."""


class JSONDecodeError(Exception):
    """Ошибка декодирования формата JSON."""


class ResponseAPIError(Exception):
    """Ошибка в ответе от сервера."""


class ResponseApiStatus(Exception):
    """Cтатус ответа от API."""


class InvalidTokenException(Exception):
    """Ошибка - доступность переменных окружения."""


class EmptyListExc(Exception):
    """Исключение - статус работы не изменился."""
