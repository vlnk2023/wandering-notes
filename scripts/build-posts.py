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
.side-card,
.post-card {
  border:1px solid rgba(230,222,208,.9);
  background:rgba(255,253,248,.86);
  box-shadow:var(--shadow-soft);
}
.facet-chip,
.filter-pill button {
  border:none;
  cursor:pointer;
}
.content-grid {
  display:grid;
  grid-template-columns:220px minmax(0, 1fr);
  gap:22px;
  align-items:start;
  padding:28px 0 64px;
}
.sidebar {
  position:sticky;
  top:86px;
  display:grid;
  gap:16px;
}
.side-card {
  border-radius:18px;
  padding:14px;
}
.side-card h2 {
  margin:0 0 10px;
  color:var(--muted);
  font-size:15px;
  font-weight:900;
  letter-spacing:.02em;
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
  margin:0 0 14px;
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
  .content-grid {
    grid-template-columns:1fr;
    padding-top:18px;
  }
  .sidebar {
    position:static;
  }
  .sidebar {
    display:block;
  }
  .archive-stack { display:flex; gap:8px; overflow-x:auto; padding-bottom:2px; scrollbar-width:thin }
  .archive-button { width:auto; flex:0 0 auto }
}
@media (max-width:680px) {
  .nav { min-height:0; padding:10px 18px; gap:10px 14px; flex-wrap:wrap }
  .nav-search { order:3; flex-basis:100%; max-width:none; margin-left:0 }
  .home-shell,
  .wrap,
  .post-wrap { padding:0 18px }
  .content-grid { gap:14px; padding-top:14px }
  .side-card { margin:0 -2px; padding:12px; border-radius:16px }
  .side-card h2 { font-size:14px }
  .active-filters { min-height:0 }
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
    archiveFilters: document.getElementById("archiveFilters"),
    activeFilters: document.getElementById("activeFilters"),
    postList: document.getElementById("postList"),
    empty: document.getElementById("emptyState")
  };

  const state = { q: "", tag: "", month: "" };

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

  function readUrl() {
    const params = new URLSearchParams(location.search);
    state.q = params.get("q") || "";
    state.tag = params.get("tag") || "";
    state.month = params.get("month") || "";
  }

  function writeUrl(replace = false) {
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.tag) params.set("tag", state.tag);
    if (state.month) params.set("month", state.month);
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
    const monthCounts = [...countBy(posts, (post) => post.month).entries()].sort((a, b) => b[0].localeCompare(a[0]));

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
      return b.date.localeCompare(a.date);
    });

    return { list, tokens };
  }

  function apply(replaceUrl = false) {
    els.search.value = state.q;

    const { list, tokens } = filteredPosts();
    renderFacets();
    renderActiveFilters();
    renderPosts(list, tokens);
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


def edit_url(source_path: str, slug: str) -> str:
    params = f"path={quote(source_path, safe='')}&slug={quote(slug, safe='')}"
    return "/edit?" + params


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


def render_post_html(
    title: str,
    date_str: str,
    tags: list[str],
    body_html: str,
    summary: str,
    source_path: str,
    slug: str,
) -> str:
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
            f'<a class="post-action secondary" href="{esc(edit_url(source_path, slug))}">编辑本文</a>',
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
            '<section class="content-grid">',
            '<aside class="sidebar" aria-label="时间归档">',
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

        source_path = md_path.relative_to(ROOT).as_posix()
        post_html = render_post_html(title, date_str, tags, body_html, summary, source_path, slug)
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
                "sourcePath": source_path,
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
