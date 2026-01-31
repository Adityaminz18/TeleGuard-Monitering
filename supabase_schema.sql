-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Users Table
create table users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  hashed_password text not null,
  referral_code_used text,
  is_verified boolean default false,
  role text default 'user', -- 'user' or 'admin'
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Referral Codes Table
create table referral_codes (
  code text primary key,
  created_by_user_id uuid references users(id),
  max_uses int default 10,
  used_count int default 0,
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Telegram Sessions Table
create table telegram_sessions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) not null,
  session_string text not null, -- Encrypted session string
  phone_number text,
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Alerts Table
create table alerts (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) not null,
  source_id bigint, -- Telegram Chat ID (NULL for global/all)
  source_name text, -- Friendly name for the source
  keywords text[], -- Array of keywords to match
  excluded_keywords text[], -- Array of keywords to exclude
  is_regex boolean default false,
  notify_email boolean default true,
  notify_bot boolean default false,
  webhook_url text,
  is_paused boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Alert Logs Table
create table alert_logs (
    id uuid primary key default uuid_generate_v4(),
    alert_id uuid references alerts(id),
    user_id uuid references users(id),
    message_content text,
    detected_keyword text,
    dispatched_to_email boolean,
    dispatched_to_bot boolean,
    dispatched_to_webhook boolean,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RLS Installation (Optional but recommended, kept simple for now)
alter table users enable row level security;
alter table telegram_sessions enable row level security;
alter table alerts enable row level security;
alter table alert_logs enable row level security;
