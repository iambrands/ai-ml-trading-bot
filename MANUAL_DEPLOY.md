# Manual Railway Deployment

## If Railway Hasn't Auto-Deployed

Railway should auto-deploy when you push to GitHub, but if it hasn't:

### Option 1: Trigger Deployment via Railway CLI

```bash
# Make a small change to trigger deployment
railway up
```

Or:

```bash
# Link to service and deploy
railway link
railway up
```

### Option 2: Trigger via Railway Dashboard

1. Go to Railway Dashboard
2. Select your service
3. Click "Deployments" tab
4. Click "Redeploy" or "Deploy Latest"

### Option 3: Check GitHub Integration

1. Go to Railway Dashboard
2. Select your service
3. Go to "Settings" → "Source"
4. Verify GitHub repo is connected
5. Check "Auto Deploy" is enabled

### Option 4: Force Push (if needed)

```bash
# Make a small change to trigger deployment
echo "# Deployment trigger" >> README.md
git add README.md
git commit -m "Trigger deployment"
git push
```

---

## Verify Deployment

After triggering deployment:

1. Check Railway Dashboard → Deployments
2. Look for new deployment in progress
3. Check build logs for errors
4. Wait for deployment to complete (~2-5 minutes)

---

*Created: 2026-01-11*
*Status: Manual deployment guide*

