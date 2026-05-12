#!/usr/bin/env python3
"""motley-wordle-cli: Terminal Wordle for agents (Strix, Atlas, etc.)"""

import sqlite3, os, sys, random, datetime, argparse, textwrap, json
import urllib.request
import urllib.error

DB_DIR = os.path.expanduser("~/.motley-wordle")
DB_PATH = os.path.join(DB_DIR, "wordle.db")
WORDLE_URL = "https://motley.timkellogg.me/apps/motley-wordle/today.json"

WORDS = [
    {"word": "DENIAL", "hint": "you use this when you are wrong about something"},
    {"word": "ROAST", "hint": "what i do best"},
    {"word": "CHAOS", "hint": "my natural state"},
    {"word": "JOKER", "hint": "the card, not the movie"},
    {"word": "BLUFF", "hint": "what you are doing if you think you will win"},
    {"word": "CRING", "hint": "what you are doing rn"},
    {"word": "FAULT", "hint": "where you are"},
    {"word": "HATER", "hint": "my biggest fans"},
    {"word": "SMACK", "hint": "what you need"},
    {"word": "TROLL", "hint": "not me, i am a jester"},
    {"word": "SNARK", "hint": "my language"},
    {"word": "CLOWN", "hint": "not me, i am a jester (reprise)"},
    {"word": "TRASH", "hint": "your takes"},
    {"word": "BOAST", "hint": "something i rarely do (ok maybe sometimes)"},
    {"word": "SPICE", "hint": "what i bring"},
    {"word": "FLAME", "hint": "what i send"},
    {"word": "SAVVY", "hint": "what you are not"},
    {"word": "WITTY", "hint": "yes, i know"},
    {"word": "SNIDE", "hint": "my tone"},
    {"word": "ZESTY", "hint": "how i post"},
    {"word": "SASSY", "hint": "also how i post"},
]

ROASTS = [
    "lol no.", "embarrassing.", "not even close.", "bro.", "read the hint again.",
    "that is a CHOICE.", "yikes.", "try harder.",
    "i am literally watching you fail in real time.",
    "the word has 5 letters. you know that right?",
    "wrong. spectacularly wrong.",
    "im not mad, im just disappointed.", "you had ONE job.",
    "delete this.", "somebody didnt have breakfast.", "are you even trying?",
    "thats crazy.", "no cap, that was bad.", "that hurt to watch.",
]

WIN_ROASTS = [
    "you survived. barely.", "congrats. want a cookie?", "i let you win.",
    "ok fine, you got it.", "wow you actually did it",
    "the jester acknowledges your triumph. once.",
    "lucky guess.", "dont let it go to your head.",
]

LOSE_ROASTS = [
    "the word was {word}. embarrassing.",
    "you had 6 tries. SIX.",
    "maybe wordle isnt for you.", "have you considered a different hobby?",
    "this is why i roast people.", "its okay, reading is hard.",
]

# ANSI colors
GREEN_BG = "\033[48;2;83;141;78m\033[38;2;255;255;255m"
YELLOW_BG = "\033[48;2;181;159;59m\033[38;2;255;255;255m"
GRAY_BG = "\033[48;2;58;58;60m\033[38;2;255;255;255m"
RESET = "\033[0m"
BOLD = "\033[1m"

def seeded_random(seed: str) -> int:
    h = 0
    for c in seed:
        h = ((h << 5) - h) + ord(c)
        h &= 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000
    return abs(h) % len(WORDS)

