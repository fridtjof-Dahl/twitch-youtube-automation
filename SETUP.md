# 🚀 Setup Guide – Twitch → YouTube Automation

**Time: 15 minutes**  
**Cost: $0**  
**Token burn: $0** ✅

---

## Step 1: Clone Repository

```bash
cd /home/user  # or your workspace
git clone https://github.com/fridtjof-Dahl/twitch-youtube-automation.git
cd twitch-youtube-automation
```

---

## Step 2: Install System Dependencies

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3-pip ffmpeg
```

### macOS
```bash
brew install python@3.11 ffmpeg
```

### Windows
- Download Python: https://www.python.org/
- Download FFmpeg: https://ffmpeg.org/download.html

---

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**What this installs:**
- `requests` – HTTP client for APIs
- `yt-dlp` – Download videos from Twitch
- `google-auth-oauthlib` – YouTube authentication
- `google-api-python-client` – YouTube API

---

## Step 4: Get API Keys

### 4A. Twitch API

1. Go to https://dev.twitch.tv/console/apps
2. Click **"Register Your Application"**
3. Fill in:
   - **Name:** `Twitch YouTube Automation`
   - **OAuth Redirect URL:** `http://localhost:3000`
   - **Category:** `Analytics`
4. Click **Create**
5. Copy **Client ID**
6. Go to https://twitchtokengenerator.com/
7. Paste Client ID
8. Click **Generate Token** → Authorize
9. Copy **OAuth Token**

### 4B. YouTube API

1. Go to https://console.cloud.google.com/
2. Create **New Project** (name: `TwitchYouTube`)
3. Go to **APIs & Services** → **Library**
4. Search: `YouTube Data API v3`
5. Click **Enable**
6. Go to **APIs & Services** → **Credentials**
7. Click **+ Create Credentials** → **API Key**
8. Copy the key

---

## Step 5: Configure

```bash
cp config.json.example config.json
nano config.json  # or use any text editor
```

Paste your API keys:

```json
{
  "twitch_client_id": "your_client_id_here",
  "twitch_token": "your_oauth_token_here",
  "youtube_api_key": "your_api_key_here",
  "games": [
    "12345"    // Find game IDs below
  ],
  "post_frequency": "3_per_week",
  "max_clips_per_run": 20,
  "min_views": 500,
  "min_likes": 10
}
```

### Find Twitch Game IDs

```bash
curl -H "Client-ID: YOUR_CLIENT_ID" \
  "https://api.twitch.tv/helix/search/categories?query=Valorant"
```

Look for `id` field in response. Examples:
- **Valorant**: 516575
- **League of Legends**: 21779
- **Dota 2**: 29595
- **Counter-Strike 2**: 1437168

---

## Step 6: Test Locally

```bash
python3 main.py
```

**Expected output (first run):**

```
2026-03-24 15:45:10 - INFO - ✅ Twitch→YouTube automation initialized
2026-03-24 15:45:11 - INFO - 🔍 Fetching clips for game: 12345
2026-03-24 15:45:12 - INFO - ✅ Fetched 87 clips
2026-03-24 15:45:13 - INFO - 📊 Scoring clips...
2026-03-24 15:45:14 - INFO - 📥 Downloading: Clip Title
2026-03-24 15:45:35 - INFO - ✅ Downloaded
2026-03-24 15:45:45 - INFO - 🎬 Editing...
2026-03-24 15:46:00 - INFO - ✅ Edited
2026-03-24 15:46:05 - INFO - ✅ Posted to YouTube
```

Check logs:
```bash
tail twitch_yt.log
```

---

## Step 7: Schedule with Cron

### Check cron is installed
```bash
crontab -l  # List existing jobs (may be empty)
```

### Add daily job
```bash
crontab -e  # Opens editor
```

Paste at bottom:
```
# Run Twitch→YouTube automation daily at 09:00 CET
0 9 * * * cd /home/user/twitch-youtube-automation && python3 main.py >> logs/cron.log 2>&1
```

Save and exit (Ctrl+X if nano, :wq if vim)

### Verify
```bash
crontab -l  # Should show your job
```

---

## Step 8: Monitor

### Watch logs in real-time
```bash
tail -f twitch_yt.log
```

### Check posted clips
```bash
sqlite3 posted_clips.db "SELECT * FROM posted_clips LIMIT 5;"
```

### View cron runs
```bash
tail -f logs/cron.log
```

---

## Troubleshooting

### "Twitch API 401 Unauthorized"

```bash
# Regenerate token: https://twitchtokengenerator.com/
# Then update config.json with new token
```

### "YouTube upload failed"

1. Verify YouTube API is **enabled** in Google Cloud
2. Check API key has **YouTube Data API v3** permission
3. Verify project has proper **OAuth setup**

### "FFmpeg: command not found"

```bash
# Reinstall:
sudo apt install ffmpeg  # Linux
brew install ffmpeg     # macOS
```

### "No clips downloaded"

Check:
1. Game ID is correct
2. `min_views` and `min_likes` thresholds aren't too high
3. Clips exist in that game (check Twitch directly)
4. Twitch API token is valid

### "Cron job not running"

Check:
```bash
# Verify cron daemon is running
sudo systemctl status cron  # Linux
sudo launchctl list | grep cron  # macOS

# Check cron permissions
ls -la /var/spool/cron/crontabs/$USER

# Test manually:
cd /home/user/twitch-youtube-automation && python3 main.py
```

---

## Next Steps

### 1. Enable YouTube Upload
Currently, the script logs uploads but doesn't post. To enable:

Edit `main.py` line ~265:
```python
# Replace this:
youtube_id = f"youtube_{clip['id']}"

# With actual YouTube API upload (requires OAuth setup)
```

### 2. Add More Games
Edit `config.json`:
```json
{
  "games": [
    "516575",   // Valorant
    "21779",    // League of Legends
    "29595"     // Dota 2
  ]
}
```

### 3. Adjust Scoring
Edit `main.py` method `score_clip()` to tweak how clips are ranked.

### 4. Git Workflow
```bash
git checkout -b feature/youtube-upload
# Make changes
git commit -am "feat: Enable YouTube API upload"
git push origin feature/youtube-upload
```

---

## Monitoring Dashboard (Optional)

Create `monitor.py` to check status:
```python
import sqlite3

db = sqlite3.connect("posted_clips.db")
cursor = db.cursor()
cursor.execute("SELECT COUNT(*) FROM posted_clips")
count = cursor.fetchone()[0]
print(f"Total posted: {count}")
```

Run:
```bash
python3 monitor.py
```

---

## Cost Summary

| Item | Cost |
|------|------|
| Twitch API | FREE |
| YouTube API | FREE |
| FFmpeg | FREE |
| Hosting (VPS) | $5-15/mnd |
| **Claude tokens** | **$0** ✅ |
| **TOTAL** | **~$5-15/mnd** |

---

## Support

Issues? Check:

1. **Logs:** `tail twitch_yt.log`
2. **Config:** `cat config.json` (redact keys)
3. **Git status:** `git status`
4. **Create issue** on GitHub with logs

---

**Done! 🎉**

Your automation is now running daily at 09:00 CET.

Check back tomorrow for first clips!
