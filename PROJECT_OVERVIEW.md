# wandering-notes

## 项目目标介绍

- 一个轻量 Markdown 笔记/博客发布系统。
- 项目通过 Python 构建脚本将 `data/posts/` 中的 Markdown 文章生成静态 HTML、文章索引和 JSON 数据，并通过 Vercel 部署。
- 同时包含 `api/auth.js`、`api/post.js` 和 `static/edit/`，用于在线编辑、鉴权或文章更新的轻量后台能力。

## 进度状态

- 当前状态：可用静态站点/内容持续积累
- 最近更新：2026-05-24
- 关键入口：
  - `data/posts/`：Markdown 原文，主题包括 AI 工具、知识管理、情感/人格产品、代理、部署教程等
  - `scripts/build-posts.py`：构建静态文章、首页和 `posts.json`
  - `scripts/new-post.py`、`scripts/new-post.ps1`：新建文章脚本
  - `static/posts/`：生成后的 HTML 页面
  - `static/admin/`、`static/edit/`：后台/编辑页面
  - `api/auth.js`、`api/post.js`：Vercel API

## 遗留问题/待办

- [ ] 明确哪些 `static/posts/*.html` 是生成产物，避免手工改动丢失
- [ ] 给在线编辑 API 补充鉴权配置、环境变量和部署说明
- [ ] 整理文章标签、分类、摘要和日期规范
- [ ] 确认大体量文章生成后的性能、索引大小和移动端阅读体验
- [ ] 与 `emo1/other` 中的内容建立迁移或同步规则，避免重复维护

## 备注

- 这是内容输出和个人资料发布的主线目录之一。适合作为“把本地 Markdown 变成在线知识库”的轻量底座。
