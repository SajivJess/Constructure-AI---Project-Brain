# Quick Start Guide

## 1. Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Edit .env and add your OPENAI_API_KEY

# Run server
python main.py
```

Server runs at: http://localhost:8000

## 2. Frontend Setup (3 minutes)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.local.example .env.local

# Run development server
npm run dev
```

App runs at: http://localhost:3000

## 3. Login

Use these credentials:
- Email: `testingcheckuser1234@gmail.com`
- Password: `testpassword123`

## 4. Upload Documents

1. Go to "Documents" tab
2. Click "Upload PDF"
3. Select construction document PDFs
4. Wait for processing

## 5. Start Chatting

Ask questions like:
- "What is the fire rating for corridor partitions?"
- "Generate a door schedule"
- "What flooring materials are specified?"

## Testing

Run evaluation:
1. Go to "Evaluation" tab
2. Click "Run Evaluation"
3. View results

## Deployment to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel

# Follow prompts and add NEXT_PUBLIC_API_URL environment variable
```

For backend deployment, use Railway, Render, or any Python hosting service.
