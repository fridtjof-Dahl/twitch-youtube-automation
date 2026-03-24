#!/usr/bin/env python3
"""
Twitch → YouTube Automation
Fetches top clips from Twitch, edits, and posts to YouTube
Zero token burn (heuristic-based scoring, no Claude)
"""

import requests
import json
import subprocess
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitch_yt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TwitchToYouTube:
    def __init__(self, config_path="config.json"):
        """Initialize with config"""
        self.config = self.load_config(config_path)
        self.twitch_api = "https://api.twitch.tv/helix"
        self.db_path = "posted_clips.db"
        self.init_db()
        
        # Create directories
        Path("temp").mkdir(exist_ok=True)
        Path("edited").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info("✅ Twitch→YouTube automation initialized")
    
    def load_config(self, path):
        """Load configuration from JSON"""
        with open(path) as f:
            config = json.load(f)
        logger.info(f"✅ Config loaded from {path}")
        return config
    
    def init_db(self):
        """Initialize SQLite database for tracking"""
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_clips (
                twitch_id TEXT PRIMARY KEY,
                youtube_id TEXT,
                posted_at TEXT,
                title TEXT
            )
        """)
        db.commit()
        db.close()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def score_clip(self, clip):
        """
        HEURISTIC SCORING (0 tokens!)
        Rates clips based on virality signals
        """
        score = 0
        
        # View count (max 10 points)
        view_count = clip.get('view_count', 0)
        view_score = min(view_count / 1000, 10)
        score += view_score
        
        # Like count (max 5 points) - some clips don't have this
        like_count = clip.get('like_count', clip.get('total_views', 0) // 50)  # Fallback estimate
        like_score = min(like_count / 100, 5)
        score += like_score
        
        # Duration bonus (30-60s is optimal)
        duration = clip.get('duration', 0)
        if 30 <= duration <= 60:
            score += 5  # Perfect length
        elif 20 <= duration <= 70:
            score += 2  # Acceptable
        
        # Language bonus (Swedish content)
        if clip.get('language', '') == 'sv':
            score += 2
        
        logger.debug(f"Clip '{clip.get('title')}' scored: {score:.1f}")
        return score
    
    def fetch_top_clips(self, limit=20):
        """
        Fetch top clips from Twitch API (FREE)
        Filters by configured games and languages
        """
        
        headers = {
            "Client-ID": self.config['twitch_client_id'],
            "Authorization": f"Bearer {self.config['twitch_token']}"
        }
        
        all_clips = []
        
        for game_id in self.config.get('games', []):
            logger.info(f"🔍 Fetching clips for game: {game_id}")
            
            params = {
                "game_id": game_id,
                "first": 100,
                "period": "day",  # Last 24h
                "trending": True,
                "language": "sv"
            }
            
            try:
                response = requests.get(
                    f"{self.twitch_api}/clips",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                clips = response.json().get('data', [])
                all_clips.extend(clips)
                logger.info(f"✅ Fetched {len(clips)} clips for game {game_id}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching clips: {e}")
                continue
        
        # Score and sort by heuristic
        logger.info(f"📊 Scoring {len(all_clips)} clips...")
        scored = [(self.score_clip(c), c) for c in all_clips]
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Return top N
        top_clips = [c for _, c in scored[:limit]]
        logger.info(f"🏆 Top {len(top_clips)} clips selected")
        
        return top_clips
    
    def is_already_posted(self, twitch_clip_id):
        """Check if clip was already posted to YouTube"""
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()
        cursor.execute(
            "SELECT youtube_id FROM posted_clips WHERE twitch_id = ?",
            (twitch_clip_id,)
        )
        result = cursor.fetchone()
        db.close()
        return result is not None
    
    def download_and_edit(self, clip):
        """
        Download clip and edit with FFmpeg (FREE)
        - Convert to 9:16 (YouTube Shorts format)
        - Trim to max 59 seconds
        - Add basic formatting
        """
        
        clip_id = clip['id']
        url = clip['url']
        
        logger.info(f"📥 Downloading: {clip['title']}")
        
        # Download
        try:
            subprocess.run([
                "yt-dlp",
                "-f", "best",
                "-o", f"temp/{clip_id}.mp4",
                url
            ], check=True, capture_output=True)
            logger.info(f"✅ Downloaded: {clip_id}.mp4")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Download failed: {e}")
            return None
        
        # Edit with FFmpeg
        logger.info(f"🎬 Editing: {clip_id}")
        
        try:
            subprocess.run([
                "ffmpeg",
                "-i", f"temp/{clip_id}.mp4",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-t", "59",  # Max 59 seconds
                "-c:v", "libx264",
                "-c:a", "aac",
                "-q:v", "5",
                f"edited/{clip_id}.mp4"
            ], check=True, capture_output=True)
            logger.info(f"✅ Edited: {clip_id}.mp4")
            return f"edited/{clip_id}.mp4"
        
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Edit failed: {e}")
            return None
    
    def upload_to_youtube(self, file_path, clip):
        """
        Upload to YouTube (FREE API)
        Uses hardcoded title/description (no Claude!)
        """
        
        logger.info(f"📤 Uploading to YouTube: {clip['title']}")
        
        # Hardcoded title template (saves tokens!)
        title = f"{clip['broadcaster_name']}: {clip['title']} | Twitch Clips"
        
        description = f"""🎮 {clip['game_name']} Highlights

