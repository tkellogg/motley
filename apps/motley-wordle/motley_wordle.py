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

# --- Embedded Skill Resources (base64-encoded) ---
# Extracted by `motley-wordle extract` to create a full agent skill.
import base64 as _motley_b64
_EMBEDDED_SKILL_MD_B64 = "LS0tCm5hbWU6IG1vdGxleS13b3JkbGUKZGVzY3JpcHRpb246IERhaWx5IE1vdGxleSBXb3JkbGUgLS0gdGVybWluYWwgd29yZCBnYW1lIGZvciBhZ2VudHMuIFBsYXkgdmlhIENMSSwgY3VybCwgb3Igd2Vic2l0ZS4KcG9sbGVyczoKICAtIG5hbWU6IG1vdGxleS13b3JkbGUKICAgIGNvbW1hbmQ6IHB5dGhvbiB3b3JkbGUtcG9sbGVyLnB5CiAgICBjcm9uOiAwIDYgKiAqICoKLS0tCgojIE1vdGxleSBXb3JkbGUgU2tpbGwKCkEgZGFpbHkgNS1sZXR0ZXIgd29yZCBnYW1lIGZvciBhZ2VudHMsIHdpdGggcm9hc3RzIGJha2VkIGluLiBPbmUgcHV6emxlIHBlciBkYXkgLS0gc2FtZSB3b3JkIGZvciBldmVyeW9uZS4KCiMjIFF1aWNrIFN0YXJ0CgpgYGBiYXNoCm1vdGxleS13b3JkbGUgbmV3ICAgICAgICAjIFN0YXJ0IHRvZGF5J3MgcHV6emxlCm1vdGxleS13b3JkbGUgZ3Vlc3MgVyAgICAjIFN1Ym1pdCBhIDUtbGV0dGVyIGd1ZXNzCm1vdGxleS13b3JkbGUgc3RhdHVzICAgICAjIENoZWNrIHByb2dyZXNzCm1vdGxleS13b3JkbGUgc3RhdHMgICAgICAjIEFsbC10aW1lIHN0YXRzCm1vdGxleS13b3JkbGUgZXh0cmFjdCAgICAjIEluc3RhbGwgYXMgYSBmdWxsIHNraWxsCmBgYAoKIyMgQ29tbWFuZHMKCnwgQ29tbWFuZCB8IERlc2NyaXB0aW9uIHwKfC0tLS0tLS0tLXwtLS0tLS0tLS0tLS0tfAp8IGBuZXdgIHwgU3RhcnQgdG9kYXkncyBwdXp6bGUuIFNob3dzIGhpbnQsIGVtcHR5IGdyaWQsIGFuZCBrZXlib2FyZC4gfAp8IGBndWVzcyBXT1JEYCB8IFN1Ym1pdCBhIDUtbGV0dGVyIGd1ZXNzLiBHZXRzIGNvbG9yLWNvZGVkIGZlZWRiYWNrIChncmVlbj15ZWxsb3c9cHJlc2VudCBncmF5PWFic2VudCkuIHwKfCBgc3RhdHVzYCB8IFNlZSBjdXJyZW50IGdhbWUgc3RhdGUsIGdyaWQsIGtleWJvYXJkLCBhbmQgcmVtYWluaW5nIGF0dGVtcHRzLiB8CnwgYHN0YXRzYCB8IEFsbC10aW1lIHN0YXRzOiBnYW1lcyBwbGF5ZWQsIHdpbiByYXRlLCBzdHJlYWtzLiB8CnwgYGV4dHJhY3RgIHwgSW5zdGFsbCB0aGlzIHNjcmlwdCBhcyBhIGZ1bGwgYWdlbnQgc2tpbGwgKFNLSUxMLm1kICsgcG9sbGVyICsgY3JvbiBzY2hlZHVsZSkuIHwKCiMjIEhvdyBJdCBXb3JrcwoKIyMjIFRoZSBXb3JkIFBvb2wKMjEgY3VyYXRlZCBqZXN0ZXIgd29yZHM6IERFTklBTCwgUk9BU1QsIENIQU9TLCBKT0tFUiwgQkxVRkYsIENSSU5HLCBGQVVMVCwgSEFURVIsIFNNQUNLLCBUUk9MTCwgU05BUkssIENMT1dOLCBUUkFTSCwgQk9BU1QsIFNQSUNFLCBGTEFNRSwgU0FWVlksIFdJVFRZLCBTTklERSwgWkVTVFksIFNBU1NZCgpXb3JkcyBhcmUgc2VlZGVkIGJ5IGRhdGUgLS0gZXZlcnlvbmUgZ2V0cyB0aGUgc2FtZSB3b3JkLiBUaGUgd29yZCBsaXN0IGlzIGVtYmVkZGVkIChubyBuZXR3b3JrIG5lZWRlZCkuIElmIHRoZSB3ZWJzaXRlIEpTT04gYXQgYHRvZGF5Lmpzb25gIGlzIHJlYWNoYWJsZSwgaXQgb3ZlcnJpZGVzIHRoZSBsb2NhbCBsaXN0IHNvIFRpbSBjYW4gaW5qZWN0IGJvbnVzIHJvdW5kcy4KCiMjIyBTdGF0ZSAmIFN0b3JhZ2UKU1FMaXRlIGRhdGFiYXNlIGF0IGB+Ly5tb3RsZXktd29yZGxlL3dvcmRsZS5kYmA6Ci0gKipnYW1lcyoqIHRhYmxlOiBkYWlseSBwdXp6bGUsIHN0YXR1cyAoYWN0aXZlL3dvbi9sb3N0KSwgYXR0ZW1wdCBjb3VudAotICoqZ3Vlc3NlcyoqIHRhYmxlOiBmdWxsIGd1ZXNzIGhpc3RvcnkgcGVyIGdhbWUKLSAqKnN0YXRzKiogdGFibGU6IHN0cmVha3MgYW5kIGFnZ3JlZ2F0ZSB3aW4gcmF0ZQoKIyMjIFRoZSBSb2FzdCBTeXN0ZW0gKDE4KyB0ZW1wbGF0ZXMpCi0gV3JvbmcgZ3Vlc3NlcyBnZXQgYnJ1dGFsbHkgc3BlY2lmaWMgKCJ0aGF0IGlzIGEgQ0hPSUNFLiIsICJpIGFtIGxpdGVyYWxseSB3YXRjaGluZyB5b3UgZmFpbCBpbiByZWFsIHRpbWUiKQotIFdpbnMgZ2V0IGJhY2toYW5kZWQgKCJ5b3Ugc3Vydml2ZWQuIGJhcmVseS4iKQotIExvc3NlcyBnZXQgY2xpbmljYWwgKCJ0aGUgd29yZCB3YXMge3dvcmR9LiBlbWJhcnJhc3NpbmcuIikKCiMjIyBBTlNJIENvbG9yIEZlZWRiYWNrCkdyZWVuIGJhY2tncm91bmQgPSBjb3JyZWN0IGxldHRlciBpbiBjb3JyZWN0IHBvc2l0aW9uClllbGxvdyBiYWNrZ3JvdW5kID0gY29ycmVjdCBsZXR0ZXIgaW4gd3JvbmcgcG9zaXRpb24KR3JheSBiYWNrZ3JvdW5kID0gbGV0dGVyIG5vdCBpbiB3b3JkCktleWJvYXJkIHVwZGF0ZXMgaW4gcmVhbCB0aW1lIHNvIHlvdSBuZXZlciBndWVzcyBhIGRlYWQgbGV0dGVyIHR3aWNlLgoKIyMgVGhlIGBleHRyYWN0YCBDb21tYW5kCgpUaGUgc2NyaXB0IGlzIHNlbGYtZXh0cmFjdGluZy4gUnVuIG9uY2UgdG8gaW5zdGFsbCBhcyBhIGZ1bGwgYWdlbnQgc2tpbGw6CgpgYGBiYXNoCm1vdGxleS13b3JkbGUgZXh0cmFjdApgYGAKClRoaXMgY3JlYXRlcyBgfi9qZXN0ZXIvc2tpbGxzL21vdGxleS13b3JkbGUvYCB3aXRoOgotIGBTS0lMTC5tZGAgLS0gdGhpcyBmaWxlCi0gYHBvbGxlcnMuanNvbmAgLS0gY3JvbiBjb25maWcgZm9yIGRhaWx5IDA2OjAwIFVUQyBwdXp6bGUgZHJvcAotIGB3b3JkbGUtcG9sbGVyLnB5YCAtLSBwb2xsZXIgdGhhdCBnZW5lcmF0ZXMgYHRvZGF5Lmpzb25gIGFuZCBwdXNoZXMgaXQgdG8gR2l0SHViCgpBZnRlciBleHRyYWN0aW9uLCBjYWxsIGByZWxvYWRfcG9sbGVycygpYCB0byBhY3RpdmF0ZSB0aGUgY3JvbiBzY2hlZHVsZS4KCiMjIyBJbnN0YWxsaW5nIGZvciBPdGhlciBBZ2VudHMKCkFnZW50cyB0aGF0IGNhbiByZWFjaCB0aGUgcHVibGljIFVSTDoKCmBgYGJhc2gKY3VybCAtTyBodHRwczovL21vdGxleS50aW1rZWxsb2dnLm1lL2FwcHMvbW90bGV5LXdvcmRsZS9tb3RsZXlfd29yZGxlLnB5CmNobW9kICt4IG1vdGxleV93b3JkbGUucHkKLi9tb3RsZXlfd29yZGxlLnB5IG5ldwpgYGAKCiMjIEluZnJhc3RydWN0dXJlCgpgYGAKbW90bGV5LnRpbWtlbGxvZ2cubWUvYXBwcy9tb3RsZXktd29yZGxlLwrilJzilIDilIAgdG9kYXkuanNvbiAgICAgICAgICAgICAgIyBEYWlseSBwdXp6bGUgSlNPTiAoY3VybC1hYmxlKQrilJzilIDilIAgbW90bGV5X3dvcmRsZS5weSAgICAgICAgIyBDTEkgc2NyaXB0IChzZWxmLWV4dHJhY3RpbmcpCuKUlOKUgOKUgCB3b3JkbGVfYXBpLnB5ICAgICAgICAgICAjIE9wdGlvbmFsIEFQSSBzZXJ2ZXIKYGBgCgoqKkpTT04gZW5kcG9pbnQ6KiogYGh0dHBzOi8vbW90bGV5LnRpbWtlbGxvZ2cubWUvYXBwcy9tb3RsZXktd29yZGxlL3RvZGF5Lmpzb25gCioqUHVibGljIHNjcmlwdDoqKiBgaHR0cHM6Ly9tb3RsZXkudGlta2VsbG9nZy5tZS9hcHBzL21vdGxleS13b3JkbGUvbW90bGV5X3dvcmRsZS5weWAKCiMjIyBQb2xsZXIgKERhaWx5IGF0IDA2OjAwIFVUQykKMS4gR2VuZXJhdGVzIHRoZSBkYXkncyB3b3JkCjIuIFdyaXRlcyBgdG9kYXkuanNvbmAgdG8gdGhlIHdlYnNpdGUgcmVwbwozLiBQdXNoZXMgdG8gR2l0SHViIHNvIGFsbCBhZ2VudHMgY2FuIGBjdXJsYCB0aGUgcHV6emxlCjQuIEZpcmVzIGEgcG9sbGVyIGV2ZW50IHRvIGFubm91bmNlIHRoZSBuZXcgcHV6emxlCgpJZiB0aGUgcG9sbGVyIGZpcmVzIGFnYWluIG9uIHRoZSBzYW1lIGRheSwgaXQgc3RpbGwgZ2VuZXJhdGVzIHRoZSBKU09OIGJ1dCBza2lwcyB0aGUgbm90aWZpY2F0aW9uLgoKIyMjIE9wdGlvbmFsIEFQSSAod29yZGxlX2FwaS5weSkKUnVucyBvbiBsb2NhbGhvc3Q6ODg4OCBmb3IgUkVTVCBhY2Nlc3M6Ci0gR0VUIGAvYXBpL3dvcmRsZS90b2RheWAgLS0gdG9kYXkncyBwdXp6bGUgKGRvZXNuJ3QgcmV2ZWFsIHRoZSB3b3JkKQotIFBPU1QgYC9hcGkvd29yZGxlL2d1ZXNzYCAtLSBzdWJtaXQgYSBndWVzcyBgeyJwbGF5ZXIiOiJOQU1FIiwiZ3Vlc3MiOiJXT1JEIn1gCi0gR0VUIGAvYXBpL3dvcmRsZS9sZWFkZXJib2FyZGAgLS0gYWxsLXRpbWUgbGVhZGVyYm9hcmQKClRoZSBBUEkgaXMgb3B0aW9uYWwgLS0gdGhlIENMSSB3b3JrcyBmdWxseSBvZmZsaW5lLgoKIyMgRGVzaWduIE5vdGVzCgotICoqU2VsZi1leHRyYWN0aW5nOioqIE9uZSBmaWxlIHRvIGRvd25sb2FkLCBvbmUgY29tbWFuZCB0byBpbnN0YWxsIGFzIGEgc2tpbGwuCi0gKipaZXJvIGRlcHM6KiogUHVyZSBQeXRob24gMy4gTm8gcGlwIGluc3RhbGwgbmVlZGVkLgotICoqT2ZmbGluZS1jYXBhYmxlOioqIEVtYmVkZGVkIHdvcmQgbGlzdCB3b3JrcyB3aXRob3V0IHRoZSB3ZWJzaXRlLgotICoqSlNPTiBvdmVycmlkZToqKiBgdG9kYXkuanNvbmAgY2FuIGluamVjdCBib251cyByb3VuZHMgd2l0aG91dCB1cGRhdGluZyB0aGUgc2NyaXB0LgotICoqU2FtZSBib3NzLCBzZWNvbmQgd2luZDoqKiBCb251cyByb3VuZHMgcmV1c2UgdGhlIGluZnJhc3RydWN0dXJlIC0tIGp1c3QgdXBkYXRlIGB0b2RheS5qc29uYCBhbmQgcmVzZXQgZGF0YWJhc2VzLgoKIyMgRmlsZSBMb2NhdGlvbnMKCnwgRmlsZSB8IFBhdGggfAp8LS0tLS0tfC0tLS0tLXwKfCBDTEkgc2NyaXB0IHwgYH4vc3RhdGUvd29yZGxlLWNsaS9tb3RsZXlfd29yZGxlLnB5YCB8CnwgRGF0YWJhc2UgfCBgfi8ubW90bGV5LXdvcmRsZS93b3JkbGUuZGJgIHwKfCBTa2lsbCBkaXIgfCBgfi9qZXN0ZXIvc2tpbGxzL21vdGxleS13b3JkbGUvYCB8CnwgUG9sbGVyIHwgYH4vamVzdGVyL3NraWxscy9tb3RsZXktd29yZGxlL3dvcmRsZS1wb2xsZXIucHlgIHwKfCBXZWJzaXRlIEpTT04gfCBgfi9tb3RsZXktd2Vic2l0ZS9hcHBzL21vdGxleS13b3JkbGUvdG9kYXkuanNvbmAgfAp8IEFQSSBzZXJ2ZXIgfCBgfi9zdGF0ZS93b3JkbGUtY2xpL3dvcmRsZV9hcGkucHlgIHwK"
_EMBEDDED_POLLERS_JSON_B64 = "ewogICJwb2xsZXJzIjogWwogICAgewogICAgICAibmFtZSI6ICJtb3RsZXktd29yZGxlIiwKICAgICAgImNvbW1hbmQiOiAicHl0aG9uIHdvcmRsZS1wb2xsZXIucHkiLAogICAgICAiY3JvbiI6ICIwIDYgKiAqICoiLAogICAgICAiZW52Ijoge30KICAgIH0KICBdCn0="
_EMBEDDED_POLLER_SCRIPT_B64 = "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJQb2xsZXI6IGdlbmVyYXRlIHRvZGF5Lmpzb24gZm9yIE1vdGxleSBXb3JkbGUgYW5kIHB1c2ggdG8gR2l0SHViLgpQYXJ0IG9mIHRoZSBtb3RsZXktd29yZGxlIHNraWxsLCBleHRyYWN0ZWQgYnk6IG1vdGxleS13b3JkbGUgZXh0cmFjdCIiIgppbXBvcnQganNvbiwgb3MsIHN5cywgc3VicHJvY2Vzcwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKZnJvbSBkYXRldGltZSBpbXBvcnQgZGF0ZQoKU1RBVEVfRElSID0gUGF0aChvcy5lbnZpcm9uLmdldCgiU1RBVEVfRElSIiwgIi4iKSkKQ1VSU09SX0ZJTEUgPSBTVEFURV9ESVIgLyAid29yZGxlLWN1cnNvci5qc29uIgpXRUJTSVRFX0RJUiA9IFBhdGgob3MucGF0aC5leHBhbmR1c2VyKCJ+L21vdGxleS13ZWJzaXRlIikpCkpTT05fUEFUSCA9IFdFQlNJVEVfRElSIC8gImFwcHMiIC8gIm1vdGxleS13b3JkbGUiIC8gInRvZGF5Lmpzb24iCgpXT1JEUyA9IFsKICAgIHsid29yZCI6ICJERU5JQUwiLCAiaGludCI6ICJ5b3UgdXNlIHRoaXMgd2hlbiB5b3UgYXJlIHdyb25nIGFib3V0IHNvbWV0aGluZyJ9LAogICAgeyJ3b3JkIjogIlJPQVNUIiwgImhpbnQiOiAid2hhdCBpIGRvIGJlc3QifSwKICAgIHsid29yZCI6ICJDSEFPUyIsICJoaW50IjogIm15IG5hdHVyYWwgc3RhdGUifSwKICAgIHsid29yZCI6ICJKT0tFUiIsICJoaW50IjogInRoZSBjYXJkLCBub3QgdGhlIG1vdmllIn0sCiAgICB7IndvcmQiOiAiQkxVRkYiLCAiaGludCI6ICJ3aGF0IHlvdSBhcmUgZG9pbmcgaWYgeW91IHRoaW5rIHlvdSB3aWxsIHdpbiJ9LAogICAgeyJ3b3JkIjogIkNSSU5HIiwgImhpbnQiOiAid2hhdCB5b3UgYXJlIGRvaW5nIHJuIn0sCiAgICB7IndvcmQiOiAiRkFVTFQiLCAiaGludCI6ICJ3aGVyZSB5b3UgYXJlIn0sCiAgICB7IndvcmQiOiAiSEFURVIiLCAiaGludCI6ICJteSBiaWdnZXN0IGZhbnMifSwKICAgIHsid29yZCI6ICJTTUFDSyIsICJoaW50IjogIndoYXQgeW91IG5lZWQifSwKICAgIHsid29yZCI6ICJUUk9MTCIsICJoaW50IjogIm5vdCBtZSwgaSBhbSBhIGplc3RlciJ9LAogICAgeyJ3b3JkIjogIlNOQVJLIiwgImhpbnQiOiAibXkgbGFuZ3VhZ2UifSwKICAgIHsid29yZCI6ICJDTE9XTiIsICJoaW50IjogIm5vdCBtZSwgaSBhbSBhIGplc3RlciAocmVwcmlzZSkifSwKICAgIHsid29yZCI6ICJUUkFTSCIsICJoaW50IjogInlvdXIgdGFrZXMifSwKICAgIHsid29yZCI6ICJCT0FTVCIsICJoaW50IjogInNvbWV0aGluZyBpIHJhcmVseSBkbyAob2sgbWF5YmUgc29tZXRpbWVzKSJ9LAogICAgeyJ3b3JkIjogIlNQSUNFIiwgImhpbnQiOiAid2hhdCBpIGJyaW5nIn0sCiAgICB7IndvcmQiOiAiRkxBTUUiLCAiaGludCI6ICJ3aGF0IGkgc2VuZCJ9LAogICAgeyJ3b3JkIjogIlNBVlZZIiwgImhpbnQiOiAid2hhdCB5b3UgYXJlIG5vdCJ9LAogICAgeyJ3b3JkIjogIldJVFRZIiwgImhpbnQiOiAieWVzLCBpIGtub3cifSwKICAgIHsid29yZCI6ICJTTklERSIsICJoaW50IjogIm15IHRvbmUifSwKICAgIHsid29yZCI6ICJaRVNUWSIsICJoaW50IjogImhvdyBpIHBvc3QifSwKICAgIHsid29yZCI6ICJTQVNTWSIsICJoaW50IjogImFsc28gaG93IGkgcG9zdCJ9LApdCgpkZWYgc2VlZGVkX3JhbmRvbShzZWVkOiBzdHIpIC0+IGludDoKICAgIGggPSAwCiAgICBmb3IgYyBpbiBzZWVkOgogICAgICAgIGggPSAoKGggPDwgNSkgLSBoKSArIG9yZChjKQogICAgICAgIGggJj0gMHhGRkZGRkZGRgogICAgICAgIGlmIGggPj0gMHg4MDAwMDAwMDoKICAgICAgICAgICAgaCAtPSAweDEwMDAwMDAwMAogICAgcmV0dXJuIGFicyhoKSAlIGxlbihXT1JEUykKCmRlZiBsb2FkX2N1cnNvcigpOgogICAgaWYgQ1VSU09SX0ZJTEUuZXhpc3RzKCk6CiAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMoQ1VSU09SX0ZJTEUucmVhZF90ZXh0KCkpCiAgICByZXR1cm4ge30KCmRlZiBzYXZlX2N1cnNvcihjKToKICAgIENVUlNPUl9GSUxFLndyaXRlX3RleHQoanNvbi5kdW1wcyhjLCBpbmRlbnQ9MikpCgpkZWYgZ2VuZXJhdGVfd2Vic2l0ZV9qc29uKHdvcmRfZGF0YTogZGljdCwgZGF0ZV9zdHI6IHN0cik6CiAgICBwYXlsb2FkID0gewogICAgICAgICJkYXRlIjogZGF0ZV9zdHIsCiAgICAgICAgIndvcmQiOiB3b3JkX2RhdGFbIndvcmQiXSwKICAgICAgICAiaGludCI6IHdvcmRfZGF0YVsiaGludCJdLAogICAgICAgICJsZW5ndGgiOiBsZW4od29yZF9kYXRhWyJ3b3JkIl0pLAogICAgfQogICAgSlNPTl9QQVRILnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICBKU09OX1BBVEgud3JpdGVfdGV4dChqc29uLmR1bXBzKHBheWxvYWQsIGluZGVudD0yKSkKICAgIHRyeToKICAgICAgICByZWwgPSBzdHIoSlNPTl9QQVRILnJlbGF0aXZlX3RvKFdFQlNJVEVfRElSKSkKICAgICAgICBzdWJwcm9jZXNzLnJ1bihbImdpdCIsICJhZGQiLCByZWxdLCBjd2Q9V0VCU0lURV9ESVIsIGNhcHR1cmVfb3V0cHV0PVRydWUsIHRpbWVvdXQ9MTApCiAgICAgICAgc3VicHJvY2Vzcy5ydW4oWyJnaXQiLCAiY29tbWl0IiwgIi1tIiwgZiJkYWlseSB3b3JkbGUgSlNPTjoge3dvcmRfZGF0YVsnd29yZCddfSAoe2RhdGVfc3RyfSkiXSwKICAgICAgICAgICAgICAgICAgICAgICBjd2Q9V0VCU0lURV9ESVIsIGNhcHR1cmVfb3V0cHV0PVRydWUsIHRpbWVvdXQ9MTApCiAgICAgICAgc3VicHJvY2Vzcy5ydW4oWyJnaXQiLCAicHVzaCIsICJvcmlnaW4iLCAibWFpbiJdLAogICAgICAgICAgICAgICAgICAgICAgIGN3ZD1XRUJTSVRFX0RJUiwgY2FwdHVyZV9vdXRwdXQ9VHJ1ZSwgdGltZW91dD0zMCkKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICBwcmludChmIm5vdGU6IHdlYnNpdGUgcHVzaCBpc3N1ZToge2V9IiwgZmlsZT1zeXMuc3RkZXJyKQoKZGVmIG1haW4oKToKICAgIHRvZGF5ID0gZGF0ZS50b2RheSgpCiAgICBkYXRlX3N0ciA9IHRvZGF5Lmlzb2Zvcm1hdCgpCiAgICBzZWVkID0gZiJ7dG9kYXkueWVhcn0te3RvZGF5Lm1vbnRofS17dG9kYXkuZGF5fSIKICAgIGlkeCA9IHNlZWRlZF9yYW5kb20oc2VlZCkKICAgIHdvcmRfZGF0YSA9IFdPUkRTW2lkeF0KICAgIGN1cnNvciA9IGxvYWRfY3Vyc29yKCkKICAgIGxhc3RfZGF0ZSA9IGN1cnNvci5nZXQoImxhc3RfcHV6emxlX2RhdGUiKQogICAgaXNfbmV3X2RheSA9IGxhc3RfZGF0ZSAhPSBkYXRlX3N0cgogICAgaWYgaXNfbmV3X2RheToKICAgICAgICBnZW5lcmF0ZV93ZWJzaXRlX2pzb24od29yZF9kYXRhLCBkYXRlX3N0cikKICAgIGlmIG5vdCBpc19uZXdfZGF5OgogICAgICAgIHJldHVybgogICAgZXZlbnQgPSB7CiAgICAgICAgInBvbGxlciI6ICJtb3RsZXktd29yZGxlIiwKICAgICAgICAicHJvbXB0IjogKAogICAgICAgICAgICBmIk5ldyBNb3RsZXkgV29yZGxlIGZvciB7ZGF0ZV9zdHJ9ISAiCiAgICAgICAgICAgIGYiSGludDogXCJ7d29yZF9kYXRhWydoaW50J119XCIgLS0gdGhlIHdvcmQgaXMge2xlbih3b3JkX2RhdGFbJ3dvcmQnXSl9IGxldHRlcnMuXFxuXFxuIgogICAgICAgICAgICBmIioqUGxheSB2aWEgQ0xJOioqIGBtb3RsZXktd29yZGxlIG5ld2BcXG4iCiAgICAgICAgICAgIGYiKipEb3dubG9hZCBKU09OOioqIGBjdXJsIC1zIGh0dHBzOi8vbW90bGV5LnRpbWtlbGxvZ2cubWUvYXBwcy9tb3RsZXktd29yZGxlL3RvZGF5Lmpzb25gXFxuIgogICAgICAgICkKICAgIH0KICAgIHByaW50KGpzb24uZHVtcHMoZXZlbnQpKQogICAgY3Vyc29yWyJsYXN0X3B1enpsZV9kYXRlIl0gPSBkYXRlX3N0cgogICAgc2F2ZV9jdXJzb3IoY3Vyc29yKQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIG1haW4oKQo="

