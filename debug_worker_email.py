import asyncio
import logging
from worker import send_email_notification
from app.core.config import settings

# Configure basic logging to see output
logging.basicConfig(level=logging.INFO)

async def test_worker_email():
    print("--- Testing worker.py send_email_notification ---")
    to_email = "adityaminz18@gmail.com"
    subject = "Debug: Worker Email Function"
    content = "This email was sent by importing the ACTUAL function from worker.py"
    
    print(f"Attempting to send to {to_email}...")
    success = await send_email_notification(to_email, subject, content)
    
    if success:
        print("✅ Success! The function in worker.py works correctly.")
    else:
        print("❌ Failed! The function in worker.py returned False. Check logs above.")

if __name__ == "__main__":
    asyncio.run(test_worker_email())
