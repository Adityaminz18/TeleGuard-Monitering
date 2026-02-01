import asyncio
import logging
import re
import smtplib
from email.message import EmailMessage
import ssl
from typing import List, Dict

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.db.session import engine, AsyncSession
from app.models import TelegramSession, Alert, AlertLog

from app.db.session import engine, AsyncSession
from app.models import TelegramSession, Alert, AlertLog
from app.core.config import settings

# Bot Client
bot_client = None 

async def get_bot_client():
    global bot_client
    if not settings.BOT_TOKEN:
        return None
        
    if bot_client is None:
        # Use StringSession() to keep it in-memory and avoid "database is locked" errors
        # This makes the bot stateless (perfect for tokens) and prevents file conflicts.
        bot_client = TelegramClient(StringSession(), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
        await bot_client.start(bot_token=settings.BOT_TOKEN)
    return bot_client

# Configure Logging
logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("worker")

# Store active clients
active_clients: Dict[str, TelegramClient] = {}
processed_messages = set()

async def fetch_active_sessions():
    """Fetch all active sessions from DB."""
    async with AsyncSession(engine) as session:
        statement = select(TelegramSession).where(TelegramSession.is_active == True)
        result = await session.execute(statement)
        return result.scalars().all()

async def fetch_user_alerts(user_id):
    """Fetch alerts for a specific user."""
    async with AsyncSession(engine) as session:
        statement = select(Alert).where(Alert.user_id == user_id).where(Alert.is_paused == False)
        result = await session.execute(statement)
        return result.scalars().all()

async def log_alert(alert_id, user_id, message_content, dispatched_email, dispatched_bot):
    async with AsyncSession(engine) as session:
        log_entry = AlertLog(
            alert_id=alert_id,
            user_id=user_id,
            message_content=message_content,
            detected_keyword="match",
            dispatched_to_email=dispatched_email,
            dispatched_to_bot=dispatched_bot
        )
        session.add(log_entry)
        await session.commit()

async def notification_handler(event, user_id: str):
    """
    Callback triggered on every new message for a specific user.
    """
    try:
        alerts = await fetch_user_alerts(user_id)
        if not alerts:
            return

        message_text = event.message.message or ""
        sender = await event.get_sender()
        sender_username = getattr(sender, 'username', 'Unknown')
        chat_id = event.chat_id
        msg_id = event.message.id
        
        # Deduplication Check
        # specific_key = (chat_id, msg_id)
        # We need a global cache. For now, let's use a simple per-worker set.
        if (chat_id, msg_id) in processed_messages:
            return
        processed_messages.add((chat_id, msg_id))
        
        # Cleanup cache if too big
        if len(processed_messages) > 5000:
            processed_messages.clear()
        
        logger.info(f"Processing Msg for User {user_id} | Chat: {chat_id} | Sender: {sender_username} | Text: {message_text[:30]}...")
        
        for alert in alerts:
            # 0. Global Filters (Self-Chat, Bot Messages, Outgoing)
            # Ignore own outgoing messages (prevents self-chat loops and monitoring own speech)
            if event.out:
                continue

            # Ignore messages from our own Bot (prevents alert loops)
            # Robust Check: Compare Sender ID with Global BOT_ID
            sender_id = sender.id if sender else None
            if BOT_ID and sender_id and sender_id == BOT_ID:
                continue
            
            # Fallback Text Check (if BOT_ID failed to fetch)
            if message_text.startswith("🚨 TeleGuard Alert") or "TeleGuard Alert Triggered" in message_text:
                continue

            # 1. Source Check
            if alert.source_id and alert.source_id != chat_id:
                continue

            # 2. Content Matching
            match_found = False
            keywords = alert.keywords or []
            excluded = alert.excluded_keywords or []
            is_regex = alert.is_regex
            
            # Match Logic
            text_lower = message_text.lower()
            
            # A. Check Excluded (Fail fast)
            exclude_hit = False
            for exc in excluded:
                if exc and exc.lower() in text_lower:
                    exclude_hit = True
                    break
            if exclude_hit:
                continue

            # B. Check Triggers
            if is_regex:
                for pat in keywords:
                    try:
                         # Regex match
                        if re.search(pat, message_text, re.IGNORECASE):
                            match_found = True
                            break
                    except Exception as e:
                        logger.error(f"Invalid Regex {pat}: {e}")
            else:
                # Standard Keyword Match
                for kw in keywords:
                    if kw and kw.lower() in text_lower:
                        match_found = True
                        break

            if match_found:
                logger.info(f"MATCH FOUND for User {user_id}! Trigger: {keywords}")
                await dispatch_notification(alert, message_text, sender_username)

    except Exception as e:
        logger.error(f"Error in handler for {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in handler for {user_id}: {e}")


def generate_email_html(keyword_str, from_user, message_text):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            .header {{ background: linear-gradient(to right, #4f46e5, #6366f1); padding: 24px; text-align: center; color: white; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 32px; color: #374151; }}
            .badge {{ display: inline-block; background: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 9999px; font-size: 14px; font-weight: 600; margin-right: 4px; }}
            .message-box {{ background: #f9fafb; border-left: 4px solid #6366f1; padding: 16px; margin: 20px 0; border-radius: 4px; font-style: italic; color: #4b5563; }}
            .footer {{ background: #f9fafb; padding: 16px; text-align: center; font-size: 12px; color: #9ca3af; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TeleGuard Alert 🚨</h1>
            </div>
            <div class="content">
                <p style="font-size: 16px; margin-bottom: 24px;">
                    An alert was triggered for the following keywords:
                </p>
                <div style="margin-bottom: 24px;">
                    {''.join(f'<span class="badge">{k.strip()}</span>' for k in keyword_str.split(','))}
                </div>
                
                <p><strong>From:</strong> @{from_user}</p>
                
                <div class="message-box">
                    "{message_text}"
                </div>
                
                <p style="font-size: 14px; color: #6b7280;">
                    Visit your dashboard to manage your listeners.
                </p>
            </div>
            <div class="footer">
                &copy; 2024 TeleGuard Monitoring System
            </div>
        </div>
    </body>
    </html>
    """

def generate_bot_message(keyword_str, from_user, message_text, alert_id):
    # Telegram HTML styling
    return (
        f"<b>🚨 TeleGuard Alert Triggered!</b>\n\n"
        f"🔑 <b>Keywords:</b> <code>{keyword_str}</code>\n"
        f"👤 <b>From:</b> @{from_user}\n\n"
        f"💬 <b>Message:</b>\n"
        f"<blockquote>{message_text}</blockquote>\n\n"
        f"<i>ID: {alert_id}</i>"
    )

async def send_email_notification(to_email, subject, content, html_content=None):
    if not settings.SMTP_SERVER or not settings.SMTP_USER:
        logger.warning("SMTP not configured, skipping email.")
        return

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = settings.EMAILS_FROM_EMAIL or "noreply@tele-guard.com"
        msg['To'] = to_email
        msg.set_content(content) # Fallback text
        
        if html_content:
            msg.add_alternative(html_content, subtype='html')

        # Run blocking SMTP in thread
        def _send():
            # ZeptoMail Logic
            if settings.SMTP_PORT == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                # Default to 587 flow
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
        
        await asyncio.to_thread(_send)
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

async def send_bot_notification(telegram_id, content):
    try:
        bot = await get_bot_client()
        if not bot:
            logger.warning("Bot token not configured.")
            return False
            
        await bot.send_message(int(telegram_id), content, parse_mode='html')
        logger.info(f"Bot message sent to {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send bot message: {e}")
        return False

async def dispatch_notification(alert, message_text, from_user):
    logger.info("========================================")
    logger.info(f"ALERT TRIGGERED: {alert.id}")
    logger.info(f"From: {from_user}")
    logger.info(f"Content: {message_text}")
    logger.info("========================================")
    
    dispatched_email = False
    dispatched_bot = False
    
    # Fetch user email/telegram_id if needed
    async with AsyncSession(engine) as session:
        # Re-fetch alert with user to get email
        # Ideally we fetch this in initial query, but for now:
        stmt = select(TelegramSession).where(TelegramSession.user_id == alert.user_id).where(TelegramSession.is_active == True)
        res = await session.execute(stmt)
        tg_session = res.scalars().first()
        
        # User email is on user object, let's assume we have it or fetch it
        from app.models import User
        user_stmt = select(User).where(User.id == alert.user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

    logger.info(f"DISPATCH DEBUG: AlertID={alert.id} | NotifyEmail={alert.notify_email} | NotifyBot={alert.notify_bot}")
        
    keyword_str = ", ".join(alert.keywords)
    
    # Generate Notifications
    text_body = f"Alert triggered for keywords: {keyword_str}\n\nSender: {from_user}\nMessage: {message_text}"
    html_body = generate_email_html(keyword_str, from_user, message_text)
    bot_body = generate_bot_message(keyword_str, from_user, message_text, str(alert.id)[:8])

    if alert.notify_email and user and user.email:
        logger.info(f"Dispatching email to {user.email}")
        dispatched_email = await send_email_notification(
            user.email, 
            f"🚨 TeleGuard Alert: {keyword_str}", 
            text_body, 
            html_content=html_body
        )
    else:
        logger.warning("Skipping Email: Condition failed (Check NotifyEmail flag, User existence, or Email presence)")

    target_chat_id = None
    if alert.notify_bot:
        if user and user.bot_chat_id:
             target_chat_id = user.bot_chat_id
        elif tg_session and tg_session.telegram_id:
             target_chat_id = tg_session.telegram_id

    if target_chat_id:
        logger.info(f"Dispatching bot msg to {target_chat_id}")
        dispatched_bot = await send_bot_notification(target_chat_id, bot_body)
    
    # Log to DB
    try:
        alert.trigger_count += 1
        # access session again to save
        async with AsyncSession(engine) as session:
             # re-attach to session
             a = await session.get(Alert, alert.id)
             if a:
                 a.trigger_count += 1
                 session.add(a)
                 await session.commit()

        await log_alert(alert.id, alert.user_id, message_text[:500], dispatched_email, dispatched_bot)
    except Exception as e:
        logger.error(f"Failed to log alert or update count: {e}")


# Global Bot ID
BOT_ID = None

async def init_bot_identity():
    """Fetch and store the Bot ID once."""
    global BOT_ID
    try:
        if settings.BOT_TOKEN:
             client = await get_bot_client()
             if client:
                 me = await client.get_me()
                 BOT_ID = me.id
                 logger.info(f"Bot Identity Initialized: {me.username} (ID: {BOT_ID})")
    except Exception as e:
        logger.error(f"Failed to fetch Bot Identity: {e}")

async def sync_user_dialogs(client, user_id):
    """Syncs the user's dialogs (chats) to the database."""
    try:
        from app.models import TelegramChat
        dialogs = await client.get_dialogs(limit=50)
        
        async with AsyncSession(engine) as session:
            # Clear existing? Or Upsert. Let's clear for simplicity as it's a sync.
            # But clearing might flap the UI. Better to Upsert.
            # Actually, deleting all for user is safest for "sync" to remove deleted chats.
            stmt = select(TelegramChat).where(TelegramChat.user_id == user_id)
            res = await session.execute(stmt)
            existing = res.scalars().all()
            for e in existing:
                await session.delete(e)
            
            for d in dialogs:
                chat_type = "Group" if d.is_group else "Channel" if d.is_channel else "User"
                username = getattr(d.entity, 'username', None)
                new_chat = TelegramChat(
                    id=d.id,
                    user_id=user_id,
                    title=d.title or "Unknown",
                    type=chat_type,
                    username=username
                )
                session.add(new_chat)
            await session.commit()
            logger.info(f"Synced {len(dialogs)} dialogs for user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync dialogs for {user_id}: {e}")

async def start_user_client(session_data):
    """Start a Telethon client for a session."""
    user_id = str(session_data.user_id)
    if user_id in active_clients:
        return 
    
    logger.info(f"Starting client for user {user_id}")
    
    # Optimistic lock to prevent race conditions
    active_clients[user_id] = "initializing"
    
    try:
        client = TelegramClient(
            StringSession(session_data.session_string),
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
        
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"Session invalid for user {user_id}")
            async with AsyncSession(engine) as session:
                stmt = select(TelegramSession).where(TelegramSession.user_id == session_data.user_id).where(TelegramSession.is_active == True)
                res = await session.execute(stmt)
                db_session = res.scalars().first()
                if db_session:
                    db_session.is_active = False
                    session.add(db_session)
                    await session.commit()
            return

        @client.on(events.NewMessage)
        async def handler(event):
            # Pass identity down
            await notification_handler(event, user_id)

        active_clients[user_id] = client
        logger.info(f"Client started for {user_id}")
        
        # Initial Sync
        asyncio.create_task(sync_user_dialogs(client, user_id))
        
    except Exception as e:
        error_str = str(e)
        if "used under two different IP addresses" in error_str or "AuthKeyDuplicatedError" in error_str:
             logger.error(f"Session REVOKED for {user_id}: {e}")
             # Invalidate in DB
             async with AsyncSession(engine) as session:
                stmt = select(TelegramSession).where(TelegramSession.user_id == session_data.user_id).where(TelegramSession.is_active == True)
                res = await session.execute(stmt)
                db_session = res.scalars().first()
                if db_session:
                    db_session.is_active = False
                    session.add(db_session)
                    await session.commit()
             # Remove from active clients if present
             if user_id in active_clients:
                 del active_clients[user_id]
             return

        logger.error(f"Failed to start client for {user_id}: {e}")
async def setup_bot_commands(bot):
    """
    Registers command handlers for the Bot.
    """
    logger.info("Setting up Bot Commands...")

    @bot.on(events.NewMessage)
    async def debug_handler(event):
        logger.info(f"BOT DEBUG: Received msg from {event.sender_id}: {event.text}")

    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        sender_id = event.sender_id
        async with AsyncSession(engine) as session:
            # Try to associate
            # 1. Check TelegramSession (Best for finding linked Account)
            stmt = select(TelegramSession).where(TelegramSession.telegram_id == str(sender_id))
            res = await session.execute(stmt)
            tg_session = res.scalars().first()
            
            user = None
            if tg_session:
                 from app.models import User
                 user = await session.get(User, tg_session.user_id)
            
            # 2. If not found, check User.bot_chat_id
            if not user:
                from app.models import User
                stmt = select(User).where(User.bot_chat_id == sender_id)
                res = await session.execute(stmt)
                user = res.scalars().first()
            
            if user:
                 # Ensure bot_chat_id is set
                 if not user.bot_chat_id or user.bot_chat_id != sender_id:
                     user.bot_chat_id = sender_id
                     session.add(user)
                     await session.commit()
                 
                 await event.respond(f"👋 Welcome back, {user.full_name or 'User'}!\n\nYour account is linked. You can manage alerts here.\n\n<b>Commands:</b>\n/list - View active alerts\n/add &lt;word&gt; [@user] - Add listener\n<i>(e.g. /add bitcoin @elonmusk)</i>\n/del &lt;id&gt; - Delete listener", parse_mode='html')
            else:
                 await event.respond("👋 Welcome to TeleGuard!\n\nI couldn't find your account. Please Login to the Dashboard first and duplicate your Telegram connection, or ensure your IDs match.")

    @bot.on(events.NewMessage(pattern='/add (.+)'))
    async def add_handler(event):
        raw_args = event.pattern_match.group(1).strip().split()
        
        # 1. Parse Flags
        flags = {t.lower() for t in raw_args if t.startswith('-')}
        # 2. Parse Positional Args (Keyword, Username)
        clean_args = [t for t in raw_args if not t.startswith('-')]
        
        if not clean_args:
             await event.respond("❌ Please provide a keyword.\nUsage: <code>/add &lt;word&gt; [@user] [-email] [-bot]</code>", parse_mode='html')
             return

        keyword = clean_args[0]
        target_username = clean_args[1] if len(clean_args) > 1 else None
        
        # 3. Determine Notifications
        # If specific flags are used, valid only them. Otherwise default to BOTH.
        has_flags = ('-email' in flags or '-bot' in flags)
        notify_email = '-email' in flags if has_flags else True
        notify_bot = '-bot' in flags if has_flags else True

        sender_id = event.sender_id
        
        async with AsyncSession(engine) as session:
            # Auth
            stmt = select(TelegramSession).where(TelegramSession.telegram_id == str(sender_id))
            res = await session.execute(stmt)
            tg_session = res.scalars().first()
            
            if not tg_session: 
                 await event.respond("❌ You are not linked. Please login to dashboard.")
                 return

            # Resolve Target (if provided)
            source_id = None
            source_name = "All Chats"
            
            if target_username:
                target_username = target_username.lstrip('@')
                from app.models import TelegramChat
                # Case insensitive search
                stmt = select(TelegramChat).where(TelegramChat.user_id == tg_session.user_id)
                res = await session.execute(stmt)
                chats = res.scalars().all()
                
                found_chat = None
                for c in chats:
                    if c.username and c.username.lower() == target_username.lower():
                        found_chat = c
                        break
                
                if found_chat:
                    source_id = found_chat.id
                    source_name = f"@{found_chat.username}"
                else:
                    await event.respond(f"❌ Could not find chat <b>@{target_username}</b> in your synced dialogs.\n\nPlease ensure you have chatted with them recently and the dashboard is synced.", parse_mode='html')
                    return

            # Create Alert
            from app.models import Alert
            new_alert = Alert(
                user_id=tg_session.user_id,
                keywords=[keyword],
                source_id=source_id,
                source_name=source_name,
                notify_bot=notify_bot,
                notify_email=notify_email
            )
            session.add(new_alert)
            await session.commit()
            await session.refresh(new_alert)
            
            # Formatting response
            target_display = source_name
            chans = []
            if notify_bot: chans.append("Bot 🤖")
            if notify_email: chans.append("Email 📧")
            chan_str = " + ".join(chans)
            
            await event.respond(f"✅ <b>Alert Added!</b>\n\n🔑 Keyword: <code>{keyword}</code>\n🎯 Source: <code>{target_display}</code>\n📢 Notify: <b>{chan_str}</b>\n🆔 ID: <code>{new_alert.id}</code>", parse_mode='html')

    @bot.on(events.NewMessage(pattern='/list'))
    async def list_handler(event):
        sender_id = event.sender_id
        async with AsyncSession(engine) as session:
            stmt = select(TelegramSession).where(TelegramSession.telegram_id == str(sender_id))
            res = await session.execute(stmt)
            tg_session = res.scalars().first()
            
            if not tg_session: 
                 await event.respond("❌ Auth failed.")
                 return
            
            from app.models import Alert
            stmt = select(Alert).where(Alert.user_id == tg_session.user_id).where(Alert.is_paused == False)
            res = await session.execute(stmt)
            alerts = res.scalars().all()
            
            if not alerts:
                await event.respond("📭 No active alerts. Use /add <keyword> to create one.")
                return
            
            msg = "<b>📋 Active Listeners:</b>\n\n"
            for a in alerts:
                kws = ", ".join(a.keywords)
                msg += f"• {kws} (ID: <code>{str(a.id)[:8]}</code>)\n"
            
            await event.respond(msg, parse_mode='html')

    @bot.on(events.NewMessage(pattern='/del (.+)'))
    async def del_handler(event):
        alert_id_fragment = event.pattern_match.group(1).strip()
        sender_id = event.sender_id
        
        async with AsyncSession(engine) as session:
            stmt = select(TelegramSession).where(TelegramSession.telegram_id == str(sender_id))
            res = await session.execute(stmt)
            tg_session = res.scalars().first()
            
            if not tg_session: return

            from app.models import Alert
            stmt = select(Alert).where(Alert.user_id == tg_session.user_id)
            res = await session.execute(stmt)
            alerts = res.scalars().all()
            
            target = None
            for a in alerts:
                if str(a.id).startswith(alert_id_fragment):
                    target = a
                    break
            
            if target:
                # Capture data before deletion
                kws_display = str(target.keywords)
                
                # Delete associated logs (Manual Cascade)
                # Delete associated logs (Manual Cascade)
                from app.models import AlertLog
                from sqlmodel import delete
                await session.execute(delete(AlertLog).where(AlertLog.alert_id == target.id))
                
                await session.delete(target)
                await session.commit()
                await event.respond(f"🗑 Alert <code>{kws_display}</code> deleted.", parse_mode='html')
            else:
                await event.respond(f"❌ Alert ID <code>{alert_id_fragment}</code> not found.", parse_mode='html')


async def main():
    logger.info("Worker started. monitoring sessions...")
    
    # 1. Initialize Bot Identity for filtering
    await init_bot_identity()

    # 1.5 Setup Bot Commands
    if bot_client:
        await setup_bot_commands(bot_client)

    while True:
        sessions = await fetch_active_sessions()
        
        for session in sessions:
            user_id_str = str(session.user_id)
            if user_id_str not in active_clients:
                asyncio.create_task(start_user_client(session))
            else:
                # 2. Auto-Reconnect & Health Check
                client = active_clients[user_id_str]
                
                # Skip if still initializing
                if client == "initializing":
                     continue
                
                try:
                    # A. Check internal flag
                    if not client.is_connected():
                        raise ConnectionError("Client is_connected() returned False")

                    # B. Active Heartbeat (Real test of the pipe)
                    # We check this to detect "Zombie" connections where the server kicked us but client thinks it's alive.
                    # We accept the overhead of 1 request every 5s for stability.
                    try:
                        await asyncio.wait_for(client.get_me(), timeout=5.0)
                    except Exception as heartbeat_err:
                         raise ConnectionError(f"Heartbeat failed: {heartbeat_err}")
                         
                except Exception as e:
                    logger.warning(f"Client {user_id_str} connection issue: {e}. Reinitializing...")
                    try:
                        # 1. Try to close silently
                        await client.disconnect()
                    except: 
                        pass
                    
                    # 2. Re-connect
                    try:
                        await client.connect()
                        if not await client.is_user_authorized():
                             logger.warning(f"Session invalidated for {user_id_str}. Removing.")
                             async with AsyncSession(engine) as session:
                                stmt = select(TelegramSession).where(TelegramSession.user_id == user_id_str).where(TelegramSession.is_active == True)
                                res = await session.execute(stmt)
                                db_session = res.scalars().first()
                                if db_session:
                                    db_session.is_active = False
                                    session.add(db_session)
                                    await session.commit()
                             del active_clients[user_id_str]
                        else:
                             logger.info(f"Client {user_id_str} recovered successfully.")
                    except Exception as recon_err:
                        logger.error(f"Recovery failed for {user_id_str}: {recon_err}")
                        # 3. Last Resort: Nuke from memory so it gets recreated from scratch next loop
                        del active_clients[user_id_str]

        # Optimize polling for faster responsiveness
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
