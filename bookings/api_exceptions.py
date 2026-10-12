from rest_framework import status
from rest_framework.exceptions import APIException


class SlotUnavailable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "slot_unavailable"
    default_detail = "Это время уже занято. Выберите другой слот."

    def __init__(self):
        self.detail = {
            "code": "slot_unavailable",
            "detail": "Это время уже занято. Выберите другой слот.",
        }
