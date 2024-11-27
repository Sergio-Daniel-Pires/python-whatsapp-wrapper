class WhatsAppError (Exception):
    message: str

    def __init__(self, message: str):
        super().__init__()

        self.message = message

class VerificationFailed (WhatsAppError):
    ...

class MissingParameters (WhatsAppError):
    ...

class NotImplementedMsgType (WhatsAppError):
    ...

class UnknownEvent (WhatsAppError):
    ...

class EmptyState (WhatsAppError):
    ...