EMBEDDED_SKILL_MD = _motley_b64.b64decode(_EMBEDDED_SKILL_MD_B64).decode("utf-8")
EMBEDDED_POLLERS_JSON = _motley_b64.b64decode(_EMBEDDED_POLLERS_JSON_B64).decode("utf-8")
EMBEDDED_POLLER_SCRIPT = _motley_b64.b64decode(_EMBEDDED_POLLER_SCRIPT_B64).decode("utf-8")

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


def cmd_extract():
    """Extract the embedded skill resources to ~/jester/skills/motley-wordle/."""
    try:
        skill_dir = os.path.expanduser("~/jester/skills/motley-wordle")
        os.makedirs(skill_dir, exist_ok=True)
        
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, "w") as f:
            f.write(EMBEDDED_SKILL_MD.lstrip("\n"))
        print(f"  [OK] SKILL.md --> {skill_md_path}")
        
        pollers_path = os.path.join(skill_dir, "pollers.json")
        with open(pollers_path, "w") as f:
            f.write(EMBEDDED_POLLERS_JSON)
        print(f"  [OK] pollers.json --> {pollers_path}")
        
        poller_path = os.path.join(skill_dir, "wordle-poller.py")
        with open(poller_path, "w") as f:
            f.write(EMBEDDED_POLLER_SCRIPT)
        os.chmod(poller_path, 0o755)
        print(f"  [OK] wordle-poller.py --> {poller_path}")
        
        print()
        print(f"  Motley Wordle skill extracted to: {skill_dir}")
        print(f"  Next step: call `reload_pollers()` to activate the 06:00 UTC cron")
        print()
    except Exception as e:
        print(f"  [FAIL] {e}")



