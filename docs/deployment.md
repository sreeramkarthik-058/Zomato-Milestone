# Deployment Guide — Railway & Vercel

This document outlines the deployment process for the **Epicurean Pulse** restaurant recommendation application:
- **Backend**: Deployed to [Railway](https://railway.app)
- **Frontend**: Deployed to [Vercel](https://vercel.com)

---

## Table of Contents

1. [Backend Deployment (Railway)](#backend-deployment-railway)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Environment Configuration](#environment-configuration)
4. [Troubleshooting](#troubleshooting)

---

## Backend Deployment (Railway)

### Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub account with repository access
- Groq API key for LLM provider

### Step 1: Create a Railway Project

1. Log in to [Railway Dashboard](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select the repository: `sreeramkarthik-058/Zomato-Milestone`
4. Authorize Railway to access your GitHub account

### Step 2: Configure Railway Environment

1. In the Railway project, click on your service
2. Go to **"Variables"** tab
3. Add the following environment variables:

```env
LLM_API_KEY=gsk_... # Your Groq API key
LLM_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
DATASET_URL=https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
CACHE_PATH=./data/restaurants.parquet
FORCE_REFRESH=false
MAX_CANDIDATES=20
TOP_N=5
PROMPT_VERSION=v1
```

### Step 3: Configure Build & Start Commands

Do **not** set a custom Start Command in Railway — leave it blank. The `Dockerfile` handles everything via `docker-entrypoint.sh`, which starts uvicorn on port 8000. Setting a start command overrides the Dockerfile and breaks port resolution.

The `railway.json` in the repo already configures the correct build settings.

### Step 4: Data Ingestion

The HuggingFace dataset is downloaded and cached **at Docker build time** (as a `RUN` step in the Dockerfile). No action needed after deployment — every request is served from the pre-built parquet cache in the image.

### Step 5: Deploy

1. Click **"Deploy"** button in Railway
2. Monitor the deployment logs
3. Once complete, Railway will provide your service URL: `https://your-app.railway.app`

### Step 6: Configure CORS for Frontend

After the backend URL is known, update the frontend environment or code to point to:
```
VITE_API_URL=https://your-app.railway.app
```

---

## Frontend Deployment (Vercel)

### Prerequisites

- Vercel account (sign up at https://vercel.com)
- GitHub account with repository access
- Backend URL from Railway deployment

### Step 1: Prepare Frontend

Update the frontend API endpoint in environment variables or source code.

**Option A: Using environment variables (required)**
Set `VITE_API_URL` in the **Vercel dashboard** (Project → Settings → Environment Variables):
```
VITE_API_URL=https://zomato-milestone-production.up.railway.app
```
> The Vercel dashboard value takes precedence over `frontend/.env.production`. Always set it in the dashboard to avoid stale builds.

**Option B: Update source code**
If the API URL is hardcoded in the React app, update it in the relevant component.

### Step 2: Deploy to Vercel

#### Method 1: Via Vercel Dashboard (Recommended)

1. Log in to [Vercel Dashboard](https://vercel.com)
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Search and select `sreeramkarthik-058/Zomato-Milestone`
5. Configure project:
   - **Framework**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

6. Add environment variables:
   ```
   VITE_API_URL=https://your-railway-backend-url
   ```

7. Click **"Deploy"**

#### Method 2: Via Vercel CLI

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

### Step 3: Monitor Deployment

- Vercel will provide a live URL: `https://your-app.vercel.app`
- Check deployment logs at https://vercel.com/dashboard

---

## Environment Configuration

### Backend Environment Variables (Railway)

| Variable | Value | Required |
|----------|-------|----------|
| `LLM_API_KEY` | Your Groq API key | ✅ Yes |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | ✅ Yes |
| `LLM_PROVIDER` | `groq` | ✅ Yes |
| `DATASET_URL` | Hugging Face dataset URL | ✅ Yes |
| `CACHE_PATH` | `./data/restaurants.parquet` | ✅ Yes |
| `FORCE_REFRESH` | `false` | ⚠️ No (default) |
| `MAX_CANDIDATES` | `20` | ⚠️ No (default) |
| `TOP_N` | `5` | ⚠️ No (default) |
| `PROMPT_VERSION` | `v1` | ⚠️ No (default) |

### Frontend Environment Variables (Vercel)

| Variable | Value | Required |
|----------|-------|----------|
| `VITE_API_URL` | Railway backend URL | ✅ Yes |

---

## Post-Deployment Checklist

- [ ] Backend is accessible at `https://zomato-milestone-production.up.railway.app/api/health`
- [ ] Frontend is accessible at `https://zomato-milestone-ashy.vercel.app`
- [ ] API requests from frontend reach the backend successfully
- [ ] CORS is properly configured (should be open to all origins in `api.py`)
- [ ] Dataset has been cached on Railway (`data/restaurants.parquet`)
- [ ] LLM provider (Groq) is accessible and authenticated
- [ ] Test a recommendation request end-to-end

---

## Troubleshooting

### Backend Issues

#### 1. ModuleNotFoundError: No module named 'restaurant_recommender'

**Cause**: PYTHONPATH is not set correctly.

**Solution**:
- Ensure `PYTHONPATH=src` is set in Railway environment variables or update the start command:
  ```bash
  cd /app && PYTHONPATH=src uvicorn src.restaurant_recommender.app.api:app --host 0.0.0.0 --port $PORT
  ```

#### 2. 502 Bad Gateway on first request

**Cause**: Previously, the HuggingFace dataset downloaded on the first request, causing a timeout or OOM crash. This is now fixed — the dataset is baked into the Docker image at build time.

**If 502 still occurs**:
- Check Railway deploy logs immediately after the failed request for OOM or exception details
- Ensure the `RUN python -c "..."` build step completed successfully in the build logs

#### 3. Groq API key error

**Cause**: Invalid or expired API key.

**Solution**:
- Regenerate Groq API key from https://console.groq.com
- Update `LLM_API_KEY` in Railway environment variables
- Redeploy the service

### Frontend Issues

#### 1. CORS errors when calling backend

**Cause**: API URL mismatch or CORS not configured.

**Solution**:
- Verify `VITE_API_URL` in Vercel environment matches the Railway backend URL
- Check `api.py` CORS configuration is set to allow all origins:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

#### 2. Blank page or build errors

**Cause**: Build process failed or incorrect root directory.

**Solution**:
- Check Vercel build logs
- Ensure **Root Directory** is set to `frontend`
- Verify `npm run build` works locally:
  ```bash
  cd frontend && npm run build
  ```

#### 3. Environment variables not loaded

**Cause**: Variables not passed correctly to Vite build.

**Solution**:
- Ensure variables start with `VITE_` prefix (Vite requirement)
- Trigger a redeploy after adding environment variables
- Check browser console for the resolved URL: `console.log(import.meta.env.VITE_API_URL)`

---

## Monitoring & Logs

### Railway Logs

1. Go to Railway Dashboard → Your Service
2. Click **"Logs"** tab
3. Filter by date/time for debugging

### Vercel Logs

1. Go to Vercel Dashboard → Your Project
2. Click **"Deployments"** tab
3. Select a deployment to view build and runtime logs

---

## Updating Deployments

### Backend Updates (Railway)

1. Push changes to GitHub `main` branch
2. Railway auto-redeploys on push (if connected)
3. Monitor deployment logs for errors

### Frontend Updates (Vercel)

1. Push changes to GitHub `main` branch
2. Vercel auto-deploys on push (if connected)
3. Check Vercel dashboard for deployment status

---

## Rollback

### Railway

1. Go to **"Deployments"** tab
2. Select a previous stable deployment
3. Click **"Rollback"**

### Vercel

1. Go to **"Deployments"** tab
2. Click the three-dot menu on a previous deployment
3. Select **"Rollback to this Deployment"**

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)
- [Groq API Docs](https://console.groq.com/docs)
- [Hugging Face Datasets](https://huggingface.co/datasets)

---

## Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review logs on Railway or Vercel dashboards
3. Refer to project documentation in `docs/`
