# 🎬 Twitch → YouTube Automation

Automatically fetch top Twitch clips, edit, and post to YouTube Shorts.

**Zero token burn** – uses heuristic-based clip scoring (no Claude/AI needed).

---

## Features

✅ **Twitch API Integration** – Fetch trending clips from selected games  
✅ **Heuristic Scoring** – Rate clips by views, engagement, duration (0 tokens)  
✅ **Auto-Download** – yt-dlp integration  
✅ **FFmpeg Editing** – Convert to 9:16 (YouTube Shorts), trim to 59s  
✅ **YouTube Upload** – Post with templated title/description  
✅ **Duplicate Prevention** – SQLite database tracks posted clips  
✅ **Logging** – Full audit trail to `twitch_yt.log`  
✅ **Cron-Ready** – Run via `crontab -e`

---

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/fridtjof-Dahl/twitch-youtube-automation.git
cd twitch-youtube-automation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg # macOS
```

### 3. Configure

```bash
cp config.json.example config.json
nano config.json  # Edit with your API keys
```

### 4. Get API Keys

#### Twitch API
1. Go to https://dev.twitch.tv/console/apps
2. Create New Application
3. Copy **Client ID**
4. Generate OAuth Token: https://twitchtokengenerator.com/
5. Add to `config.json`

#### YouTube API
1. Go to https://console.cloud.google.com/
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Add API key to `config.json`

### 5. Run Manually

```bash
python3 main.py
```

Expected output:
```
2026-03-24 15:45:10 - INFO - ✅ Twitch→YouTube automation initialized
2026-03-24 15:45:11 - INFO - 🔍 Fetching clips for game: 12345
2026-03-24 15:45:12 - INFO - ✅ Fetched 87 clips for game 12345
2026-03-24 15:45:13 - INFO - 📊 Scoring 87 clips...
2026-03-24 15:45:13 - INFO - 🏆 Top 20 clips selected
2026-03-24 15:45:14 - INFO - ⏭️ Skipped (already posted): Clip #1
2026-03-24 15:45:20 - INFO - 📥 Downloading: New Viral Moment
2026-03-24 15:45:35 - INFO - ✅ Downloaded: clip_xyz.mp4
2026-03-24 15:45:45 - INFO - 🎬 Editing: clip_xyz
2026-03-24 15:46:00 - INFO - ✅ Edited: clip_xyz.mp4
2026-03-24 15:46:05 - INFO - ✅ Posted to YouTube: youtube_clip_xyz
```

### 6. Schedule with Cron

```bash
# Run daily at 09:00 CET
crontab -e

# Add this line:
0 9 * * * cd /home/user/twitch-youtube-automation && python3 main.py >> logs/cron.log 2>&1
```

---

## How It Works

### 1. Fetch Clips (FREE Twitch API)
- Queries Twitch for trending clips in configured games
- Filters by last 24h, Swedish language

### 2. Score Clips (0 tokens)
Uses heuristic scoring:
- **View count** (max 10 points)
- **Like count** (max 5 points)  
- **Duration** (30-60s optimal = 5 points)
- **Language** (Swedish bonus = 2 points)

Total score = viral likelihood (no ML needed!)

### 3. Download & Edit (FREE FFmpeg)
- Downloads clip via yt-dlp
- Converts to 9:16 (YouTube Shorts)
- Trims to max 59 seconds
- Compresses video (quality/size balance)

### 4. Upload to YouTube (FREE YouTube API)
- Posts with templated title/description
- No Claude = no token burn!

### 5. Log & Prevent Duplicates
- SQLite database tracks `twitch_id → youtube_id`
- Never posts same clip twice

---

## Configuration

Edit `config.json`:

```json
{
  "twitch_client_id": "abc123xyz",
  "twitch_token": "oauth_token_here",
  "youtube_api_key": "key_here",
  "games": ["12345", "67890"],  // Twitch Game IDs
  "post_frequency": "3_per_week",
  "max_clips_per_run": 20,
  "min_views": 500,
  "min_likes": 10
}
```

**Find Game IDs:**
```bash
curl -H "Client-ID: YOUR_CLIENT_ID" \
  "https://api.twitch.tv/helix/search/categories?query=Valorant"
```

---

## Database

SQLite database (`posted_clips.db`) tracks all posted clips:

```sql
SELECT * FROM posted_clips;
-- Returns: twitch_id | youtube_id | posted_at | title
```

To reset (careful!):
```bash
rm posted_clips.db
# Will be recreated on next run
```

---

## Logs

All runs logged to `twitch_yt.log`:

```bash
tail -f twitch_yt.log
```

Filter by level:
```bash
grep "❌ Error" twitch_yt.log
grep "✅" twitch_yt.log
```

---

## Troubleshooting

### "Twitch API 401 Unauthorized"
- Check `twitch_client_id` and `twitch_token` in config.json
- Regenerate token: https://twitchtokengenerator.com/

### "YouTube upload failed"
- Verify YouTube API is enabled in Google Cloud Console
- Check API key has YouTube Data API v3 access

### "FFmpeg not found"
```bash
# Install:
apt install ffmpeg  # Linux
brew install ffmpeg # macOS
```

### "No clips downloaded"
- Check min_views / min_likes thresholds
- Verify game IDs are correct
- Check Twitch API rate limits

---

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Twitch API | FREE |
| YouTube API | FREE |
| FFmpeg | FREE |
| yt-dlp | FREE |
| Server (if VPS) | $5-15/mnd |
| **Claude tokens** | **$0** |
| **TOTAL** | **~$5-15/mnd** |

---

## Development

### Run tests
```bash
python3 -m pytest tests/
```

### Check code
```bash
pylint main.py
```

### Git workflow
```bash
git checkout -b feature/new-feature
# Make changes
git commit -m "feat: [description]"
git push origin feature/new-feature
# Create Pull Request on GitHub
```

---

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/x`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/x`)
5. Create Pull Request

---

## License

MIT – Use freely, modify, distribute.

---

## Support

Issues? Check the logs first:
```bash
tail -50 twitch_yt.log
```

Then create a GitHub issue with:
- Error message from logs
- `config.json` (redact API keys)
- Steps to reproduce

---

**Made with ❤️ by VisionMedia**  
Zero token burn. Pure automation. Maximum viral.