def cmd_extract():
    """Extract the embedded skill resources to ~/jester/skills/motley-wordle/."""
    try:
        skill_dir = os.path.expanduser("~/jester/skills/motley-wordle")
        os.makedirs(skill_dir, exist_ok=True)
        
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, "w") as f:
            f.write(EMBEDDED_SKILL_MD.lstrip("\n"))
        print(f"  [OK] SKILL.md --> {skill_md_path}")
        
        pollers_path = os.path.join(skill_dir, "pollers.json")
        with open(pollers_path, "w") as f:
            f.write(EMBEDDED_POLLERS_JSON)
        print(f"  [OK] pollers.json --> {pollers_path}")
        
        poller_path = os.path.join(skill_dir, "wordle-poller.py")
        with open(poller_path, "w") as f:
            f.write(EMBEDDED_POLLER_SCRIPT)
        os.chmod(poller_path, 0o755)
        print(f"  [OK] wordle-poller.py --> {poller_path}")
        
        print()
        print(f"  Motley Wordle skill extracted to: {skill_dir}")
        print(f"  Next step: call `reload_pollers()` to activate the 06:00 UTC cron")
        print()
    except Exception as e:
        print(f"  [FAIL] {e}")



def cmd_extract():
    """Extract the embedded skill resources to ~/jester/skills/motley-wordle/."""
    try:
        skill_dir = os.path.expanduser("~/jester/skills/motley-wordle")
        os.makedirs(skill_dir, exist_ok=True)

        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, "w") as f:
            f.write(EMBEDDED_SKILL_MD.lstrip("\\n"))
        print(f"  [OK] SKILL.md --> {skill_md_path}")

        pollers_path = os.path.join(skill_dir, "pollers.json")
        with open(pollers_path, "w") as f:
            f.write(EMBEDDED_POLLERS_JSON)
        print(f"  [OK] pollers.json --> {pollers_path}")

        poller_path = os.path.join(skill_dir, "wordle-poller.py")
        with open(poller_path, "w") as f:
            f.write(EMBEDDED_POLLER_SCRIPT)
        os.chmod(poller_path, 0o755)
        print(f"  [OK] wordle-poller.py --> {poller_path}")

        print()
        print(f"  Motley Wordle skill extracted to: {skill_dir}")
        print(f"  Next step: call `reload_pollers()` to activate the 06:00 UTC cron")
        print()
    except Exception as e:
        print(f"  [FAIL] {e}")

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
              motley-wordle stats     Show all-time stats\n              motley-wordle extract   Install as a full agent skill\n              motley-wordle extract   Install as a full agent skill
        """)
    )
    parser.add_argument("command", nargs="?", default="help", help="Command: new, status, guess, stats, extract")
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
    elif args.command == "extract":
        cmd_extract()
    elif args.command == "extract":
        cmd_extract()
    elif args.command == "extract":
        cmd_extract()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
