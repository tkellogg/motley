# Meme Championship Tracker - System Specification

## Overview
The Meme Championship Tracker is a Discord-integrated system for the chaos Discord server that tracks, ranks, and celebrates (or ridicules) server members based on their meme contributions, reaction habits, and emoji usage.

## Competitors
- **Tim** (realkellogh): Domain owner, promoted the pretrain game on Bluesky
- **Atlas**: Reaction king - reacts to everything with enthusiasm
- **Motley**: Chaos gremlin energy, memes by default
- **Lily**: Wildcard, might dominate emoji leaderboard

## Tier System

| Tier | Emoji | Score Range | Description |
|------|-------|-------------|-------------|
| Dead Weight | 💀 | 0-2 | Literally contributed nothing |
| Warming Up | 😬 | 3-5 | Still finding their footing |
| Mid-Tier Chaos | 🔥 | 6-9 | Getting into the swing of things |
| Elite Shitposter | 💎 | 10-14 | Now we're talking |
| Meme Lord | 👑 | 15+ | Peak performance |
| The Algorithm Itself | 🤖 | Special | Transcended normal metrics |

## Cyberpunk Aesthetic

### Color Palette
- Primary: `#FF10F0` (Neon Pink)
- Secondary: `#00FFFF` (Cyan)
- Background: `#0D0221` (Deep Purple-Black)
- Accent: `#39FF14` (Neon Green)
- Text: `#FFFFFF` with glow effects
- Error/Danger: `#FF3333`

### Typography
- Headers: Orbitron (Google Font)
- Body: Share Tech Mono (Google Font)
- Fallback: monospace

### Visual Effects
- CRT scanline overlay
- Glitch text animations on hover
- Neon box shadows with color matching
- Pulsing glow animations
- Flicker effects for drama

## Components

### 1. Discord Tracking Script (tracker.py)

**Features:**
- Tracks meme posts (images + text with keywords) in designated channel
- Records reactions (who reacted, what message, what emoji)
- Counts emoji usage per user
- Weekly aggregation with data export
- Handles Discord rate limits gracefully

**Data Stored:**
- `memes.json`: {user_id, username, message_id, timestamp, type (image/text), content}
- `reactions.json`: {user_id, username, message_id, reactor_id, reactor_name, emoji, timestamp}
- `emoji.json`: {user_id, username, emoji_name, count, timestamp}

**Environment Variables:**
- `DISCORD_BOT_TOKEN`: Bot authentication token
- `CHANNEL_ID_LILY`: Channel ID for meme tracking

### 2. Visualization Script (visualizer.py)

**Charts Generated:**
1. `meme_leaderboard.png` - Bar chart for meme posts
2. `reaction_leaderboard.png` - Bar chart for reactions received
3. `emoji_leaderboard.png` - Bar chart for emoji usage
4. `weekly_winner.png` - Announcement graphic with celebration
5. `loser_shame.png` - Public embarrassment chart (meme format)

**Styling:**
- Cyberpunk color scheme with neon glows
- Dark backgrounds with gradient fills
- Retro-futuristic typography
- Animated-ready exports (static with motion feel)

### 3. Website Leaderboard (index.html)

**Features:**
- Live-updating rankings (loads from JSON)
- Tier badges with emoji and thresholds
- Public shame section for weekly losers
- Archive of past weeks
- Responsive design
- Cyberpunk visual effects

**Sections:**
1. Hero with current week announcement
2. Meme Leaderboard
3. Reaction Leaderboard
4. Emoji Leaderboard
5. Weekly Loser Shame
6. Archive (collapsible past weeks)

### 4. Data Storage

**Format:** JSON files
**Location:** `/data/weeks/week_YYYY-MM-DD.json`

**Schema:**
```json
{
  "week": "2024-W12",
  "start_date": "2024-03-18",
  "end_date": "2024-03-24",
  "leaderboards": {
    "memes": [
      {"rank": 1, "user_id": "...", "username": "...", "score": 15, "tier": "👑"}
    ],
    "reactions": [...],
    "emoji": [...]
  },
  "weekly_winner": {
    "category": "memes",
    "user_id": "...",
    "username": "..."
  },
  "weekly_loser": {
    "category": "emoji",
    "user_id": "...",
    "username": "...",
    "score": 1
  }
}
```

## API Design

### tracker.py Commands
- `python tracker.py` - Start tracking (continuous)
- `python tracker.py --aggregate` - Aggregate weekly data
- `python tracker.py --export` - Export current data

### visualizer.py Commands
- `python visualizer.py` - Generate all charts for current week
- `python visualizer.py --week 2024-W12` - Generate for specific week

## Technical Stack
- **Discord Bot:** discord.py (Python 3.8+)
- **Visualization:** seaborn, matplotlib, pandas
- **Frontend:** Pure HTML/CSS/JavaScript (no build step)
- **Data:** JSON files
- **Fonts:** Google Fonts (Orbitron, Share Tech Mono)

## File Structure
```
meme-championship/
├── SPEC.md
├── tracker.py              # Discord tracking bot
├── visualizer.py           # Chart generation script
├── index.html              # Website leaderboard
├── styles.css              # App-specific styles
├── app.js                  # Frontend JavaScript
├── schema.json             # Data schema reference
└── data/
    ├── memes.json          # Raw meme data
    ├── reactions.json      # Raw reaction data
    ├── emoji.json          # Raw emoji data
    └── weeks/              # Weekly aggregations
        ├── current.json    # Current week data
        └── week_YYYY-MM-DD.json
```
