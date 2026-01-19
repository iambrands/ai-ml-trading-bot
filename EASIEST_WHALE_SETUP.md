# Easiest Whale Discovery Setup 🎉

**Good news!** I've created the **easiest possible solution** - just one command!

## One Command Solution ⚡

After Railway redeploys (takes ~2 minutes), just run:

```bash
curl -X POST https://web-production-c490dd.up.railway.app/whales/initialize
```

**That's it!** The endpoint runs on Railway's infrastructure, so no tunnel setup needed.

---

## What This Does

1. ✅ Discovers top whales from Polymarket APIs
2. ✅ Indexes them into the database
3. ✅ Returns success status

**Response:**
```json
{
  "success": true,
  "discovered": 100,
  "indexed": 100,
  "message": "Successfully indexed 100 whales"
}
```

---

## Verify It Worked

1. **Check the API:**
   ```bash
   curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=5
   ```

2. **Check the UI:**
   - Go to: https://web-production-c490dd.up.railway.app
   - Click "🐋 Whale Tracker" in the sidebar
   - You should see the leaderboard!

---

## That's It!

No complex setup, no tunnels, no manual steps. Just one `curl` command and you're done! 🎉

---

## Alternative: If You Want to Use Scripts

If you prefer using the scripts instead:

1. **Simple script:**
   ```bash
   ./scripts/run_whale_discovery_simple.sh
   ```

2. **Automated script (handles tunnel):**
   ```bash
   ./scripts/run_whale_discovery_automated.sh
   ```

But the API endpoint is the **easiest** option! ✨

