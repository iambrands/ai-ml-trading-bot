# Whale Discovery - Easy Setup Options

I've created **automated scripts** to make this much easier! You have 3 options:

## Option 1: Simple Script (Try This First) ⚡

Just run this one command:

```bash
./scripts/run_whale_discovery_simple.sh
```

**What it does:**
- Runs the script directly on Railway's infrastructure
- No tunnel setup needed
- Should work automatically

**If this fails with connection errors**, use Option 2.

---

## Option 2: Automated Script (Handles Everything) 🤖

If Option 1 doesn't work, use this automated script:

```bash
./scripts/run_whale_discovery_automated.sh
```

**What it does:**
- Automatically creates a Railway tunnel
- Sets up the database connection
- Runs the whale discovery
- Handles cleanup

**You'll be prompted:**
- Press Enter to start the tunnel
- (Optional) Provide database URL if auto-detection fails

---

## Option 3: Manual Setup (If Scripts Don't Work) 📖

If both scripts fail, follow the detailed guide:

```bash
# See the full guide
cat WHALE_DISCOVERY_SETUP.md
```

---

## Quick Start

**Just want to get it done? Run:**

```bash
./scripts/run_whale_discovery_simple.sh
```

That's it! The script will handle everything.

---

## Troubleshooting

### "Permission denied"
```bash
chmod +x scripts/run_whale_discovery_simple.sh
chmod +x scripts/run_whale_discovery_automated.sh
```

### "Railway CLI not found"
```bash
npm install -g @railway/cli
railway login
```

### Script fails with connection errors
- Try Option 2 (automated script)
- Or see `WHALE_DISCOVERY_SETUP.md` for manual steps

---

## What Happens After?

Once the script completes successfully:

1. **Check the UI:**
   - Go to: https://web-production-c490dd.up.railway.app
   - Click "🐋 Whale Tracker" in the sidebar
   - You should see the leaderboard populated

2. **Verify via API:**
   ```bash
   curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=5
   ```

3. **Done!** The whale tracker will auto-refresh every 60 seconds.

