#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 sections/*.body.html 生成《大模型训练入门》书籍页（小白可读小节版）。"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTIONS = ROOT / "sections"
SRC_IMAGES = ROOT.parent / "images"

CHAPTERS = [
    {
        "body": "ch01.body.html",
        "out": "ch01.html",
        "num": "01",
        "title": "下一个字符预测与交叉熵",
        "short": "下一个字符与 Loss",
        "lead": "给定前文猜下一个字符；用交叉熵衡量对错；对照本机曲线看懂训练在优化什么。",
    },
    {
        "body": "ch02.body.html",
        "out": "ch02.html",
        "num": "02",
        "title": "Embedding、Attention 与 MLP",
        "short": "模型前向结构",
        "lead": "字符 → 向量 → 因果 Attention 汇总前文 → MLP 加工 → 65 维分数 → Softmax。",
    },
    {
        "body": "ch03.body.html",
        "out": "ch03.html",
        "num": "03",
        "title": "反向传播与 AdamW",
        "short": "梯度与优化器",
        "lead": "反向传播算往哪改；AdamW 负责怎么改；学习率决定改多大。",
    },
    {
        "body": "ch04.body.html",
        "out": "ch04.html",
        "num": "04",
        "title": "训练循环全景",
        "short": "train.py 整圈对照",
        "lead": "把第 1–3 章概念，按 train.py 真实执行顺序串成一条闭环。",
    },
    {
        "body": "ch05.body.html",
        "out": "ch05.html",
        "num": "05",
        "title": "采样生成与过拟合",
        "short": "采样与曲线解读",
        "lead": "训练抬高真实下一字符概率；生成按学到的分布逐字外推，并用曲线判断过拟合。",
    },
]

APPENDIX = {
    "body": "practice.body.html",
    "out": "practice.html",
    "num": "附",
    "title": "本机实战过程总结",
    "short": "实战记录",
    "lead": "按真实操作顺序记录环境、数据、两轮训练、画曲线与采样，便于复现。",
}

