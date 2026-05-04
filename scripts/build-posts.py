#!/usr/bin/env python3
"""
Build static posts from data/posts/*.md → static/posts/*.html + index.

Usage:
  python3 scripts/build-posts.py          # build all
  python3 scripts/build-posts.py --draft  # include draft posts
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import frontmatter
import mistune

ROOT = Path(__file__).resolve().parents[1]
POSTS_SRC = ROOT / "data" / "posts"
OUT_DIR = ROOT / "static" / "posts"
PUBLIC_DIR = ROOT / "data" / "public"

# HTML Templates

PAGE_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} · 笔记</title>
<style>
:root {
  --bg:#f9f8f6; --surface:#fff; --line:#e6e2db; --line-light:#f0ede8;
  --text:#1a1714; --text-secondary:#736b60; --text-quiet:#9a9184;
  --accent:#1d6b72; --accent-light:#e2f0f1; --accent-dim:#315f64;
  --code-bg:#f0ece5; --code-border:#e0dbd2; --shadow:0 1px 3px rgba(0,0,0,.04);
  --radius:10px; --radius-sm:6px;
}
*,*::before,*::after { box-sizing:border-box }
body {
  margin:0; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  font-size:16px; line-height:1.75; -webkit-font-smoothing:antialiased
}
a { color:var(--accent); text-decoration:none; transition:color .15s }
a:hover { color:#0a4b52; text-decoration:underline }
.topbar {
  position:sticky; top:0; z-index:100;
  border-bottom:1px solid var(--line);
  background:rgba(255,255,255,.88); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px)
}
.nav { max-width:820px; min-height:54px; margin:0 auto; padding:0 24px; display:flex; align-items:center; gap:24px }
.brand { font-size:15px; font-weight:700; margin-right:auto; color:var(--text); letter-spacing:-.01em }
.brand::before { content:"\\25B6"; color:var(--accent); margin-right:6px; font-size:11px }
.nav a { color:var(--text-secondary); text-decoration:none; font-size:13px; padding:4px 0; border-bottom:2px solid transparent; transition:color .15s,border-color .15s }
.nav a:hover, .nav a.active { color:var(--text); border-bottom-color:var(--accent); text-decoration:none }
.wrap { max-width:820px; margin:0 auto; padding:0 24px }
.post-hero { padding:48px 0 32px; text-align:center }
.post-hero h1 { font-size:32px; font-weight:800; line-height:1.3; margin:0 0 12px; color:var(--text); letter-spacing:-.02em }
.post-hero .date { display:block; color:var(--text-quiet); font-size:13px; margin-bottom:14px }
.post-hero .tags { display:flex; gap:6px; flex-wrap:wrap; justify-content:center }
.tag {
  display:inline-flex; background:var(--accent-light); color:var(--accent-dim);
  border-radius:20px; padding:3px 12px; font-size:12px; font-weight:500;
  text-decoration:none; transition:background .15s
}
.tag:hover { background:#cde4e6; text-decoration:none; color:var(--accent-dim) }
.article { max-width:720px; margin:0 auto 48px }
.article h2 { font-size:24px; font-weight:700; margin:40px 0 14px; color:var(--text); letter-spacing:-.01em; padding-bottom:8px; border-bottom:1px solid var(--line-light) }
.article h3 { font-size:19px; font-weight:600; margin:32px 0 10px; color:var(--text) }
.article h4 { font-size:16px; font-weight:600; margin:24px 0 8px; color:var(--text) }
.article p { margin:0 0 18px; color:var(--text-secondary); line-height:1.8 }
.article ul, .article ol { margin:0 0 18px; padding-left:24px; color:var(--text-secondary) }
.article li { margin-bottom:6px }
.article li > ul, .article li > ol { margin-bottom:0 }
.article hr { border:none; border-top:1px solid var(--line); margin:36px 0 }
.article code {
  background:var(--code-bg); border:1px solid var(--code-border); border-radius:var(--radius-sm);
  padding:2px 6px; font-size:14px; color:var(--text);
  font-family:"JetBrains Mono","Fira Code","Cascadia Code",Consolas,monospace
}
.article pre {
  background:var(--code-bg); border:1px solid var(--code-border); border-radius:var(--radius);
  padding:18px 20px; overflow-x:auto; font-size:13.5px; line-height:1.6; margin:0 0 20px
}
.article pre code { background:transparent; border:none; padding:0; font-size:inherit }
.article blockquote {
  margin:0 0 22px; padding:14px 20px; border-left:4px solid var(--accent);
  color:var(--text-secondary); background:var(--accent-light);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0; font-style:normal
}
.article blockquote p { margin:0; color:inherit }
.article blockquote p + p { margin-top:10px }
.article table { width:100%; border-collapse:collapse; margin:0 0 22px; font-size:14px }
.article th, .article td { border:1px solid var(--line); padding:10px 14px; text-align:left; vertical-align:top }
.article th {
  background:var(--line-light); font-weight:600; color:var(--text);
  font-size:13px; letter-spacing:.02em; text-transform:uppercase
}
.article td { color:var(--text-secondary) }
.article tr:nth-child(even) td { background:#fcfbf9 }
.article img { max-width:100%; border-radius:var(--radius); border:1px solid var(--line); margin:8px 0; display:block }
.article small { font-size:13px; color:var(--text-quiet) }
.footer {
  max-width:720px; margin:0 auto 48px; padding-top:20px;
  border-top:1px solid var(--line); font-size:13px;
  color:var(--text-quiet); display:flex; justify-content:space-between; align-items:center
}
.back { color:var(--text-secondary); text-decoration:none; font-size:13px; transition:color .15s }
.back:hover { color:var(--accent); text-decoration:none }
.back::before { content:"\\2190"; margin-right:4px }
.index-header { padding:48px 0 8px; text-align:center }
.index-header h1 { font-size:28px; font-weight:800; margin:0 0 6px; letter-spacing:-.02em }
.index-header p { font-size:14px; color:var(--text-quiet); margin:0 }
.post-list { max-width:640px; margin:0 auto 48px; padding:0 }
.post-row { display:block; padding:18px 0; border-bottom:1px solid var(--line-light); text-decoration:none; transition:padding .15s,background .15s }
.post-row:first-child { border-top:1px solid var(--line-light) }
.post-row:hover {
  padding-left:16px; padding-right:16px; margin:0 -16px;
  background:var(--surface); border-radius:var(--radius);
  box-shadow:var(--shadow); border-bottom-color:transparent; text-decoration:none
}
.post-row:hover + .post-row { border-top-color:transparent }
.post-date { display:block; font-size:12px; color:var(--text-quiet); margin-bottom:4px; font-weight:500 }
.post-title { display:block; font-size:17px; font-weight:600; color:var(--text); margin-bottom:5px; letter-spacing:-.01em }
.post-summary { display:block; font-size:14px; color:var(--text-secondary); line-height:1.6; max-width:90% }
.empty { text-align:center; padding:60px 0; color:var(--text-quiet); font-size:14px }
@media (max-width:640px) {
  .post-hero { padding:32px 0 24px }
  .post-hero h1 { font-size:26px }
  .article h2 { font-size:21px }
  .article { font-size:15px }
  .article pre { padding:14px 16px; font-size:13px }
  .post-row:hover { padding-left:12px; padding-right:12px; margin:0 -12px }
}
</style>
</head>
<body>
<header class="topbar"><nav class="nav"><a class="brand" href="/">Wandering Notes</a><a href="/posts">笔记</a></nav></header>
<div class="wrap">
"""