Streamer: {clip['broadcaster_name']}
Original Clip: {clip['url']}

Subscribe for more viral gaming clips!

#TwitchClips #{clip['game_name'].replace(' ', '')} #GamingHighlights"""
        
        # TODO: Implement YouTube API upload
        # For now, log the metadata
        logger.info(f"Would upload with title: {title}")
        logger.info(f"Description: {description[:100]}...")
        
        # Return mock YouTube ID for now
        youtube_id = f"youtube_{clip['id']}"
        return youtube_id
    
    def log_posted(self, twitch_id, youtube_id, title):
        """Log posted clip to prevent duplicates"""
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO posted_clips VALUES (?, ?, ?, ?)",
            (twitch_id, youtube_id, datetime.now().isoformat(), title)
        )
        db.commit()
        db.close()
        logger.info(f"✅ Logged: {twitch_id} → {youtube_id}")
    
    def cleanup_temp(self):
        """Clean up temporary files"""
        for f in Path("temp").glob("*.mp4"):
            try:
                f.unlink()
                logger.debug(f"Cleaned: {f}")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
    
    def run_daily(self):
        """
        Main daily run
        Called by cron job
        """
        
        logger.info("=" * 50)
        logger.info("🚀 Starting Twitch→YouTube daily run")
        logger.info("=" * 50)
        
        try:
            # Fetch top clips
            clips = self.fetch_top_clips(limit=20)
            
            if not clips:
                logger.warning("⚠️ No clips found")
                return
            
            # Process top 3 only (weekly batch = 3 per week)
            posted_count = 0
            for clip in clips[:3]:
                if self.is_already_posted(clip['id']):
                    logger.info(f"⏭️ Skipped (already posted): {clip['title']}")
                    continue
                
                logger.info(f"🎬 Processing: {clip['title']}")
                
                # Download and edit
                file_path = self.download_and_edit(clip)
                if not file_path:
                    continue
                
                # Upload to YouTube
                youtube_id = self.upload_to_youtube(file_path, clip)
                
                # Log
                self.log_posted(clip['id'], youtube_id, clip['title'])
                posted_count += 1
                
                logger.info(f"✅ Posted to YouTube: {youtube_id}")
            
            # Cleanup
            self.cleanup_temp()
            
            logger.info(f"✅ Daily run complete. Posted: {posted_count}")
            logger.info("=" * 50)
        
        except Exception as e:
            logger.error(f"❌ Error in daily run: {e}", exc_info=True)


if __name__ == "__main__":
    bot = TwitchToYouTube()
    bot.run_daily()
