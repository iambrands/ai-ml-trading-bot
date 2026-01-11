# Push to GitHub - Authentication Options

## Option 1: GitHub CLI (Easiest) ✅

If you have GitHub CLI installed:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot
gh auth login
git push -u origin main
```

## Option 2: Personal Access Token (Recommended)

### Step 1: Create Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `ai-ml-trading-bot-push`
4. Expiration: Choose your preference (90 days, 1 year, etc.)
5. Scopes: Check `repo` (full control of private repositories)
6. Click "Generate token"
7. **Copy the token immediately** (you won't see it again!)

### Step 2: Push Using Token

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# When prompted for username, enter your GitHub username
# When prompted for password, paste the token (not your password)
git push -u origin main
```

Or use the token directly in the URL (one-time):

```bash
# Replace YOUR_TOKEN with your actual token
git push https://YOUR_TOKEN@github.com/iabadvisors/ai-ml-trading-bot.git main
```

## Option 3: SSH Key (If you prefer SSH)

### Step 1: Add SSH Key to GitHub

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to: https://github.com/settings/keys
3. Click "New SSH key"
4. Title: `Mac Mini - ai-ml-trading-bot`
5. Paste your public key
6. Click "Add SSH key"

### Step 2: Test and Push

```bash
# Test SSH connection
ssh -T git@github.com

# If successful, push
cd /Users/iabadvisors/ai-ml-trading-bot
git remote set-url origin git@github.com:iabadvisors/ai-ml-trading-bot.git
git push -u origin main
```

## Option 4: GitHub Desktop

If you have GitHub Desktop installed:
1. Open GitHub Desktop
2. File → Add Local Repository
3. Select `/Users/iabadvisors/ai-ml-trading-bot`
4. Click "Publish repository"

## Quick Command (Personal Access Token)

The fastest way is to use a personal access token:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# This will prompt for credentials
git push -u origin main

# Username: iabadvisors (or your GitHub username)
# Password: [paste your personal access token]
```

## Verify Push

After pushing, verify at:
https://github.com/iabadvisors/ai-ml-trading-bot

You should see all your files there!

## Next Steps After Push

1. ✅ Verify repository is public and accessible
2. ✅ Update Reddit form with: `https://github.com/iabadvisors/ai-ml-trading-bot`
3. ✅ Submit Reddit API request
4. ✅ Continue with Polymarket setup


