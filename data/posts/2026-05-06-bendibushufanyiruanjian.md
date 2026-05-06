---
title: TranslateGemma是专门的本地部署翻译模型
date: 2026-05-06
tags: [技术笔记]
summary: "Google 2026 年发布的 TranslateGemma（基于 Gemma 3，有 4B/12B/27B 版本）是专门的翻译模型，在 WMT 等基准上表现优秀，尤其适合新闻语气、自然度、上下文理解，支持 55 种语言。"
---

##  Ollama + TranslateGemma (12B 或 4B)（2026 年质量最佳平衡）
为什么推荐：Google 2026 年发布的 TranslateGemma（基于 Gemma 3，有 4B/12B/27B 版本）是专门的翻译模型，在 WMT 等基准上表现优秀，尤其适合新闻语气、自然度、上下文理解（比传统 MT 更像 human journalist）。支持 55 种语言，覆盖大多数 TG 频道。
优点：输出更自然、可通过 Prompt 控制风格（“professional news English, keep facts and tone”）、结构化输出（JSON）、易用。
缺点：比 CTranslate2 稍慢（但 800 条仍极快）。
实施：
ollama pull translategemma:12b（或 :4b 如果显存有限）。
强 Prompt 示例（结构化输出）：
text

You are a professional news translator. Translate the following {source_lang} news title and summary into natural, journalistic English. Preserve facts, names, and tone. Do not add commentary.
Return only valid JSON: {"title": "...", "summary": "..."}

Text: {combined_text}
用 asyncio + Ollama Python 库并发调用（4-8 个并发视硬件）。
12B 在消费级 GPU（RTX 3060+）或 Mac Metal 上运行良好，4B 可纯 CPU。
