from pydantic import BaseModel

class TelegramAuthRequest(BaseModel):
    phone_number: str

class TelegramAuthResponse(BaseModel):
    phone_number: str
    phone_code_hash: str
    session_string: str  # Added to persist DC info
    message: str

class TelegramVerifyRequest(BaseModel):
    phone_number: str
    phone_code_hash: str
    session_string: str  # Added to persist DC info
    code: str
    code: str
    password: str | None = None  # 2FA password

class TelegramVerifyResponse(BaseModel):
    message: str
    session_id: str
