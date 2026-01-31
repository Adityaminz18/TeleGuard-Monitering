# TeleGuard Alert System

**TeleGuard** is a multi-tenant web application designed to allow users to connect their personal Telegram accounts and configure automated alerts. Users can set specific "triggers" (keywords, specific senders) that, when detected in their Telegram chats, instantly send a notification via Email or a dedicated Telegram Bot.

## Executive Summary

The platform acts as a bridge between your active Telegram conversations and your need for immediate notifications. Gated by a referral system, it ensures a controlled user base. Whether monitoring for "breaking news" in a channel or waiting for a message from a specific client, TeleGuard listeners run 24/7 to keep you informed.

## Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python) - High-performance async framework.
- **Frontend:** Jinja2 Templates + [HTMX](https://htmx.org/) + TailwindCSS.
- **Database & Auth:** [Supabase](https://supabase.com/) (PostgreSQL + Auth).
- **Telegram Client:** [Telethon](https://docs.telethon.dev/en/stable/) (MTProto interaction).
- **Deployment:**
    - **Web/API:** Vercel (Serverless).
    - **Worker Node:** Persistent VPS (e.g., Railway, Heroku, DigitalOcean) for continuous listeners.

## Key Features

### A. User Authentication & Access Control
- **Referral-Gated Registration:** New users require a valid invite code.
- **Secure Login:** Email/Password authentication via Supabase.
- **Session Management:** Secure management of user sessions.

### B. Telegram Account Linking ("Pairing System")
- **Seamless Connection:** Connect via Phone Number (OTP) or QR Code scan.
- **Multi-Tenant:** Supports multiple distinct users and sessions securely stored in Supabase.

### C. Alert Configuration Engine
Define custom "Alert Rules" to filter noise and get notified only on what matters.
- **Source Selection:** Specific Chat, Group, Channel, or "All Incoming".
- **Trigger Conditions:**
    - **Keyword Match:** Detects specific text (e.g., "Urgent", "API Breaking").
    - **Sender Match:** specific user or bot ID.
- **Actions:**
    - Send Email.
    - Send Telegram Message (via the platform's Notification Bot).

### D. Notification Dispatcher
- **Email:** Direct alerts to your registered inbox.
- **Bot Message:** Forwarded alerts via the TeleGuard Alert Bot.

## System Architecture

### The "Listener" Problem & Solution
Vercel's serverless environment puts functions to sleep when idle, making it unsuitable for maintaining persistent connections required by Telegram's MTProto.

**The Hybrid Solution:**
1.  **Web Node (Vercel):** Hosts the Dashboard, API, and Database interactions.
2.  **Worker Node (VPS):** A lightweight, persistent Python script that:
    - Loads active sessions from Supabase.
    - Listens for `events.NewMessage`.
    - Matches messages against Alert Rules.
    - Dispatches notifications.

### Data Schema (Supabase)
- **`users`**: User credentials and profile.
- **`referral_codes`**: Access control management.
- **`telegram_sessions`**: Encrypted Telethon session strings.
- **`alerts`**: User-defined rules and triggers.

## Roadmap

### Phase 1: Setup & Auth
- [ ] FastAPI structure & Supabase init.
- [ ] User Registration (Referral check) & Login.

### Phase 2: Frontend
- [ ] Landing Page & Dashboard with Jinja2 + Tailwind.
- [ ] Alert Management UI.

### Phase 3: Telegram Integration
- [ ] Account Linking (OTP & QR flows).
- [ ] Session string encryption & storage.

### Phase 4: The Worker
- [ ] Standalone listener script `worker.py`.
- [ ] Telethon client pooling.
- [ ] Event filtering & Dispatcher logic.

### Phase 5: Deployment
- [ ] Vercel deployment for Web.
- [ ] VPS/Railway deployment for Worker.

## Usage

1.  **Register:** obtain a referral code and create an account.
2.  **Connect:** Link your Telegram account via the dashboard.
3.  **Configure:** Set up keywords to watch for.
4.  **Listen:** The system runs in the background and notifies you of matches.
