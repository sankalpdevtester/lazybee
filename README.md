# LazyBee 🐝

Automated GitHub streak maintainer + LeetCode daily problem tracker.

## Structure
```
lazybee/
├── backend/        # FastAPI + APScheduler + Gemini AI
└── frontend/       # React + TypeScript + Tailwind
```

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables (backend/.env)
```
GEMINI_API_KEY=your_key
JWT_SECRET=random_64_char_string
DATA_DIR=./data
```

## Deploy
- **Frontend** → Vercel (connect `/frontend` folder)
- **Backend** → Railway (connect `/backend` folder, set env vars)
