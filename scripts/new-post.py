#!/usr/bin/env python3
"""
Create a new note template with today's date.

Usage:
  python3 scripts/new-post.py                       # interactive: enter slug + title
  python3 scripts/new-post.py my-new-post           # create with slug only
  python3 scripts/new-post.py my-new-post "标题"    # create with slug + title
"""
import re
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "data" / "posts"
POSTS_DIR.mkdir(parents=True, exist_ok=True)

today = date.today().strftime("%Y-%m-%d")

# --- parse args ---
if len(sys.argv) >= 2:
    slug = sys.argv[1].strip()
else:
    slug = input("Slug (英文, e.g. my-note): ").strip()

if len(sys.argv) >= 3:
    title = sys.argv[2].strip()
else:
    title = input("Title (笔记标题): ").strip()

# sanitize slug
slug = slug.lower().strip()
slug = re.sub(r"[^a-z0-9-]", "-", slug)
slug = re.sub(r"-+", "-", slug).strip("-")
slug = slug[:60] or "untitled"

filename = f"{today}-{slug}.md"
filepath = POSTS_DIR / filename

if filepath.exists():
    print(f"  ⚠️  Already exists: {filename}")
    overwrite = input("  Overwrite? (y/N): ").strip().lower()
    if overwrite not in ("y", "yes"):
        print("  Cancelled.")
        sys.exit(0)

content = f"""---
title: {title or "笔记标题"}
date: {today}
tags: []
summary: ""
---

## 正文

在此处开始写笔记...
"""

filepath.write_text(content, encoding="utf-8")
print(f"\n  ✅ Created: {filename}")
print(f"  📝 {filepath}")
print()
print("  Next steps:")
print("    1. Edit the file and fill in content")
print(f"    2. cd {ROOT} && python scripts/build-posts.py")
print("    3. npx vercel deploy --prod --token=$VERCEL_TOKEN")
print()
