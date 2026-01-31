# Deployment Guide

This project consists of two components that must be deployed separately for a production environment:

1.  **Backend API (FastAPI)**: Handles HTTP requests, dashboard, and database. Suitable for **Vercel**.
2.  **Worker (Telegram Client)**: Runs a persistent background loop. **CANNOT run on Vercel**. Must be deployed on **Railway, Heroku, Render, or a VPS**.

---

## 🚀 Part 1: Deploy API to Vercel

1.  **Install Vercel CLI** (Optional, or use the web dashboard):
    ```bash
    npm i -g vercel
    ```

2.  **Deploy**:
    Run the following command in the project root:
    ```bash
    vercel --prod
    ```
    *   Follow the prompts.
    *   Link to your existing Vercel project if you have one.

3.  **Environment Variables**:
    Go to your Vercel Project Dashboard > **Settings** > **Environment Variables** and add all variables from your `.env`:
    *   `POSTGRES_URL` (Use the "Pooler" URL from Supabase text to AWS, looks like `postgres://...:6543/postgres`)
    *   `SECRET_KEY`
    *   `TELEGRAM_API_ID`
    *   `TELEGRAM_API_HASH`
    *   `BOT_TOKEN`
    *   `SMTP_SERVER`, `SMTP_USER`, etc.

---

## ⚙️ Part 2: Deploy Worker (Railway/VPS)

Since Vercel functions time out after 10-60 seconds, they kill the Telegram client connection. You need a server that runs 24/7.

### Option A: Railway (Recommended)

1.  Create a new project on [Railway](https://railway.app/).
2.  Connect your GitHub repository.
3.  **Configure Service**:
    *   Railway will likely auto-detect the `Procfile`.
    *   By default, it might try to run the web server. You want it to run the **Worker**.
    *   Go to **Settings** > **Build/Start Command**.
    *   Set Start Command to: `python worker.py`
4.  **Environment Variables**:
    *   Copy the same `.env` variables to Railway.
5.  **Deploy**.

### Option B: VPS (Ubuntu/DigitalOcean)

1.  SSH into your server.
2.  Clone the repo:
    ```bash
    git clone <your-repo-url>
    cd TeleGuard
    ```
3.  Install dependencies:
    ```bash
    apt install python3-venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  Setup Systemd Service for Worker:
    `sudo nano /etc/systemd/system/teleguard-worker.service`
    ```ini
    [Unit]
    Description=TeleGuard Worker
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/path/to/TeleGuard
    ExecStart=/path/to/TeleGuard/venv/bin/python worker.py
    Restart=always
    EnvironmentFile=/path/to/TeleGuard/.env

    [Install]
    WantedBy=multi-user.target
    ```
5.  Start it:
    ```bash
    sudo systemctl enable teleguard-worker
    sudo systemctl start teleguard-worker
    ```

---

## 🔄 Status Check

*   **API**: Visit `https://your-vercel-app.vercel.app`. It should load the login page.
*   **Worker**: sending a message to the bot or checking `GET /api/v1/users/me` (after login) to see `telegram_connected: true`.