BOOK_CSS = r"""
:root {
  --llm-bg: #f6f7f9;
  --llm-sidebar: #f6f7f9;
  --llm-ink: #15202b;
  --llm-muted: #6b7785;
  --llm-line: #e2e6eb;
  --llm-active-bg: #e8eef3;
  --llm-accent: #3db8a9;
  --llm-accent-ink: #0d3d38;
}
body.llm-book {
  background: var(--llm-bg) !important;
  color: var(--llm-ink);
  font-size: 17px;
  line-height: 1.75;
}
body.llm-book a { color: #0f5c54; }
body.llm-book a:hover { color: var(--llm-ink); }
.llm-shell {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
}
.llm-sidebar {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow-y: auto;
  padding: 1.25rem 1rem 1.5rem;
  border-right: 1px solid var(--llm-line);
  background: var(--llm-sidebar);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.llm-back {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--llm-muted) !important;
  text-decoration: none;
  font-size: 0.88rem;
}
.llm-back:hover { color: var(--llm-ink) !important; }
.llm-toc-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--llm-muted);
  letter-spacing: 0.06em;
  margin: 0.35rem 0 0.15rem;
}
.llm-chapters {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.llm-chapters a {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: 0.55rem;
  align-items: baseline;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  text-decoration: none;
  color: var(--llm-muted);
  font-size: 0.92rem;
  line-height: 1.35;
  border-left: 3px solid transparent;
}
.llm-chapters a:hover {
  background: rgba(0,0,0,0.03);
  color: var(--llm-ink);
}
.llm-chapters a.active {
  background: var(--llm-active-bg);
  color: var(--llm-ink);
  font-weight: 600;
  border-left-color: var(--llm-accent);
}
.llm-chapters .num {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: inherit;
  opacity: 0.85;
}
.llm-sec-toc {
  list-style: none;
  margin: 0.15rem 0 0.35rem;
  padding: 0 0 0 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}
.llm-sec-toc a {
  display: block;
  padding: 0.28rem 0.55rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--llm-muted);
  font-size: 0.78rem;
  line-height: 1.35;
}
.llm-sec-toc a:hover {
  background: rgba(0,0,0,0.03);
  color: var(--llm-ink);
}
.llm-side-foot {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--llm-line);
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.llm-side-foot a {
  color: var(--llm-muted);
  text-decoration: none;
  font-size: 0.88rem;
}
.llm-side-foot a:hover { color: var(--llm-ink); }
.llm-main { min-width: 0; display: flex; flex-direction: column; }
.llm-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 2rem;
  border-bottom: 1px solid var(--llm-line);
  background: rgba(246,247,249,0.92);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 5;
}
.llm-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  color: var(--llm-ink);
  font-weight: 650;
  font-size: 0.98rem;
  letter-spacing: -0.02em;
}
.llm-brand-mark {
  width: 1.55rem;
  height: 1.55rem;
  border-radius: 6px;
  background: #15202b;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 0.68rem;
  font-weight: 700;
  font-family: var(--font-mono);
}
.llm-top-links { display: flex; gap: 1.1rem; flex-wrap: wrap; }
.llm-top-links a {
  color: var(--llm-muted);
  text-decoration: none;
  font-size: 0.9rem;
}
.llm-top-links a:hover { color: var(--llm-ink); }
.llm-article {
  width: min(760px, calc(100% - 3rem));
  margin: 0 auto;
  padding: 1.75rem 0 4rem;
}
.llm-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  color: var(--llm-muted);
  font-size: 0.88rem;
  margin-bottom: 1.25rem;
}
.llm-chapter-head {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  margin-bottom: 0.85rem;
}
.llm-chapter-num {
  flex: 0 0 auto;
  min-width: 2.4rem;
  height: 2.4rem;
  padding: 0 0.55rem;
  border-radius: 8px;
  background: var(--llm-accent);
  color: var(--llm-accent-ink);
  display: grid;
  place-items: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.95rem;
}
.llm-chapter-head h1 {
  margin: 0;
  font-size: clamp(1.55rem, 3vw, 2.15rem);
  border: none;
  padding: 0;
  letter-spacing: -0.03em;
}
.llm-content .lead { margin-top: 0; }
.llm-content h2 {
  border-top: none;
  padding-top: 0.2rem;
  margin-top: 2.2rem;
  scroll-margin-top: 5rem;
}
.llm-content h2::before {
  content: "";
  display: block;
  width: 2rem;
  height: 3px;
  background: var(--llm-accent);
  margin-bottom: 0.75rem;
  border-radius: 2px;
}
.llm-onpage {
  margin: 1rem 0 1.5rem;
  padding: 0.9rem 1rem;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--llm-line);
}
.llm-onpage .label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--llm-muted);
  letter-spacing: 0.04em;
  margin-bottom: 0.45rem;
}
.llm-onpage ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.25rem;
}
.llm-onpage a { text-decoration: none; }
.llm-footer-nav {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 2.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--llm-line);
}
.llm-footer-nav a {
  text-decoration: none;
  color: var(--llm-ink);
  font-weight: 600;
}
@media (max-width: 920px) {
  .llm-shell { grid-template-columns: 1fr; }
  .llm-sidebar {
    position: static;
    height: auto;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid var(--llm-line);
  }
  .llm-article { width: min(760px, calc(100% - 2rem)); }
  .llm-topbar { padding: 0.85rem 1rem; }
}
"""


def load(name: str) -> str:
    return (SECTIONS / name).read_text(encoding="utf-8")


def inject_assets(body: str) -> str:
    if "<!--VOCAB-->" in body:
        body = body.replace("<!--VOCAB-->", load("vocab_panel.html"))
    if "<!--LOOP_FIGURE-->" in body:
        body = body.replace("<!--LOOP_FIGURE-->", load("loop_figure.html"))
    if "<!--GEN_FIGURE-->" in body:
        body = body.replace("<!--GEN_FIGURE-->", load("gen_figure.html"))
    return body


def extract_sections(body: str) -> list[tuple[str, str]]:
    """从 h2 提取 (id, title) 作为小节目录。"""
    out = []
    for m in re.finditer(r'<h2\s+id="([^"]+)">(.*?)</h2>', body, re.S):
        title = re.sub(r"<[^>]+>", "", m.group(2))
        title = re.sub(r"\s+", " ", title).strip()
        # 跳过自测可保留；本章小结也保留
        out.append((m.group(1), title))
    return out


