class RequestApiError(Exception):
    """Ошибка при запросе к основному API."""

    pass


class HTTPStatusError(Exception):
    """Ошибка доступа к API, код ответа не 200."""

    pass


class JSONDecodeError(Exception):
    """Ошибка декодирования формата JSON."""

    pass


class ResponseAPIError(Exception):
    """Ошибка в ответе от сервера."""

    pass


class ResponseApiStatus(Exception):
    """Cтатус ответа от API."""

    pass


class InvalidTokenException(Exception):
    """Ошибка - доступность переменных окружения."""

    pass
