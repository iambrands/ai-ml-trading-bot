# How to Run curl Commands

## 📋 Where to Run curl

**curl** commands can be run in:

### ✅ Terminal/Command Line

**Mac/Linux**:
- Open Terminal app
- Paste the command
- Press Enter

**Windows**:
- Open Command Prompt or PowerShell
- Paste the command
- Press Enter
- (Note: Windows may need `curl.exe` or install curl first)

### ✅ Any Tool That Supports HTTP Requests

- Postman
- Insomnia
- HTTPie (`http` command)
- Browser extensions (REST Client, etc.)
- API testing tools

---

## 🎯 Current Command

**Command**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5&auto_signals=true&auto_trades=true" -H "Content-Type: application/json"
```

**What it does**:
- Triggers prediction generation
- Processes 5 markets
- Creates signals automatically (`auto_signals=true`)
- Creates trades automatically (`auto_trades=true`)

**Expected Response**:
```json
{
  "status": "started",
  "message": "Prediction generation started in background",
  "limit": 5,
  "auto_signals": true,
  "auto_trades": true
}
```

---

## ⏱️ Timeline

**Command Sent**: Immediately
**Processing Time**: 2-5 minutes for 5 markets
**Completion**: Check Railway logs after 2-5 minutes

---

## 🔍 Monitoring

### Check Railway Logs

1. Go to Railway Dashboard
2. Click on web service (web-production-c490dd)
3. Go to "Logs" tab
4. Look for:
   - `Starting prediction generation`
   - `Prediction generated`
   - `Signal created` (if conditions met)
   - `Trade created` (if signals created)

### Check UI

**After 2-5 minutes**:
1. Go to Railway dashboard
2. Check Signals tab - should see new signals
3. Check Trades tab - should see new trades
4. Check Predictions tab - should see new predictions

---

## 📊 Verify Results

### Check Signals

```bash
curl "https://web-production-c490dd.up.railway.app/signals?limit=10"
```

**Look for**:
- Signals with today's date (2026-01-11...)
- Edge values
- Side (YES or NO)

### Check Trades

```bash
curl "https://web-production-c490dd.up.railway.app/trades?limit=10"
```

**Look for**:
- Trades with today's date (2026-01-11...)
- Status: "OPEN"
- Entry time: today

---

## 🔧 Alternative: Update Cron Job

**Instead of manual commands**, you can update the cron job URL to include `auto_trades=true`:

**Current URL**:
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20
```

**Updated URL**:
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true
```

**Steps**:
1. Go to cron-job.org dashboard
2. Click on your cron job
3. Edit the URL
4. Add `&auto_signals=true&auto_trades=true`
5. Save

**Result**: Trades will be created automatically every 5 minutes

---

## ✅ Summary

**To Run curl**:
- ✅ Terminal/Command Line (easiest)
- ✅ Any HTTP client tool
- ✅ Browser extensions

**Command Sent**: ✅ Already executed
**Processing**: ⏱️ Takes 2-5 minutes
**Next Step**: Check Railway logs and UI tabs

---

*Created: 2026-01-11*
*Purpose: Help run curl commands to trigger prediction generation*



