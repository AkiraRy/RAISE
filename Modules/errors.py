from enum import Enum


class ErrorType(Enum):
    HOST_FAULT = 1
    WHISPER_FAULT = 2


def handle_error(error_type, value) -> tuple:
    if not isinstance(error_type, ErrorType):
        raise ValueError("Invalid error type. Must be an instance of ErrorType enum.")

    if error_type == ErrorType.HOST_FAULT:
        return (f"Invalid value '{value}' for Host, Please check the box or paste correct HOST",
                f'Host value error')
    elif error_type == ErrorType.WHISPER_FAULT:
        return (f"Invalid value '{value}' for Whisper_Host, Please check the box or paste correct Whisper_HOST",
                f'Whisper host value error')
    print("Unknown error type.")