PAGE_TAIL = """</div>
</body>
</html>"""


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s[:60].strip("-")


def format_date(date_val) -> str:
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    return str(date_val)[:10]


def render_post_html(title: str, date_str: str, tags: list[str], body_html: str) -> str:
    tags_html = " ".join(
        f'<a class="tag" href="/posts?tag={t}">{t}</a>' for t in tags
    ) if tags else ""
    return "".join([
        PAGE_HEAD.replace("{title}", title),
        '<div class="post-hero">',
        f'<h1>{title}</h1>',
        f'<span class="date">{date_str}</span>',
        f'<div class="tags">{tags_html}</div>' if tags_html else "",
        '</div>',
        '<article class="article">',
        body_html,
        '</article>',
        '<footer class="footer"><a class="back" href="/posts">返回笔记列表</a></footer>',
        PAGE_TAIL,
    ])


def render_index_html(posts: list[dict]) -> str:
    items = "\n".join(
        f'<a class="post-row" href="/post/{p["slug"]}">'
        f'<span class="post-date">{p["date"]}</span>'
        f'<strong class="post-title">{p["title"]}</strong>'
        f'<span class="post-summary">{p["summary"]}</span>'
        f'</a>'
        for p in posts
    )
    index_head = PAGE_HEAD.replace("{title}", "笔记列表")
    return "".join([
        index_head,
        '<div class="index-header"><h1>笔记</h1><p>日常观察与短篇分析</p></div>',
        '<div class="post-list">',
        items if items else '<p class="empty">暂无文章</p>',
        '</div>',
        PAGE_TAIL,
    ])




def build(include_drafts: bool = False) -> None:
    POSTS_SRC.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(POSTS_SRC.glob("*.md"), reverse=True)
    posts = []
    markdown = mistune.create_markdown(plugins=['table', 'strikethrough', 'task_lists', 'footnotes'])

    for md_path in md_files:
        if md_path.name == "README.md":
            continue
        try:
            post = frontmatter.load(md_path)
        except Exception as e:
            print(f"  \u26a0\ufe0f  Skip {md_path.name}: {e}")
            continue

        if post.get("draft", False) and not include_drafts:
            print(f"  \u23ed\ufe0f  Skip draft: {md_path.name}")
            continue

        title = post.get("title", "").strip()
        if not title:
            print(f"  \u26a0\ufe0f  Skip {md_path.name}: no title")
            continue

        slug = post.get("slug") or md_path.stem
        date_str = format_date(post.get("date", ""))
        tags = post.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        body_html = markdown(str(post))
        summary = post.get("summary", "").strip() or re.sub(r"<[^>]+>", "", body_html)[:120]

        post_html = render_post_html(title, date_str, tags, body_html)
        (OUT_DIR / f"{slug}.html").write_text(post_html, encoding="utf-8")
        print(f"  \u2705 {md_path.name} \u2192 /posts/{slug}.html")

        posts.append({
            "slug": slug,
            "title": title,
            "date": date_str,
            "summary": summary,
            "tags": tags,
        })

    index_html = render_index_html(posts)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"\n  \U0001f4c4 Index: /posts/index.html ({len(posts)} posts)")

    json_path = PUBLIC_DIR / "posts.json"
    json_path.write_text(
        json.dumps({"posts": posts, "count": len(posts)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  📄 JSON: {json_path.name}")

    print(f"\n✅ Done: {len(posts)} posts built")


if __name__ == "__main__":
    include_drafts = "--draft" in sys.argv
    build(include_drafts=include_drafts)
