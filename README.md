# Voss CRM

A lightweight personal CRM to track prospects, clients, deals, and follow-ups. Accessible from phone and laptop, with LinkedIn capture, Telegram alerts, and AI-powered email drafts.

## Architecture

- **Backend**: Python/FastAPI on Render
- **Frontend**: React + TypeScript + Tailwind + shadcn/ui on Netlify
- **Storage**: Google Sheets (via gspread)
- **Alerts**: Telegram bot with scheduled notifications
- **Email drafts**: Claude API
- **LinkedIn capture**: Chrome extension (Manifest V3)

## Setup

### 1. Google Cloud Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to IAM → Service Accounts → Create Service Account
5. Download the JSON key file
6. Create a Google Sheet with these tabs (first row = headers):
   - **Contacts**: `id`, `company_id`, `first_name`, `last_name`, `email`, `phone`, `role`, `linkedin_url`, `urls`, `source`, `referral_contact_id`, `tags`, `notes`, `status`, `created_at`, `updated_at`
   - **Companies**: `id`, `name`, `industry`, `website`, `size`, `notes`, `created_at`, `updated_at`
   - **Deals**: `id`, `contact_id`, `company_id`, `title`, `stage`, `value`, `currency`, `priority`, `expected_close`, `notes`, `created_at`, `updated_at`
   - **Interactions**: `id`, `contact_id`, `deal_id`, `type`, `subject`, `body`, `url`, `direction`, `occurred_at`, `created_at`
   - **FollowUps**: `id`, `contact_id`, `deal_id`, `title`, `due_date`, `due_time`, `status`, `reminder_sent`, `notes`, `created_at`, `completed_at`
   - **Users**: `id`, `username`, `password_hash`, `telegram_chat_id`, `created_at`
7. Share the sheet with the service account email (Editor access)
8. Copy the Sheet ID from the URL

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials:
#   GOOGLE_SHEETS_CREDENTIALS_JSON (paste the entire JSON key)
#   GOOGLE_SHEET_ID
#   JWT_SECRET_KEY (generate a random string)
#   INVITE_CODE (for user registration)
#   ANTHROPIC_API_KEY (for email drafts)

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm install
npm run dev
```

### 4. Telegram Bot (Optional)

1. Message [@BotFather](https://t.me/BotFather) on Telegram, create a bot
2. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_ENABLED=true
   ```
3. Message your bot, then add your `telegram_chat_id` to the Users sheet

### 5. Chrome Extension

1. Open `chrome://extensions/`
2. Enable Developer Mode
3. Click "Load unpacked" and select the `chrome-extension/` folder
4. Click the extension icon, enter your API URL and login

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env.example`

### Frontend (Netlify)

1. Connect your repo on Netlify
2. Set base directory to `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register (requires invite code) |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/contacts` | List/create contacts |
| GET/PUT/DELETE | `/api/contacts/{id}` | Get/update/archive contact |
| POST | `/api/contacts/from-linkedin` | Create from Chrome extension |
| GET/POST | `/api/companies` | List/create companies |
| GET/PUT | `/api/companies/{id}` | Get/update company |
| GET/POST | `/api/deals` | List/create deals |
| GET/PUT | `/api/deals/{id}` | Get/update deal |
| PATCH | `/api/deals/{id}/stage` | Update deal stage |
| GET/POST | `/api/interactions` | List/create interactions |
| GET/POST | `/api/follow-ups` | List/create follow-ups |
| PATCH | `/api/follow-ups/{id}/complete` | Complete follow-up |
| PATCH | `/api/follow-ups/{id}/snooze` | Snooze follow-up |
| GET | `/api/dashboard/summary` | Dashboard stats |
| GET | `/api/dashboard/stale-deals` | Stale deals |
| POST | `/api/email/draft` | AI email draft |

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/today` | Today's + overdue follow-ups |
| `/note Name — text` | Log interaction |
| `/new Name, Company, Role` | Create contact |
| `/find query` | Search contacts/companies |
| `/pipeline` | Pipeline summary |

## Tests

```bash
cd backend
pytest -v
```
