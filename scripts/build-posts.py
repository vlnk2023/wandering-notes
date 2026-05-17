#!/usr/bin/env python3
"""
Build static posts from data/posts/*.md -> static/posts/*.html plus the /posts index.

Usage:
  python scripts/build-posts.py          # build public posts
  python scripts/build-posts.py --draft  # include draft posts
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import frontmatter
import mistune

ROOT = Path(__file__).resolve().parents[1]
POSTS_SRC = ROOT / "data" / "posts"
OUT_DIR = ROOT / "static" / "posts"
PUBLIC_DIR = ROOT / "data" / "public"
STATIC_DIR = ROOT / "static"

SITE_NAME = "Wandering Notes"
SITE_SUBTITLE = "日常观察、工具记录与长短分析的临时营地。"


BASE_CSS = r"""
:root {
  --bg:#f7f3eb;
  --paper:#fffdf8;
  --paper-strong:#fff8eb;
  --ink:#201b16;
  --muted:#70675c;
  --quiet:#9b9184;
  --line:#e6ded0;
  --line-soft:#f0e8db;
  --accent:#0e6f6d;
  --accent-deep:#094d4b;
  --accent-soft:#dff1ec;
  --amber:#af6b1a;
  --amber-soft:#f7e8c9;
  --rose:#8b4738;
  --shadow:0 20px 60px rgba(79,55,28,.11);
  --shadow-soft:0 10px 26px rgba(79,55,28,.08);
  --radius:22px;
  --radius-md:16px;
  --radius-sm:10px;
}
*,*::before,*::after { box-sizing:border-box }
html { scroll-behavior:smooth }
body {
  margin:0;
  color:var(--ink);
  background:
    radial-gradient(circle at 8% -8%, rgba(14,111,109,.14), transparent 34rem),
    radial-gradient(circle at 88% 8%, rgba(175,107,26,.15), transparent 28rem),
    linear-gradient(180deg, #fbf6ec 0%, var(--bg) 42%, #f3eee5 100%);
  font-family:"Noto Serif SC","Source Han Serif SC","LXGW WenKai","PingFang SC","Microsoft YaHei",serif;
  font-size:16px;
  line-height:1.75;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}
body::before {
  content:"";
  position:fixed;
  inset:0;
  pointer-events:none;
  opacity:.52;
  background-image:
    linear-gradient(rgba(32,27,22,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(32,27,22,.027) 1px, transparent 1px);
  background-size:34px 34px;
  mask-image:linear-gradient(180deg, rgba(0,0,0,.65), transparent 68%);
}
a { color:var(--accent); text-decoration:none; text-underline-offset:3px }
a:hover { color:var(--accent-deep); text-decoration:underline }
button,input,select { font:inherit }
.sr-only {
  position:absolute;
  width:1px;
  height:1px;
  padding:0;
  margin:-1px;
  overflow:hidden;
  clip:rect(0,0,0,0);
  white-space:nowrap;
  border:0;
}
.topbar {
  position:sticky;
  top:0;
  z-index:100;
  border-bottom:1px solid rgba(230,222,208,.78);
  background:rgba(255,253,248,.82);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
}
.nav {
  max-width:1120px;
  min-height:64px;
  margin:0 auto;
  padding:0 24px;
  display:flex;
  align-items:center;
  gap:16px;
}
.brand {
  flex:0 0 auto;
  color:var(--ink);
  font-size:16px;
  font-weight:800;
  letter-spacing:.01em;
}
.brand::before {
  content:"";
  display:inline-block;
  width:9px;
  height:9px;
  margin-right:9px;
  border-radius:99px;
  background:var(--accent);
  box-shadow:0 0 0 5px rgba(14,111,109,.12);
  vertical-align:1px;
}
.nav a:not(.brand) {
  color:var(--muted);
  font-size:14px;
  font-weight:700;
  text-decoration:none;
  padding:5px 0;
  border-bottom:2px solid transparent;
}
.nav a:not(.brand):hover,
.nav a.active {
  color:var(--ink);
  border-bottom-color:var(--accent);
}
.nav-search {
  flex:1 1 520px;
  max-width:560px;
  margin-left:auto;
}
.nav-search-box {
  position:relative;
}
.nav-search-box::before {
  content:"⌕";
  position:absolute;
  left:16px;
  top:50%;
  transform:translateY(-50%);
  color:var(--quiet);
  font-size:20px;
  z-index:1;
}
.nav-search #searchInput {
  width:100%;
  min-height:42px;
  border:1px solid var(--line);
  border-radius:999px;
  background:rgba(255,250,241,.94);
  color:var(--ink);
  outline:none;
  padding:0 76px 0 44px;
}
.nav-search #searchInput:focus {
  border-color:rgba(14,111,109,.55);
  box-shadow:0 0 0 4px rgba(14,111,109,.12);
}
.nav-search-submit {
  position:absolute;
  right:5px;
  top:5px;
  min-height:32px;
  padding:0 14px;
  border:0;
  border-radius:999px;
  background:var(--ink);
  color:#fffaf1;
  cursor:pointer;
  font-size:13px;
  font-weight:900;
}
.nav-search-submit:hover { background:var(--accent-deep) }
.wrap,
.home-shell {
  width:min(1120px, 100%);
  margin:0 auto;
  padding:0 24px;
}
.post-wrap {
  width:min(880px, 100%);
  margin:0 auto;
  padding:0 24px;
}
.post-hero {
  padding:64px 0 34px;
  text-align:center;
}
.post-hero h1 {
  max-width:780px;
  margin:0 auto 14px;
  color:var(--ink);
  font-size:clamp(30px, 5vw, 52px);
  font-weight:900;
  line-height:1.16;
  letter-spacing:-.045em;
}
.post-hero .date {
  display:block;
  color:var(--quiet);
  font-size:14px;
  margin-bottom:16px;
}
.tags {
  display:flex;
  justify-content:center;
  flex-wrap:wrap;
  gap:8px;
}
.tag,
.mini-tag,
.filter-pill {
  display:inline-flex;
  align-items:center;
  gap:6px;
  border:1px solid rgba(14,111,109,.16);
  border-radius:999px;
  background:var(--accent-soft);
  color:var(--accent-deep);
  font-size:13px;
  font-weight:700;
  line-height:1;
  text-decoration:none;
}
.tag { padding:7px 12px }
.mini-tag { padding:6px 10px }
.tag:hover,
.mini-tag:hover {
  color:var(--accent-deep);
  background:#cfe9e3;
  text-decoration:none;
}
.article {
  max-width:760px;
  margin:0 auto 56px;
  padding:32px clamp(20px, 4vw, 42px);
  border:1px solid rgba(230,222,208,.9);
  border-radius:var(--radius);
  background:rgba(255,253,248,.88);
  box-shadow:var(--shadow-soft);
}
.article h2 {
  margin:44px 0 16px;
  padding-bottom:10px;
  border-bottom:1px solid var(--line-soft);
  color:var(--ink);
  font-size:26px;
  font-weight:900;
  line-height:1.35;
  letter-spacing:-.025em;
}
.article h2:first-child { margin-top:0 }
.article h3 {
  margin:34px 0 12px;
  color:var(--ink);
  font-size:21px;
  font-weight:800;
}
.article h4 {
  margin:26px 0 10px;
  color:var(--ink);
  font-size:17px;
  font-weight:800;
}
.article p { margin:0 0 18px; color:var(--muted); line-height:1.86 }
.article ul,
.article ol { margin:0 0 20px; padding-left:26px; color:var(--muted) }
.article li { margin-bottom:7px }
.article li > ul,
.article li > ol { margin-bottom:0 }
.article hr { border:none; border-top:1px solid var(--line); margin:38px 0 }
.article code {
  border:1px solid #e6dac8;
  border-radius:8px;
  background:#f3eadb;
  padding:2px 6px;
  color:#3b2e20;
  font-family:"JetBrains Mono","Fira Code","Cascadia Code",Consolas,monospace;
  font-size:.9em;
}
.article pre {
  margin:0 0 22px;
  padding:18px 20px;
  overflow-x:auto;
  border:1px solid #e3d7c4;
  border-radius:var(--radius-md);
  background:#f4ecdf;
  font-size:14px;
  line-height:1.65;
}
.article pre code { border:none; background:transparent; padding:0; font-size:inherit }
.article blockquote {
  margin:0 0 24px;
  padding:16px 20px;
  border-left:4px solid var(--accent);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;
  background:rgba(223,241,236,.7);
  color:var(--muted);
}
.article blockquote p { margin:0; color:inherit }
.article blockquote p + p { margin-top:10px }
.article table {
  width:100%;
  margin:0 0 24px;
  border-collapse:collapse;
  font-size:14px;
}
.article th,
.article td {
  border:1px solid var(--line);
  padding:10px 14px;
  text-align:left;
  vertical-align:top;
}
.article th {
  background:var(--paper-strong);
  color:var(--ink);
  font-weight:800;
}
.article td { color:var(--muted) }
.article img {
  display:block;
  max-width:100%;
  margin:12px 0;
  border:1px solid var(--line);
  border-radius:var(--radius-md);
}
.post-actions {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  margin:26px auto 0;
}
.post-action-group {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
}
.post-action {
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:40px;
  padding:0 14px;
  border:1px solid rgba(14,111,109,.18);
  border-radius:999px;
  background:rgba(255,253,248,.86);
  color:var(--accent-deep);
  box-shadow:0 8px 22px rgba(79,55,28,.08);
  cursor:pointer;
  font-size:14px;
  font-weight:900;
  text-decoration:none;
}
.post-action:hover {
  transform:translateY(-1px);
  background:var(--accent-soft);
  color:var(--accent-deep);
  text-decoration:none;
}
.post-action.secondary {
  border-color:var(--line);
  color:var(--muted);
}
.post-action.secondary:hover {
  color:var(--ink);
  background:#fffaf1;
}
.index-strip {
  padding:28px 0 16px;
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:18px;
}
.index-strip h1 {
  margin:0;
  font-size:clamp(28px, 5vw, 48px);
  line-height:1;
  letter-spacing:-.05em;
  font-weight:950;
}
.index-strip p {
  margin:8px 0 0;
  color:var(--muted);
  font-size:15px;
}
.index-metrics {
  display:flex;
  flex-wrap:wrap;
  justify-content:flex-end;
  gap:8px;
}
.index-metric {
  display:inline-flex;
  align-items:center;
  min-height:34px;
  padding:0 11px;
  border:1px solid var(--line);
  border-radius:999px;
  background:rgba(255,253,248,.74);
  color:var(--muted);
  font-size:13px;
  font-weight:800;
}
.index-toolbar {
  margin:0 0 20px;
  padding:12px 0 18px;
  border-top:1px solid rgba(230,222,208,.72);
  border-bottom:1px solid rgba(230,222,208,.72);
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:14px;
}
.index-toolbar .search-meta {
  margin:0;
}
.index-toolbar-controls {
  display:flex;
  align-items:center;
  gap:10px;
}
.index-toolbar #sortSelect {
  width:auto;
  min-width:136px;
  min-height:40px;
  border-radius:999px;
}
.index-toolbar .clear-btn {
  min-height:40px;
  border-radius:999px;
}
.index-hero {
  padding:58px 0 24px;
  display:grid;
  grid-template-columns:minmax(0, 1.35fr) minmax(260px, .65fr);
  gap:24px;
  align-items:stretch;
}
.hero-copy,
.hero-card,
.search-card,
.side-card,
.post-card {
  border:1px solid rgba(230,222,208,.9);
  background:rgba(255,253,248,.86);
  box-shadow:var(--shadow-soft);
}
.hero-copy {
  position:relative;
  overflow:hidden;
  border-radius:calc(var(--radius) + 8px);
  padding:38px;
}
.hero-copy::after {
  content:"";
  position:absolute;
  right:-72px;
  bottom:-96px;
  width:260px;
  height:260px;
  border-radius:40% 60% 50% 50%;
  background:linear-gradient(135deg, rgba(14,111,109,.16), rgba(175,107,26,.18));
  transform:rotate(-14deg);
}
.eyebrow {
  display:inline-flex;
  align-items:center;
  gap:8px;
  margin:0 0 16px;
  color:var(--accent-deep);
  font-size:13px;
  font-weight:900;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.eyebrow::before {
  content:"";
  width:22px;
  height:2px;
  border-radius:99px;
  background:var(--accent);
}
.hero-copy h1 {
  position:relative;
  z-index:1;
  margin:0;
  max-width:760px;
  font-size:clamp(38px, 7vw, 76px);
  line-height:1.02;
  letter-spacing:-.065em;
  font-weight:950;
}
.hero-copy p {
  position:relative;
  z-index:1;
  max-width:620px;
  margin:18px 0 0;
  color:var(--muted);
  font-size:18px;
}
.hero-card {
  border-radius:var(--radius);
  padding:24px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  background:
    linear-gradient(160deg, rgba(255,253,248,.95), rgba(255,248,235,.92)),
    radial-gradient(circle at 100% 0, rgba(14,111,109,.18), transparent 10rem);
}
.hero-card-title {
  margin:0 0 16px;
  color:var(--muted);
  font-size:13px;
  font-weight:900;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.stat-grid {
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:12px;
}
.stat {
  padding:14px;
  border:1px solid var(--line-soft);
  border-radius:var(--radius-md);
  background:rgba(255,255,255,.45);
}
.stat strong {
  display:block;
  font-size:27px;
  line-height:1;
  letter-spacing:-.03em;
}
.stat span {
  display:block;
  margin-top:8px;
  color:var(--quiet);
  font-size:13px;
  font-weight:700;
}
.latest-list {
  margin:20px 0 0;
  display:grid;
  gap:10px;
}
.latest-item {
  display:block;
  padding:12px;
  border-radius:var(--radius-sm);
  color:var(--ink);
  background:rgba(255,255,255,.5);
  text-decoration:none;
}
.latest-item:hover { background:var(--accent-soft); text-decoration:none }
.latest-item span {
  display:block;
  color:var(--quiet);
  font-size:12px;
}
.latest-item strong {
  display:block;
  margin-top:2px;
  font-size:14px;
  line-height:1.45;
}
.search-card {
  position:sticky;
  top:76px;
  z-index:50;
  margin:0 0 24px;
  border-radius:var(--radius);
  padding:18px;
}
.search-row {
  display:grid;
  grid-template-columns:minmax(0, 1fr) 160px auto;
  gap:12px;
}
.search-input-wrap { position:relative }
.search-input-wrap::before {
  content:"⌕";
  position:absolute;
  left:16px;
  top:50%;
  transform:translateY(-50%);
  color:var(--quiet);
  font-size:20px;
}
#searchInput,
#sortSelect {
  width:100%;
  min-height:48px;
  border:1px solid var(--line);
  border-radius:15px;
  background:#fffaf1;
  color:var(--ink);
  outline:none;
}
#searchInput {
  padding:0 16px 0 44px;
}
#sortSelect {
  padding:0 12px;
  cursor:pointer;
}
#searchInput:focus,
#sortSelect:focus {
  border-color:rgba(14,111,109,.55);
  box-shadow:0 0 0 4px rgba(14,111,109,.12);
}
.clear-btn,
.facet-chip,
.filter-pill button {
  border:none;
  cursor:pointer;
}
.clear-btn {
  min-height:48px;
  padding:0 18px;
  border-radius:15px;
  background:var(--ink);
  color:#fffaf1;
  font-weight:900;
}
.clear-btn:hover { background:var(--accent-deep) }
.search-meta {
  margin-top:12px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:14px;
  color:var(--quiet);
  font-size:13px;
}
.shortcut { color:var(--muted) }
kbd {
  display:inline-flex;
  min-width:22px;
  min-height:22px;
  align-items:center;
  justify-content:center;
  margin:0 3px;
  border:1px solid var(--line);
  border-bottom-width:2px;
  border-radius:7px;
  background:#fffaf1;
  color:var(--ink);
  font-family:"JetBrains Mono","Cascadia Code",monospace;
  font-size:12px;
}
.content-grid {
  display:grid;
  grid-template-columns:280px minmax(0, 1fr);
  gap:24px;
  align-items:start;
  padding-bottom:64px;
}
.sidebar {
  position:sticky;
  top:84px;
  display:grid;
  gap:16px;
}
.side-card {
  border-radius:var(--radius);
  padding:18px;
}
.side-card h2 {
  margin:0 0 12px;
  font-size:15px;
  letter-spacing:.02em;
}
.chip-stack {
  display:flex;
  flex-wrap:wrap;
  gap:8px;
}
.facet-chip {
  display:inline-flex;
  align-items:center;
  gap:7px;
  padding:8px 10px;
  border:1px solid var(--line);
  border-radius:999px;
  background:#fffaf1;
  color:var(--muted);
  font-size:13px;
  font-weight:800;
}
.facet-chip:hover,
.facet-chip.active {
  border-color:rgba(14,111,109,.24);
  background:var(--accent-soft);
  color:var(--accent-deep);
}
.facet-chip span {
  color:var(--quiet);
  font-size:12px;
  font-weight:800;
}
.archive-stack {
  display:grid;
  gap:8px;
}
.archive-button {
  width:100%;
  justify-content:space-between;
  border-radius:14px;
}
.active-filters {
  min-height:31px;
  margin:0 0 16px;
  display:flex;
  flex-wrap:wrap;
  gap:8px;
}
.filter-pill {
  padding:7px 9px 7px 12px;
  background:var(--amber-soft);
  color:#6d4113;
  border-color:rgba(175,107,26,.2);
}
.filter-pill button {
  width:18px;
  height:18px;
  border-radius:999px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  background:rgba(109,65,19,.12);
  color:#6d4113;
  font-weight:900;
}
.month-section {
  margin:0 0 28px;
}
.month-title {
  margin:0 0 12px;
  display:flex;
  align-items:center;
  gap:12px;
  color:var(--muted);
  font-size:14px;
  font-weight:900;
  letter-spacing:.04em;
}
.month-title::after {
  content:"";
  height:1px;
  flex:1;
  background:var(--line);
}
.month-title span:last-child {
  color:var(--quiet);
  font-weight:800;
}
.post-list {
  display:grid;
  gap:14px;
}
.post-card {
  border-radius:var(--radius);
  padding:22px;
  transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.post-card:hover {
  transform:translateY(-2px);
  border-color:rgba(14,111,109,.22);
  box-shadow:var(--shadow);
}
.post-meta {
  display:flex;
  flex-wrap:wrap;
  gap:9px;
  align-items:center;
  margin-bottom:10px;
  color:var(--quiet);
  font-size:13px;
  font-weight:800;
}
.dot::before {
  content:"";
  display:inline-block;
  width:4px;
  height:4px;
  margin:0 9px 2px 0;
  border-radius:999px;
  background:var(--line);
}
.post-title {
  display:inline;
  color:var(--ink);
  font-size:23px;
  font-weight:900;
  line-height:1.28;
  letter-spacing:-.025em;
  text-decoration:none;
}
.post-title:hover { color:var(--accent-deep); text-decoration:none }
.post-summary {
  margin:10px 0 0;
  color:var(--muted);
  line-height:1.75;
}
.post-tags {
  margin-top:14px;
  display:flex;
  flex-wrap:wrap;
  gap:8px;
}
mark {
  border-radius:5px;
  background:#ffe39b;
  color:inherit;
  padding:0 2px;
}
.empty {
  padding:56px 24px;
  border:1px dashed var(--line);
  border-radius:var(--radius);
  background:rgba(255,253,248,.68);
  color:var(--muted);
  text-align:center;
}
.empty strong {
  display:block;
  margin-bottom:6px;
  color:var(--ink);
  font-size:20px;
}
.empty[hidden] { display:none }
@media (max-width:900px) {
  .index-hero,
  .content-grid {
    grid-template-columns:1fr;
  }
  .search-card,
  .sidebar {
    position:static;
  }
  .sidebar {
    grid-template-columns:repeat(2, minmax(0, 1fr));
  }
}
@media (max-width:680px) {
  .nav { min-height:0; padding:10px 18px; gap:10px 14px; flex-wrap:wrap }
  .nav-search { order:3; flex-basis:100%; max-width:none; margin-left:0 }
  .home-shell,
  .wrap,
  .post-wrap { padding:0 18px }
  .index-strip { align-items:flex-start; flex-direction:column; padding-top:22px }
  .index-metrics { justify-content:flex-start }
  .index-toolbar { align-items:flex-start; flex-direction:column }
  .index-toolbar-controls { width:100%; align-items:stretch }
  .index-toolbar #sortSelect { flex:1; width:100% }
  .index-hero { padding-top:34px }
  .hero-copy { padding:26px }
  .hero-copy p { font-size:16px }
  .search-row { grid-template-columns:1fr }
  .search-meta { align-items:flex-start; flex-direction:column }
  .sidebar { grid-template-columns:1fr }
  .post-card { padding:18px }
  .post-title { font-size:20px }
  .article { padding:24px 18px }
  .post-hero { padding:40px 0 26px }
}
"""


INDEX_SCRIPT = r"""
(() => {
  const posts = JSON.parse(document.getElementById("posts-data").textContent);
  const els = {
    form: document.getElementById("navSearchForm"),
    search: document.getElementById("searchInput"),
    sort: document.getElementById("sortSelect"),
    clear: document.getElementById("clearFilters"),
    tagFilters: document.getElementById("tagFilters"),
    archiveFilters: document.getElementById("archiveFilters"),
    activeFilters: document.getElementById("activeFilters"),
    postList: document.getElementById("postList"),
    empty: document.getElementById("emptyState"),
    resultCount: document.getElementById("resultCount")
  };

  const state = { q: "", tag: "", month: "", sort: "new" };
  const collator = new Intl.Collator("zh-CN", { numeric: true, sensitivity: "base" });

  const normalize = (value) => String(value || "").toLocaleLowerCase("zh-CN").replace(/\s+/g, " ").trim();
  const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
  const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const tokensFrom = (value) => normalize(value).split(/\s+/).filter(Boolean).slice(0, 8);
  const urlFor = (post) => `/post/${encodeURIComponent(post.slug)}`;

  function monthName(month) {
    const found = posts.find((post) => post.month === month);
    return found ? found.monthLabel : month;
  }

  function countBy(items, iteratee) {
    const map = new Map();
    items.forEach((item) => {
      const values = iteratee(item);
      (Array.isArray(values) ? values : [values]).filter(Boolean).forEach((value) => {
        map.set(value, (map.get(value) || 0) + 1);
      });
    });
    return map;
  }

  function sortedEntries(map, byValue = false) {
    return [...map.entries()].sort((a, b) => {
      if (byValue && b[1] !== a[1]) return b[1] - a[1];
      return collator.compare(a[0], b[0]);
    });
  }

  function readUrl() {
    const params = new URLSearchParams(location.search);
    state.q = params.get("q") || "";
    state.tag = params.get("tag") || "";
    state.month = params.get("month") || "";
    state.sort = params.get("sort") || "new";
    if (!["new", "old", "title"].includes(state.sort)) state.sort = "new";
  }

  function writeUrl(replace = false) {
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.tag) params.set("tag", state.tag);
    if (state.month) params.set("month", state.month);
    if (state.sort !== "new") params.set("sort", state.sort);
    const next = `${location.pathname}${params.toString() ? `?${params}` : ""}`;
    history[replace ? "replaceState" : "pushState"]({}, "", next);
  }

  function postScore(post, tokens) {
    if (!tokens.length) return 0;
    return tokens.reduce((score, token) => {
      if (normalize(post.title).includes(token)) score += 8;
      if (post.tags.some((tag) => normalize(tag).includes(token))) score += 5;
      if (normalize(post.summary).includes(token)) score += 3;
      if (normalize(post.content).includes(token)) score += 1;
      return score;
    }, 0);
  }

  function getSnippet(post, tokens) {
    const summary = post.summary || "";
    if (!tokens.length) return summary;

    const summaryNorm = normalize(summary);
    if (tokens.some((token) => summaryNorm.includes(token))) return summary;

    const content = post.content || summary;
    const contentNorm = normalize(content);
    const firstHit = tokens.map((token) => contentNorm.indexOf(token)).filter((index) => index >= 0).sort((a, b) => a - b)[0];
    if (firstHit === undefined) return summary;

    const start = Math.max(0, firstHit - 42);
    const end = Math.min(content.length, firstHit + 118);
    return `${start > 0 ? "..." : ""}${content.slice(start, end)}${end < content.length ? "..." : ""}`;
  }

  function highlight(value, tokens) {
    const escaped = escapeHtml(value);
    if (!tokens.length) return escaped;
    const pattern = tokens.filter((token) => token.length <= 40).map(escapeRegExp).join("|");
    if (!pattern) return escaped;
    return escaped.replace(new RegExp(`(${pattern})`, "gi"), "<mark>$1</mark>");
  }

  function tagsHtml(post) {
    if (!post.tags.length) return "";
    return `<div class="post-tags">${post.tags.map((tag) => (
      `<a class="mini-tag" href="/posts?tag=${encodeURIComponent(tag)}" data-filter-tag="${escapeHtml(tag)}">#${escapeHtml(tag)}</a>`
    )).join("")}</div>`;
  }

  function postCard(post, tokens) {
    const snippet = getSnippet(post, tokens);
    return `
      <article class="post-card">
        <div class="post-meta">
          <time datetime="${escapeHtml(post.date)}">${escapeHtml(post.date || "未标日期")}</time>
          <span class="dot">${escapeHtml(post.readingTime)} 分钟读完</span>
        </div>
        <a class="post-title" href="${urlFor(post)}">${highlight(post.title, tokens)}</a>
        <p class="post-summary">${highlight(snippet, tokens)}</p>
        ${tagsHtml(post)}
      </article>
    `;
  }

  function groupPosts(list) {
    return list.reduce((groups, post) => {
      const month = post.month || "未归档";
      if (!groups.has(month)) groups.set(month, []);
      groups.get(month).push(post);
      return groups;
    }, new Map());
  }

  function renderPosts(list, tokens) {
    if (!list.length) {
      els.postList.innerHTML = "";
      els.empty.hidden = false;
      return;
    }

    els.empty.hidden = true;
    els.postList.innerHTML = [...groupPosts(list).entries()].map(([month, monthPosts]) => `
      <section class="month-section">
        <h2 class="month-title"><span>${escapeHtml(monthName(month))}</span><span>${monthPosts.length} 篇</span></h2>
        <div class="post-list">${monthPosts.map((post) => postCard(post, tokens)).join("")}</div>
      </section>
    `).join("");
  }

  function renderFacets() {
    const tagCounts = sortedEntries(countBy(posts, (post) => post.tags), true);
    const monthCounts = [...countBy(posts, (post) => post.month).entries()].sort((a, b) => b[0].localeCompare(a[0]));

    els.tagFilters.innerHTML = tagCounts.map(([tag, count]) => `
      <button class="facet-chip ${state.tag === tag ? "active" : ""}" type="button" data-tag-value="${escapeHtml(tag)}">
        #${escapeHtml(tag)} <span>${count}</span>
      </button>
    `).join("");

    els.archiveFilters.innerHTML = monthCounts.map(([month, count]) => `
      <button class="facet-chip archive-button ${state.month === month ? "active" : ""}" type="button" data-month-value="${escapeHtml(month)}">
        ${escapeHtml(monthName(month))} <span>${count}</span>
      </button>
    `).join("");

  }

  function renderActiveFilters() {
    const chips = [];
    if (state.q) chips.push(["q", `搜索：${state.q}`]);
    if (state.tag) chips.push(["tag", `标签：${state.tag}`]);
    if (state.month) chips.push(["month", `时间：${monthName(state.month)}`]);

    els.activeFilters.innerHTML = chips.map(([key, label]) => `
      <span class="filter-pill">${escapeHtml(label)} <button type="button" aria-label="移除${escapeHtml(label)}" data-remove-filter="${key}">×</button></span>
    `).join("");
  }

  function filteredPosts() {
    const tokens = tokensFrom(state.q);
    let list = posts.map((post) => ({ ...post, score: postScore(post, tokens) }));

    list = list.filter((post) => {
      const matchesQuery = !tokens.length || tokens.every((token) => normalize(post.searchText).includes(token));
      const matchesTag = !state.tag || post.tags.includes(state.tag);
      const matchesMonth = !state.month || post.month === state.month;
      return matchesQuery && matchesTag && matchesMonth;
    });

    list.sort((a, b) => {
      if (tokens.length && b.score !== a.score) return b.score - a.score;
      if (state.sort === "old") return a.date.localeCompare(b.date);
      if (state.sort === "title") return collator.compare(a.title, b.title);
      return b.date.localeCompare(a.date);
    });

    return { list, tokens };
  }

  function apply(replaceUrl = false) {
    els.search.value = state.q;
    els.sort.value = state.sort;

    const { list, tokens } = filteredPosts();
    renderFacets();
    renderActiveFilters();
    renderPosts(list, tokens);
    els.resultCount.textContent = `显示 ${list.length} / ${posts.length} 篇`;
    writeUrl(replaceUrl);
  }

  els.search.addEventListener("input", () => {
    state.q = els.search.value.trim();
    apply(true);
  });

  els.form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.q = els.search.value.trim();
    apply();
  });

  els.sort.addEventListener("change", () => {
    state.sort = els.sort.value;
    apply();
  });

  els.clear.addEventListener("click", () => {
    state.q = "";
    state.tag = "";
    state.month = "";
    state.sort = "new";
    apply();
    els.search.focus();
  });

  els.tagFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tag-value]");
    if (!button) return;
    const tag = button.dataset.tagValue;
    state.tag = state.tag === tag ? "" : tag;
    apply();
  });

  els.archiveFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-month-value]");
    if (!button) return;
    const month = button.dataset.monthValue;
    state.month = state.month === month ? "" : month;
    apply();
  });

  els.activeFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-filter]");
    if (!button) return;
    const key = button.dataset.removeFilter;
    if (key === "q") state.q = "";
    if (key === "tag") state.tag = "";
    if (key === "month") state.month = "";
    apply();
  });

  els.postList.addEventListener("click", (event) => {
    const link = event.target.closest("[data-filter-tag]");
    if (!link) return;
    event.preventDefault();
    state.tag = link.dataset.filterTag;
    apply();
  });

  window.addEventListener("popstate", () => {
    readUrl();
    apply(true);
  });

  window.addEventListener("keydown", (event) => {
    const target = event.target;
    const isTyping = target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
    if (event.key === "/" && !isTyping) {
      event.preventDefault();
      els.search.focus();
    }
  });

  readUrl();
  apply(true);
})();
"""


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def compact_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_tags(tags: object) -> list[str]:
    if not tags:
        return []
    if isinstance(tags, str):
        raw_tags = re.split(r"[,，]", tags)
    elif isinstance(tags, (list, tuple, set)):
        raw_tags = tags
    else:
        raw_tags = [tags]

    seen: set[str] = set()
    normalized: list[str] = []
    for tag in raw_tags:
        name = str(tag).strip()
        if name and name not in seen:
            seen.add(name)
            normalized.append(name)
    return normalized


def format_date(date_val: object) -> str:
    if isinstance(date_val, (datetime, date)):
        return date_val.strftime("%Y-%m-%d")
    return str(date_val or "")[:10]


def month_key(date_str: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})", date_str or "")
    return match.group(0) if match else "unknown"


def month_label(month: str) -> str:
    if re.match(r"^\d{4}-\d{2}$", month):
        year, month_num = month.split("-")
        return f"{year}年{int(month_num)}月"
    return "未归档"


def markdown_to_text(markdown_text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", markdown_text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[>\-+*\s]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~>#|]", " ", text)
    return compact_text(text)


def summarize(text: str, limit: int = 150) -> str:
    text = compact_text(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def reading_time(text: str) -> int:
    # Chinese notes are dense; 500 chars/min keeps the estimate conservative.
    return max(1, (len(text) + 499) // 500)


def post_url(slug: str) -> str:
    return "/post/" + quote(str(slug), safe="-_.~")


def tag_url(tag: str) -> str:
    return "/posts?tag=" + quote(str(tag), safe="")


def month_url(month: str) -> str:
    return "/posts?month=" + quote(str(month), safe="")


def safe_json(data: object) -> str:
    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_page_head(title: str, description: str = SITE_SUBTITLE) -> str:
    full_title = SITE_NAME if title == SITE_NAME else f"{title} · {SITE_NAME}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="{esc(description)}">
<title>{esc(full_title)}</title>
<style>
{BASE_CSS}
</style>
</head>
<body>
<header class="topbar">
  <nav class="nav" aria-label="主导航">
    <a class="brand" href="/posts">{esc(SITE_NAME)}</a>
    <form class="nav-search" id="navSearchForm" action="/posts" method="get" role="search">
      <label class="sr-only" for="searchInput">全文搜索</label>
      <div class="nav-search-box">
        <input id="searchInput" name="q" type="search" placeholder="搜索标题、正文、标签..." autocomplete="off">
        <button class="nav-search-submit" type="submit">搜索</button>
      </div>
    </form>
    <a class="active" href="/posts">笔记</a>
  </nav>
</header>
"""


PAGE_TAIL = """
</body>
</html>
"""


def render_post_html(title: str, date_str: str, tags: list[str], body_html: str, summary: str) -> str:
    tags_html = "".join(
        f'<a class="tag" href="{esc(tag_url(tag))}">#{esc(tag)}</a>' for tag in tags
    )
    return "".join(
        [
            render_page_head(title, summary or SITE_SUBTITLE),
            '<main class="post-wrap">',
            '<nav class="post-actions" aria-label="文章导航">',
            '<div class="post-action-group">',
            '<button class="post-action" type="button" onclick="if (history.length > 1) { history.back(); } else { location.href = \'/posts\'; }">← 返回上一页</button>',
            '<a class="post-action secondary" href="/posts">返回首页</a>',
            "</div>",
            "</nav>",
            '<div class="post-hero">',
            f"<h1>{esc(title)}</h1>",
            f'<time class="date" datetime="{esc(date_str)}">{esc(date_str)}</time>' if date_str else "",
            f'<div class="tags">{tags_html}</div>' if tags_html else "",
            "</div>",
            '<article class="article">',
            body_html,
            "</article>",
            "</main>",
            PAGE_TAIL,
        ]
    )


def render_initial_post_card(post: dict) -> str:
    tags_html = "".join(
        f'<a class="mini-tag" href="{esc(tag_url(tag))}" data-filter-tag="{esc(tag)}">#{esc(tag)}</a>'
        for tag in post["tags"]
    )
    return f"""
      <article class="post-card">
        <div class="post-meta">
          <time datetime="{esc(post["date"])}">{esc(post["date"] or "未标日期")}</time>
          <span class="dot">{esc(post["readingTime"])} 分钟读完</span>
        </div>
        <a class="post-title" href="{esc(post_url(post["slug"]))}">{esc(post["title"])}</a>
        <p class="post-summary">{esc(post["summary"])}</p>
        {f'<div class="post-tags">{tags_html}</div>' if tags_html else ""}
      </article>
    """


def render_initial_groups(posts: list[dict]) -> str:
    if not posts:
        return ""

    groups: dict[str, list[dict]] = {}
    for post in posts:
        groups.setdefault(post["month"], []).append(post)

    sections = []
    for month, group_posts in groups.items():
        cards = "".join(render_initial_post_card(post) for post in group_posts)
        sections.append(
            f"""
            <section class="month-section">
              <h2 class="month-title">
                <span><a href="{esc(month_url(month))}">{esc(month_label(month))}</a></span>
                <span>{len(group_posts)} 篇</span>
              </h2>
              <div class="post-list">{cards}</div>
            </section>
            """
        )
    return "".join(sections)


def render_index_html(posts: list[dict]) -> str:
    tag_count = len({tag for post in posts for tag in post["tags"]})
    month_count = len({post["month"] for post in posts})
    latest_date = posts[0]["date"] if posts else "-"
    posts_payload = [
        {
            "slug": post["slug"],
            "title": post["title"],
            "date": post["date"],
            "summary": post["summary"],
            "tags": post["tags"],
            "month": post["month"],
            "monthLabel": post["monthLabel"],
            "readingTime": post["readingTime"],
            "content": post["content"],
            "searchText": post["searchText"],
        }
        for post in posts
    ]

    initial_posts = render_initial_groups(posts)

    return "".join(
        [
            render_page_head("笔记", "全文搜索、标签过滤和时间归档。"),
            '<main class="home-shell">',
            '<section class="index-strip" aria-label="笔记索引概览">',
            '<div><p class="eyebrow">Notebook Index</p><h1>笔记</h1><p>搜索在上方，归类在左侧，结果在这里直接展开。</p></div>',
            '<div class="index-metrics">',
            f'<span class="index-metric">{len(posts)} 篇公开笔记</span>',
            f'<span class="index-metric">{tag_count} 个标签</span>',
            f'<span class="index-metric">{month_count} 个月份</span>',
            f'<span class="index-metric">最近 {esc(latest_date)}</span>',
            "</div>",
            "</section>",
            '<section class="index-toolbar" aria-label="结果工具栏">',
            '<div class="search-meta"><span id="resultCount" aria-live="polite">显示 '
            + str(len(posts))
            + " / "
            + str(len(posts))
            + ' 篇</span><span class="shortcut">按 <kbd>/</kbd> 聚焦导航栏搜索，筛选状态会同步到地址栏</span></div>',
            '<div class="index-toolbar-controls">',
            '<label class="sr-only" for="sortSelect">排序</label>',
            '<select id="sortSelect" aria-label="排序"><option value="new">最新优先</option><option value="old">最早优先</option><option value="title">标题排序</option></select>',
            '<button class="clear-btn" id="clearFilters" type="button">清除</button>',
            "</div>",
            "</section>",
            '<section class="content-grid">',
            '<aside class="sidebar" aria-label="筛选器">',
            '<div class="side-card"><h2>标签归类</h2><div class="chip-stack" id="tagFilters"></div></div>',
            '<div class="side-card"><h2>时间归档</h2><div class="archive-stack" id="archiveFilters"></div></div>',
            "</aside>",
            '<div class="results-area">',
            '<div class="active-filters" id="activeFilters" aria-live="polite"></div>',
            f'<div id="postList">{initial_posts}</div>',
            '<div class="empty" id="emptyState" hidden><strong>没有匹配的笔记</strong><span>换个关键词，或清除标签 / 时间筛选再试试。</span></div>',
            "</div>",
            "</section>",
            f'<script id="posts-data" type="application/json">{safe_json(posts_payload)}</script>',
            f"<script>{INDEX_SCRIPT}</script>",
            "</main>",
            PAGE_TAIL,
        ]
    )


def build(include_drafts: bool = False) -> None:
    POSTS_SRC.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(POSTS_SRC.glob("*.md"), reverse=True)
    posts: list[dict] = []
    markdown = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists", "footnotes"])

    for md_path in md_files:
        if md_path.name == "README.md":
            continue
        try:
            post = frontmatter.load(md_path)
        except Exception as exc:
            print(f"[WARN] Skip {md_path.name}: {exc}")
            continue

        if post.get("draft", False) and not include_drafts:
            print(f"[SKIP] Draft: {md_path.name}")
            continue

        title = str(post.get("title", "")).strip()
        if not title:
            print(f"[WARN] Skip {md_path.name}: missing title")
            continue

        slug = str(post.get("slug") or md_path.stem).strip()
        date_str = format_date(post.get("date", ""))
        tags = normalize_tags(post.get("tags", []))
        raw_body = str(post)
        body_html = markdown(raw_body)
        body_text = markdown_to_text(raw_body)
        summary = summarize(str(post.get("summary", "")).strip() or body_text)
        post_month = month_key(date_str)
        search_text = compact_text(" ".join([title, date_str, summary, " ".join(tags), body_text])).lower()

        post_html = render_post_html(title, date_str, tags, body_html, summary)
        (OUT_DIR / f"{slug}.html").write_text(post_html, encoding="utf-8")
        print(f"[OK] {md_path.name} -> static/posts/{slug}.html")

        posts.append(
            {
                "slug": slug,
                "title": title,
                "date": date_str,
                "summary": summary,
                "tags": tags,
                "month": post_month,
                "monthLabel": month_label(post_month),
                "readingTime": reading_time(body_text),
                "content": body_text,
                "searchText": search_text,
            }
        )

    posts.sort(key=lambda item: (item["date"], item["slug"]), reverse=True)

    index_html = render_index_html(posts)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"\n[OK] Index: static/posts/index.html ({len(posts)} posts)")

    public_payload = {"posts": posts, "count": len(posts)}
    json_text = json.dumps(public_payload, ensure_ascii=False, indent=2)
    (PUBLIC_DIR / "posts.json").write_text(json_text, encoding="utf-8")
    (STATIC_DIR / "posts.json").write_text(json_text, encoding="utf-8")
    print("[OK] JSON: data/public/posts.json and static/posts.json")
    print(f"\n[DONE] Built {len(posts)} posts")


if __name__ == "__main__":
    build(include_drafts="--draft" in sys.argv)
