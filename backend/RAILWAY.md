# Railway Backend Deployment

This backend is configured for Railway deployment.

## Environment Variables Required

Set these in Railway dashboard:

```
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
```

## Deployment Steps

1. Connect Railway to your GitHub repository
2. Select the `backend` folder as root directory
3. Add environment variables
4. Deploy automatically

Railway will:
- Detect Python and install requirements.txt
- Run: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Provide a public URL

## Post-Deployment

1. Copy the Railway URL (e.g., `https://your-app.railway.app`)
2. Add it to frontend's `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=https://your-app.railway.app
   ```
3. Redeploy frontend on Vercel
