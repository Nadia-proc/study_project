"""Ошибки приложения."""


class TrainerError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class VerbNotFound(TrainerError):
    status_code = 404

    def __init__(self, infinitive: str):
        super().__init__(f"Глагол «{infinitive}» не найден")