def toc_html(active: str, section_links: list[tuple[str, str]] | None = None) -> str:
    items = []
    pages = CHAPTERS + [APPENDIX]
    for ch in pages:
        cls = ' class="active"' if ch["out"] == active else ""
        items.append(
            f'<li><a href="{ch["out"]}"{cls}>'
            f'<span class="num">{ch["num"]}</span>'
            f'<span>{ch["short"]}</span></a></li>'
        )
        if ch["out"] == active and section_links:
            sub = []
            for sid, title in section_links:
                # 侧栏只放正文小节，压缩自测/小结可选都放
                short = title
                if len(short) > 18:
                    short = short[:17] + "…"
                sub.append(f'<li><a href="#{sid}">{short}</a></li>')
            items.append('<ul class="llm-sec-toc">' + "".join(sub) + "</ul>")
    return "\n        ".join(items)


def onpage_toc(section_links: list[tuple[str, str]]) -> str:
    if not section_links:
        return ""
    lis = "\n".join(
        f'      <li><a href="#{sid}">{title}</a></li>' for sid, title in section_links
    )
    return f"""
        <nav class="llm-onpage" aria-label="本章小节">
          <div class="label">本章小节</div>
          <ul>
{lis}
          </ul>
        </nav>"""


def page_shell(
    *,
    title: str,
    num: str,
    active: str,
    lead: str,
    content: str,
    section_links: list[tuple[str, str]],
    prev_link: tuple[str, str] | None,
    next_link: tuple[str, str] | None,
) -> str:
    prev_html = f'<a href="{prev_link[0]}">← {prev_link[1]}</a>' if prev_link else "<span></span>"
    next_html = f'<a href="{next_link[0]}">{next_link[1]} →</a>' if next_link else "<span></span>"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · 大模型训练入门</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'\\\\(',right:'\\\\)',display:false}},{{left:'$',right:'$',display:false}}]}})"></script>
  <style>{BOOK_CSS}</style>
</head>
<body class="llm-book">
  <div class="llm-shell">
    <aside class="llm-sidebar" aria-label="目录">
      <a class="llm-back" href="index.html">← 返回目录</a>
      <div class="llm-toc-label">目录</div>
      <ul class="llm-chapters">
        {toc_html(active, section_links)}
      </ul>
      <div class="llm-side-foot">
        <a href="index.html">总目录</a>
        <a href="cover.html">封面</a>
      </div>
    </aside>
    <div class="llm-main">
      <header class="llm-topbar">
        <a class="llm-brand" href="index.html">
          <span class="llm-brand-mark">LLM</span>
          大模型训练入门
        </a>
        <div class="llm-top-links">
          <a href="index.html">目录</a>
          <a href="practice.html">实战</a>
        </div>
      </header>
      <article class="llm-article">
        <div class="llm-meta">
          <div>大模型训练入门 · 基于 nanoGPT</div>
        </div>
        <div class="llm-chapter-head">
          <div class="llm-chapter-num">{num}</div>
          <h1>{title}</h1>
        </div>
        <p class="lead">{lead}</p>
        {onpage_toc(section_links)}
        <div class="llm-content">
{content}
        </div>
        <div class="llm-footer-nav">
          {prev_html}
          {next_html}
        </div>
      </article>
    </div>
  </div>
</body>
</html>
"""


def copy_images() -> None:
    dst = ROOT / "images"
    dst.mkdir(exist_ok=True)
    for name in ("loss_curve_v1_lite.png", "loss_curve_v2_full.png"):
        shutil.copy2(SRC_IMAGES / name, dst / name)


def build() -> None:
    copy_images()
    pages = CHAPTERS + [APPENDIX]
    for i, ch in enumerate(pages):
        body = inject_assets(load(ch["body"]))
        sections = extract_sections(body)
        prev_link = ("index.html", "目录") if i == 0 else (pages[i - 1]["out"], pages[i - 1]["short"])
        next_link = None if i == len(pages) - 1 else (pages[i + 1]["out"], pages[i + 1]["short"])
        html = page_shell(
            title=ch["title"],
            num=ch["num"],
            active=ch["out"],
            lead=ch["lead"],
            content=body,
            section_links=sections,
            prev_link=prev_link,
            next_link=next_link,
        )
        (ROOT / ch["out"]).write_text(html, encoding="utf-8")
        print("wrote", ch["out"], f"({len(sections)} sections)")


if __name__ == "__main__":
    build()