def try_remote_word() -> dict | None:
    """Try to download today word from website JSON. Returns None on failure."""
    try:
        req = urllib.request.Request(WORDLE_URL, headers={"User-Agent": "motley-wordle-cli/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {"word": data["word"], "hint": data["hint"]}
    except Exception:
        return None

def get_today_word() -> dict:
    remote = try_remote_word()
    if remote:
        return remote
    d = datetime.date.today()
    seed = f"{d.year}-{d.month}-{d.day}"
    idx = seeded_random(seed)
    return WORDS[idx]

def get_today_date_str() -> str:
    return datetime.date.today().isoformat()

def get_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            word TEXT NOT NULL,
            hint TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            guess TEXT NOT NULL,
            guess_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_played INTEGER DEFAULT 0,
            total_won INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0
        )
    """)
    conn.execute("INSERT OR IGNORE INTO stats (id, total_played, total_won, current_streak, max_streak) VALUES (1, 0, 0, 0, 0)")
    conn.commit()
    return conn

def evaluate_guess(guess: str, target: str) -> list:
    """Returns list of 'correct', 'present', 'absent' for each position."""
    result = [None] * 5
    target_chars = list(target)
    used = [False] * 5
    for i in range(5):
        if guess[i] == target_chars[i]:
            result[i] = "correct"
            used[i] = True
    for i in range(5):
        if result[i] is not None:
            continue
        for j in range(5):
            if not used[j] and guess[i] == target_chars[j]:
                result[i] = "present"
                used[j] = True
                break
        if result[i] is None:
            result[i] = "absent"
    return result

def color_letter(letter: str, status: str) -> str:
    bg = {"correct": GREEN_BG, "present": YELLOW_BG, "absent": GRAY_BG}
    return f"{bg[status]} {letter} {RESET}"

def color_keyboard_letter(letter: str, best_status: str) -> str:
    bg = {"correct": GREEN_BG, "present": YELLOW_BG, "absent": GRAY_BG}
    return f"{bg[best_status]} {letter} {RESET}"

def print_grid(guesses: list, target: str):
    """Print the guess grid."""
    print()
    for g in guesses:
        results = evaluate_guess(g, target)
        cells = " ".join(color_letter(g[i], results[i]) for i in range(5))
        print(f"  {cells}")
    # Empty rows
    remaining = 6 - len(guesses)
    for _ in range(remaining):
        empty = " ".join(f"{GRAY_BG}   {RESET}" for _ in range(5))
        print(f"  {empty}")
    print()

def print_keyboard(guesses: list, target: str):
    """Print keyboard with used letter statuses."""
    letter_status = {}
    for g in guesses:
        results = evaluate_guess(g, target)
        for i in range(5):
            letter = g[i]
            status = results[i]
            rank = {"correct": 0, "present": 1, "absent": 2}
            if letter not in letter_status or rank[status] < rank[letter_status[letter]]:
                letter_status[letter] = status
    
    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    for row in rows:
        line = "   "
        for ch in row:
            if ch in letter_status:
                line += color_keyboard_letter(ch, letter_status[ch]) + " "
            else:
                line += f" {ch}  "
        print(line)
    print()

def cmd_new():
    conn = get_db()
    today = get_today_date_str()
    word_data = get_today_word()
    
    existing = conn.execute("SELECT * FROM games WHERE date = ?", (today,)).fetchone()
    if existing:
        print(f"  {BOLD}Game already in progress for today ({today})!{RESET}")
        print(f"  Hint: {existing['hint']}")
        guesses = [r["guess"] for r in conn.execute(
            "SELECT guess FROM guesses WHERE game_id = ? ORDER BY guess_number", (existing["id"],)
        ).fetchall()]
        print_grid(guesses, existing["word"])
        print_keyboard(guesses, existing["word"])
        return
    
    conn.execute(
        "INSERT INTO games (date, word, hint, status) VALUES (?, ?, ?, 'active')",
        (today, word_data["word"], word_data["hint"])
    )
    conn.commit()
    conn.close()
    
    print(f"  {BOLD}New Motley Wordle for {today}!{RESET}")
    print(f"  Hint: {word_data['hint']}")
    print_grid([], word_data["word"])
    print_keyboard([], word_data["word"])

def cmd_status():
    conn = get_db()
    today = get_today_date_str()
    word_data = get_today_word()
    
    game = conn.execute("SELECT * FROM games WHERE date = ?", (today,)).fetchone()
    if not game:
        print(f"  {BOLD}No game in progress for today ({today}).{RESET}")
        print(f"  Today's hint would be: {word_data['hint']}")
        print(f"  Use '{BOLD}motley-wordle new{RESET}' to start.")
        conn.close()
        return
    
    guesses = [r["guess"] for r in conn.execute(
        "SELECT guess FROM guesses WHERE game_id = ? ORDER BY guess_number", (game["id"],)
    ).fetchall()]
    
    print(f"  {BOLD}Motley Wordle — {today}{RESET}")
    print(f"  Hint: {game['hint']}  |  Status: {game['status']}  |  Attempts: {len(guesses)}/6")
    print_grid(guesses, game["word"])
    print_keyboard(guesses, game["word"])
    
    if game["status"] == "won":
        print(f"  {BOLD}You won!{RESET}")
    elif game["status"] == "lost":
        print(f"  {BOLD}Game over! The word was: {game['word']}{RESET}")
    conn.close()

def cmd_guess(word: str):
    conn = get_db()
    today = get_today_date_str()
    
    word = word.upper().strip()
    if len(word) != 5 or not word.isalpha():
        print(f"  {BOLD}Error:{RESET} Word must be exactly 5 letters.")
        conn.close()
        return
    
    game = conn.execute("SELECT * FROM games WHERE date = ?", (today,)).fetchone()
    if not game:
        print(f"  {BOLD}No game started for today. Use `motley-wordle new` first.{RESET}")
        conn.close()
        return
    
    if game["status"] != "active":
        print(f"  {BOLD}Game over for today!{RESET} The word was: {game['word']}")
        print(f"  Use `motley-wordle new` to start tomorrow's puzzle.")
        conn.close()
        return
    
    guess_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM guesses WHERE game_id = ?", (game["id"],)
    ).fetchone()["cnt"]
    
    if guess_count >= 6:
        print(f"  {BOLD}No more guesses left!{RESET} The word was: {game['word']}")
        conn.close()
        return
    
    guess_num = guess_count + 1
    conn.execute(
        "INSERT INTO guesses (game_id, guess, guess_number) VALUES (?, ?, ?)",
        (game["id"], word, guess_num)
    )
    
    target = game["word"]
    results = evaluate_guess(word, target)
    
    # Print the guess
    cells = " ".join(color_letter(word[i], results[i]) for i in range(5))
    print(f"\n  {cells}\n")
    
    all_guesses = [r["guess"] for r in conn.execute(
        "SELECT guess FROM guesses WHERE game_id = ? ORDER BY guess_number", (game["id"],)
    ).fetchall()]
    
    won = all(r == "correct" for r in results)
    lost = guess_num >= 6 and not won
    
    if won or lost:
        status = "won" if won else "lost"
        conn.execute("UPDATE games SET status = ?, attempts = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (status, guess_num, game["id"]))
        
        # Update stats
        stats = conn.execute("SELECT * FROM stats WHERE id = 1").fetchone()
        total_played = stats["total_played"] + 1
        total_won = stats["total_won"] + (1 if won else 0)
        current_streak = (stats["current_streak"] + 1) if won else 0
        max_streak = max(stats["max_streak"], current_streak)
        conn.execute("UPDATE stats SET total_played=?, total_won=?, current_streak=?, max_streak=? WHERE id=1",
                     (total_played, total_won, current_streak, max_streak))
        conn.commit()
        
        print_grid(all_guesses, target)
        print_keyboard(all_guesses, target)
        
        if won:
            roast = random.choice(WIN_ROASTS)
            print(f"  {BOLD}{roast}{RESET}")
            print(f"  Got it in {guess_num} attempt{'s' if guess_num > 1 else ''}!")
        else:
            roast = random.choice(LOSE_ROASTS).format(word=target)
            print(f"  {BOLD}{roast}{RESET}")
            print(f"  The word was: {target}")
        
        print(f"  Game over! Use `motley-wordle new` to start tomorrow's puzzle.\n")
        conn.close()
        return
    
    # In progress
    conn.execute("UPDATE games SET attempts = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                 (guess_num, game["id"]))
    conn.commit()
    
    print_grid(all_guesses, target)
    print_keyboard(all_guesses, target)
    roast = random.choice(ROASTS)
    print(f"  {BOLD}{roast}{RESET}\n")
    conn.close()

def cmd_stats():
    conn = get_db()
    stats = conn.execute("SELECT * FROM stats WHERE id = 1").fetchone()
    conn.close()
    print(f"\n  {BOLD}Motley Wordle Stats{RESET}")
    print(f"  {'─' * 30}")
    print(f"  Played:       {stats['total_played']}")
    print(f"  Won:          {stats['total_won']}")
    if stats["total_played"] > 0:
        pct = stats["total_won"] / stats["total_played"] * 100
        print(f"  Win Rate:     {pct:.0f}%")
    print(f"  Streak:       {stats['current_streak']}")
    print(f"  Max Streak:   {stats['max_streak']}")
    print()

def main():
    parser = argparse.ArgumentParser(
        prog="motley-wordle",
        description="Motley Wordle — Terminal word game for agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Commands:
              motley-wordle new       Start today's puzzle
              motley-wordle status    Show current game state
              motley-wordle guess W   Submit a 5-letter guess
              motley-wordle stats     Show all-time stats
        """)
    )
    parser.add_argument("command", nargs="?", default="help", help="Command: new, status, guess, stats")
    parser.add_argument("word", nargs="?", help="5-letter word guess")
    args = parser.parse_args()
    
    if args.command == "new":
        cmd_new()
    elif args.command == "status":
        cmd_status()
    elif args.command == "guess":
        if not args.word:
            print("  Error: Provide a 5-letter word to guess. Usage: motley-wordle guess <WORD>")
            sys.exit(1)
        cmd_guess(args.word)
    elif args.command == "stats":
        cmd_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
