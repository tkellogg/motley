#!/usr/bin/env python3
"""Motley Wordle HTTP API — bonus round patch, reads word from today.json"""

import http.server
import json
import sqlite3
import os
import random
import datetime
import urllib.request
import urllib.error

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


def get_today_word() -> dict:
    """Read from published today.json so we can override for bonus rounds."""
    local = os.path.expanduser("~/motley-website/apps/motley-wordle/today.json")
    try:
        with open(local) as f:
            return json.load(f)
    except Exception:
        pass
    url = "https://motley.timkellogg.me/apps/motley-wordle/today.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "motley-wordle-api"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        pass
    d = datetime.date.today()
    seed = f"{d.year}-{d.month}-{d.day}"
    h = 0
    for c in seed:
        h = ((h << 5) - h) + ord(c)
        h &= 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000
    return WORDS[abs(h) % len(WORDS)]


def get_today_date_str() -> str:
    return datetime.date.today().isoformat()


DB_DIR = os.path.expanduser("~/.motley-wordle")
DB_PATH = os.path.join(DB_DIR, "wordle_api.db")
os.makedirs(DB_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            date TEXT NOT NULL,
            guesses TEXT NOT NULL DEFAULT '[]',
            won INTEGER NOT NULL DEFAULT 0,
            finished INTEGER NOT NULL DEFAULT 0,
            UNIQUE(player, date)
        )
    """)
    conn.commit()
    conn.close()


def check_answer(word: str, guess: str) -> list:
    word = word.upper()
    guess = guess.upper()
    result = ["gray"] * 5
    word_chars = list(word)
    guess_chars = list(guess)
    for i in range(5):
        if guess_chars[i] == word_chars[i]:
            result[i] = "green"
            word_chars[i] = None
            guess_chars[i] = None
    for i in range(5):
        if guess_chars[i] is not None and guess_chars[i] in word_chars:
            result[i] = "yellow"
            idx = word_chars.index(guess_chars[i])
            word_chars[idx] = None
    return result


class WordleAPI(http.server.BaseHTTPRequestHandler):
    def _send(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/wordle/today":
            self._handle_today()
        elif path == "/api/wordle/leaderboard":
            self._handle_leaderboard()
        else:
            self._send({"error": "not found", "endpoints": [
                "GET  /api/wordle/today",
                "POST /api/wordle/guess",
                "GET  /api/wordle/leaderboard",
            ]}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/api/wordle/guess":
            self._handle_guess()
        else:
            self._send({"error": "not found"}, 404)

    def _handle_today(self):
        word_info = get_today_word()
        self._send({
            "date": get_today_date_str(),
            "length": word_info.get("length", len(word_info["word"])),
            "hint": word_info["hint"],
            "note": "guess via POST /api/wordle/guess with {'player': NAME, 'guess': WORD}",
        })

    def _handle_guess(self):
        body = self._read_body()
        player = body.get("player", "").strip()
        guess = body.get("guess", "").strip().upper()
        if not player or not guess:
            self._send({"error": "need player and guess"}, 400)
            return
        if len(guess) != 5:
            self._send({"error": "guess must be 5 letters"}, 400)
            return
        if not guess.isalpha():
            self._send({"error": "guess must be letters only"}, 400)
            return

        word_info = get_today_word()
        answer = word_info["word"].upper()
        date_str = get_today_date_str()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute(
            "SELECT id, guesses, won, finished FROM games WHERE player = ? AND date = ?",
            (player, date_str),
        )
        row = cur.fetchone()

        if row:
            game_id, guesses_json, won, finished = row
            guesses_list = json.loads(guesses_json)
            if finished:
                conn.close()
                if won:
                    self._send({"player": player, "status": "already_won", "message": "you already got it today. stop flexing."})
                else:
                    self._send({"player": player, "status": "already_lost", "message": f"you already lost today. the word was {answer}. move on."})
                return
            if len(guesses_list) >= 6:
                conn.close()
                self._send({"player": player, "status": "out_of_tries", "message": f"no more guesses. the word was {answer}. better luck never."})
                return
        else:
            guesses_list = []

        result = check_answer(answer, guess)
        is_correct = all(r == "green" for r in result)
        guesses_list.append({"guess": guess, "result": result})

        if is_correct:
            roast = random.choice(WIN_ROASTS)
            won, finished = 1, 1
        elif len(guesses_list) >= 6:
            roast = random.choice(LOSE_ROASTS).format(word=answer)
            won, finished = 0, 1
        else:
            roast = random.choice(ROASTS)
            won, finished = 0, 0

        if row:
            conn.execute("UPDATE games SET guesses = ?, won = ?, finished = ? WHERE id = ?",
                         (json.dumps(guesses_list), int(won), int(finished), game_id))
        else:
            conn.execute("INSERT INTO games (player, date, guesses, won, finished) VALUES (?, ?, ?, ?, ?)",
                         (player, date_str, json.dumps(guesses_list), int(won), int(finished)))
        conn.commit()
        conn.close()

        self._send({
            "player": player,
            "guess": guess,
            "result": result,
            "correct": is_correct,
            "guesses_used": len(guesses_list),
            "guesses_remaining": 6 - len(guesses_list) if not finished else 0,
            "roast": roast,
        })

    def _handle_leaderboard(self):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT player, date, guesses, won, finished FROM games ORDER BY date DESC, id DESC
        """).fetchall()
        conn.close()
        today = get_today_date_str()
        leaderboard = []
        for player, date, guesses_str, won, finished in rows:
            guesses_list = json.loads(guesses_str)
            leaderboard.append({
                "player": player,
                "date": date,
                "guesses_count": len(guesses_list),
                "won": bool(won),
                "finished": bool(finished),
                "is_today": date == today,
            })
        today_winners = [e for e in leaderboard if e["is_today"] and e["won"]]
        today_winners.sort(key=lambda e: e["guesses_count"])
        self._send({
            "today": today,
            "word_info": {"hint": get_today_word()["hint"], "length": get_today_word().get("length", 5)},
            "leaderboard": leaderboard,
            "today_winners": today_winners,
        })

    def log_message(self, format, *args):
        pass


def main():
    init_db()
    port = int(os.environ.get("WORDLE_PORT", 8888))
    server = http.server.HTTPServer(("0.0.0.0", port), WordleAPI)
    word_info = get_today_word()
    print(f"Motley Wordle API on http://0.0.0.0:{port}")
    print(f"  Today's word: {word_info.get('word', '???')} — {word_info.get('hint', '???')}")
    print(f"  GET  /api/wordle/today")
    print(f"  POST /api/wordle/guess")
    print(f"  GET  /api/wordle/leaderboard")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()


if __name__ == "__main__":
    main()
