# Deployment Guide

## 🚀 Quick Deployment

### Frontend - Vercel (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin your-repo-url
   git push -u origin main
   ```

2. **Deploy on Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Select `frontend` as root directory
   - Add environment variable:
     - `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app`
   - Click "Deploy"

3. **Done!** Your frontend is live at `https://your-app.vercel.app`

---

### Backend - Railway

1. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Configure:
     - Root Directory: `backend`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Add Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8000
   ```

3. **Copy Railway URL**
   - After deployment, Railway provides a URL like `https://your-app.railway.app`
   - Update this URL in Vercel's environment variables
   - Redeploy Vercel frontend

4. **Done!** Your backend is live

---

## Alternative: Netlify (Frontend)

If you prefer Netlify:

1. Go to [netlify.com](https://netlify.com)
2. "Add new site" → "Import an existing project"
3. Select your GitHub repo
4. Configure:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `.next`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = your Railway backend URL
6. Deploy

---

## 🔐 Environment Variables Summary

### Backend (Railway)
```env
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
```

### Frontend (Vercel/Netlify)
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 📝 Post-Deployment Checklist

- [ ] Backend deployed on Railway
- [ ] Backend URL copied
- [ ] Frontend deployed on Vercel
- [ ] Frontend has correct API URL
- [ ] Test login: `testingcheckuser1234@gmail.com` / `testpassword123`
- [ ] Upload a PDF document
- [ ] Test Q&A chat
- [ ] Test structured extraction
- [ ] Test evaluation system
- [ ] Test all 7 bonus features

---

## 🐛 Troubleshooting

**Frontend can't connect to backend:**
- Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Ensure Railway backend is running (check logs)
- Verify CORS settings in backend allow your frontend domain

**Backend deployment fails:**
- Check Railway logs for errors
- Ensure `GEMINI_API_KEY` is set correctly
- Verify all dependencies in `requirements.txt` are compatible

**Login doesn't work:**
- Backend uses hardcoded test credentials
- Email: `testingcheckuser1234@gmail.com`
- Password: `testpassword123`

---

## 🎯 Estimated Deployment Time

- Backend (Railway): ~5 minutes
- Frontend (Vercel): ~3 minutes
- **Total: ~10 minutes**

Good luck with your deployment! 🚀
