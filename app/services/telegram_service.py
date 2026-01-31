import logging
from telethon import TelegramClient, sessions
from telethon.errors import SessionPasswordNeededError
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.api_id = settings.TELEGRAM_API_ID
        self.api_hash = settings.TELEGRAM_API_HASH
        
        if not self.api_id or not self.api_hash:
            logger.warning("Telegram API credentials no set in settings")

    async def send_code(self, phone_number: str):
        """
        Connects to Telegram, sends a code request, and returns (phone_code_hash, session_string).
        We MUST return the session string to persist Data Center information.
        """
        client = TelegramClient(sessions.StringSession(), self.api_id, self.api_hash)
        await client.connect()
        
        try:
            sent_code = await client.send_code_request(phone_number)
            return sent_code.phone_code_hash, client.session.save()
        finally:
            await client.disconnect()

    async def verify_code(self, phone_number: str, code: str, phone_code_hash: str, session_string: str, password: str = None):
        """
        Connects, completes the login with code/hash, and returns the StringSession.
        """
        client = TelegramClient(sessions.StringSession(session_string), self.api_id, self.api_hash)
        await client.connect()
        
        try:
            try:
                await client.sign_in(phone=phone_number, code=code, phone_code_hash=phone_code_hash)
            except SessionPasswordNeededError:
                if not password:
                    raise ValueError("2FA Password required")
                await client.sign_in(password=password)
            
            # Login successful, export session string
            session_string = client.session.save()
            user = await client.get_me()
            return session_string, user.id, user.username
        finally:
            await client.disconnect()

    async def get_dialogs(self, session_string: str, limit: int = 20):
        """
        Fetch recent dialogs (chats) for the user.
        """
        client = TelegramClient(sessions.StringSession(session_string), self.api_id, self.api_hash)
        await client.connect()
        
        try:
            if not await client.is_user_authorized():
                raise ValueError("Session invalid or expired")
                
            dialogs = await client.get_dialogs(limit=limit)
            results = []
            for d in dialogs:
                chat_type = "Group" if d.is_group else "Channel" if d.is_channel else "User"
                results.append({
                    "id": d.id,
                    "title": d.title or "Unknown",
                    "type": chat_type
                })
            return results
        finally:
            await client.disconnect()

telegram_service = TelegramService()
