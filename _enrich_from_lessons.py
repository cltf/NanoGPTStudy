#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以 lesson / practice 全文为底稿生成更丰富的书籍章节：
- 保留原课全部细节（公式、词表、深潜、图、自测）
- 按书籍小节编号 1.1 / 2.1 …
- 每章增加「本章导读」与「扩展阅读」书本层内容
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTIONS = ROOT / "sections"
NOTES = ROOT.parent


def extract_lesson(name: str) -> str:
    t = (NOTES / f"{name}.html").read_text(encoding="utf-8")
    m = re.search(r"</nav>\s*(.*?)\s*<div class=\"footer-nav\">", t, re.S)
    if not m:
        raise ValueError(name)
    body = m.group(1)
    body = re.sub(r'<span class="badge">.*?</span>\s*', "", body, count=1, flags=re.S)
    body = re.sub(r"<h1>.*?</h1>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r'<p class="lead">.*?</p>\s*', "", body, count=1, flags=re.S)
    repl = {
        "lesson01.html": "ch01.html",
        "lesson02.html": "ch02.html",
        "lesson03.html": "ch03.html",
        "lesson04.html": "ch04.html",
        "lesson05.html": "ch05.html",
        'href="index.html"': 'href="index.html"',
        'src="images/': 'src="images/',
    }
    for a, b in repl.items():
        body = body.replace(a, b)
    body = re.sub(r"第\s*([1-5])\s*课", r"第\1章", body)
    return body.strip()


def replace_h2(body: str, mapping: list[tuple[str, str, str]]) -> str:
    """mapping: (old_substring_in_h2_text, new_id, new_title_with_number)"""

    def replacer(m: re.Match) -> str:
        plain = re.sub(r"<[^>]+>", "", m.group(0))
        plain = re.sub(r"\s+", " ", plain).strip()
        for old, sid, title in mapping:
            if old in plain:
                return f'<h2 id="{sid}">{title}</h2>'
        return m.group(0)

    return re.sub(r"<h2[^>]*>.*?</h2>", replacer, body, flags=re.S)


def wrap_deep_dive_as_section(body: str, sid: str, title: str) -> str:
    """若正文以 deep-dive section 开头，在其前插入 h2，并把内部首批 h3 保留。"""
    m = re.search(r'(<section class="deep-dive".*?</section>)', body, re.S)
    if not m:
        return body
    block = m.group(1)
    # 避免 deep-dive 内已有的结构被丢掉；在 section 前加 h2
    inserted = f'<h2 id="{sid}">{title}</h2>\n{block}'
    return body[: m.start()] + inserted + body[m.end() :]


INTRO = {
    "ch01": """
<div class="card tip">
  <div class="label">本章导读</div>
  <p style="margin:0">本章按书籍顺序展开「下一字符 + 交叉熵」：先把数据与词表看清，再进入自回归与似然，然后把 logits / Softmax / CrossEntropy 串成一条可核对流水线，最后对照本机真实 loss 曲线。读完应能独立讲清：<strong>训练到底在优化什么数字</strong>。</p>
</div>
""",
    "ch02": """
<div class="card tip">
  <div class="label">本章导读</div>
  <p style="margin:0">本章先建立 Embedding / Attention / MLP 的分工地图，再分别深入查表、因果注意力、残差块、lm_head 与 Softmax。目标不是背名词，而是能指着 NanoGPT 前向链路说出<strong>每个盒子的输入输出</strong>。</p>
</div>
""",
    "ch03": """
<div class="card tip">
  <div class="label">本章导读</div>
  <p style="margin:0">本章把「反向传播 · AdamW · 学习率」写成训练三件套：人话总览 → 机制拆解 → 与 NanoGPT / 大模型预训练的对照。读完应能解释：<strong>梯度从哪来、参数怎么改、步子为什么先热身再衰减</strong>。</p>
</div>
""",
    "ch04": """
<div class="card tip">
  <div class="label">本章导读</div>
  <p style="margin:0">本章是把前三章零件装进 <code>train.py</code> 的「总装配图」。请对照源码阅读：循环外初始化、while True 内取数 / 前向 / 反向 / 评估 / 存盘，以及终端两行日志各自对应哪一段代码。</p>
</div>
""",
    "ch05": """
<div class="card tip">
  <div class="label">本章导读</div>
  <p style="margin:0">本章讲「训完之后怎么用」：生成路径、temperature、top-k，以及如何用 train/val 曲线判断过拟合。重点是建立判断力——<strong>生成难看不等于公式错，曲线分叉也不等于代码坏了</strong>。</p>
</div>
""",
    "practice": """
<div class="card tip">
  <div class="label">附录导读</div>
  <p style="margin:0">本附录保留完整本机实战记录：环境坑、数据准备、轻量 v1 / 加强 v2、采样与时间线，并和五章理论对照。它是「可复现实验手册」，建议与各章交叉阅读。</p>
</div>
""",
}

EXPAND = {
    "ch01": """
<h2 id="s1-expand">1.6 扩展：从小模型到大模型，不变的是什么</h2>
<p>字符级莎士比亚和千亿参数大模型，表面上差很远，但训练目标同构：</p>
<ul>
  <li>都在最大化「下一个 token」的似然（等价于最小化交叉熵 / NLL）</li>
  <li>都把离散符号变成向量，再经深层网络打出词表上的 logits</li>
  <li>评估时同样要同时看 train 与 held-out（val/test）曲线</li>
</ul>
<p>差别主要在：词表更大（子词 BPE）、上下文更长、层数与宽度更大、数据与算力工程更复杂。先把 NanoGPT 这条最小闭环吃透，再看大模型论文时会轻松很多。</p>
""",
    "ch02": """
<h2 id="s2-expand">2.8 扩展：和现代 LLM 结构的对照</h2>
<p>NanoGPT 的 Decoder-only Transformer 与今天主流 LLM（如 Llama / Qwen 一类）同属一族。阅读开源模型配置时，可主动寻找这些对应物：</p>
<ul>
  <li><code>n_embd</code> / hidden size：向量宽度</li>
  <li><code>n_head</code> / num attention heads：注意力头数</li>
  <li><code>n_layer</code>：堆叠多少个 Block</li>
  <li>RoPE 等位置编码：替换或增强本节的绝对位置嵌入</li>
</ul>
<p>先掌握本节的「因果自注意力 + MLP + 残差」，再去看旋转位置编码、GQA、SwiGLU，会是增量学习，而不是从零重来。</p>
""",
    "ch03": """
<h2 id="s3-expand">3.8 扩展：预训练里同一套旋钮如何被放大</h2>
<p>在大规模预训练报告里，你仍会反复看到：</p>
<ul>
  <li>AdamW（或变体）+ weight decay</li>
  <li>warmup + cosine / 多段衰减</li>
  <li>grad clip 与混合精度带来的数值稳定问题</li>
</ul>
<p>NanoGPT 是缩小版沙盘：参数少、步数少，但决策逻辑一致。调 lr 导致震荡、warmup 过短不稳——这些直觉可以直接迁移。</p>
""",
    "ch04": """
<h2 id="s4-expand">4.5 扩展：自己给 train.py 做「阅读标注」</h2>
<p>建议在编辑器里给 <code>train.py</code> 加五类书签（不必改逻辑，只为导航）：</p>
<ol>
  <li>配置与模型构建</li>
  <li><code>get_batch</code></li>
  <li>前向 <code>model(X, Y)</code> 与 <code>loss</code></li>
  <li><code>backward</code> / <code>clip</code> / <code>step</code></li>
  <li><code>estimate_loss</code> 与 checkpoint</li>
</ol>
<p>能不看笔记、只靠书签把一圈训练讲下来，第 4 章才算过关。</p>
""",
    "ch05": """
<h2 id="s5-expand">5.6 扩展：采样参数的调试清单</h2>
<p>生成效果不理想时，按这个顺序排查更省时间：</p>
<ol>
  <li>Loss 是否已从 ~4.1 明显下降？（没学会先别怪采样）</li>
  <li>是否过拟合？（val 已升，可回退更好 checkpoint）</li>
  <li>temperature 是否极端？（先回到 0.8～1.0）</li>
  <li>top-k 是否过小/过大？</li>
  <li>prompt 是否太短或超出模型能力（小模型字符级剧本）</li>
</ol>
<p>把「模型能力」和「解码策略」分开看，是使用一切生成式模型的基本功。</p>
""",
    "practice": "",
}


def move_quiz_to_end(body: str, expand: str, intro: str) -> str:
    """正文 → 扩展 → 自测题（保证自测在章末）。"""
    m = re.search(r'(<h2[^>]*id="[^"]*-quiz"[^>]*>.*)\Z', body, re.S)
    quiz = ""
    if m:
        quiz = m.group(1).strip()
        body = body[: m.start()].rstrip()
    parts = [intro.strip(), body.strip()]
    if expand.strip():
        parts.append(expand.strip())
    if quiz:
        parts.append(quiz)
    return "\n\n".join(parts) + "\n"


def build_ch01() -> str:
    body = extract_lesson("lesson01")
    body = replace_h2(
        body,
        [
            ("1. 数据长什么样", "s1-1", "1.1 数据长什么样"),
            ("2. 数学：自回归分解", "s1-2", "1.2 数学：自回归分解"),
            ("3. Loss 到底是什么数？", "s1-3", "1.3 Loss 到底是什么数？"),
            ("4. 和你训练曲线的对照", "s1-4", "1.4 和你训练曲线的对照"),
            ("5. 每个训练 step 在优化什么", "s1-5", "1.5 每个训练 step 在优化什么"),
            ("自测题", "s1-quiz", "自测题"),
        ],
    )
    return move_quiz_to_end(body, EXPAND["ch01"], INTRO["ch01"])


def build_ch02() -> str:
    body = extract_lesson("lesson02")
    body = wrap_deep_dive_as_section(body, "s2-1", "2.1 人话版：Embedding / Attention / MLP")
    body = replace_h2(
        body,
        [
            ("总览：前向传播链路", "s2-2", "2.2 总览：前向传播链路"),
            ("1. Embedding：离散字符 → 连续向量", "s2-3", "2.3 Embedding：离散字符 → 连续向量"),
            ("2. Attention：让每个位置「看见」前文", "s2-4", "2.4 Attention：让每个位置「看见」前文"),
            ("3. Block = Attn + MLP + 残差", "s2-5", "2.5 Block = Attn + MLP + 残差"),
            ("4. lm_head：向量 → 65 个分数", "s2-6", "2.6 lm_head：向量 → 65 个分数"),
            ("5. Softmax：原始分数 → 合法概率", "s2-7", "2.7 Softmax：原始分数 → 合法概率"),
            ("自测题", "s2-quiz", "自测题"),
        ],
    )
    return move_quiz_to_end(body, EXPAND["ch02"], INTRO["ch02"])


def build_ch03() -> str:
    body = extract_lesson("lesson03")
    body = wrap_deep_dive_as_section(body, "s3-1", "3.1 人话版：反向传播 / AdamW / 学习率")
    body = replace_h2(
        body,
        [
            ("1. 前向有了，还缺「怎么改参数」", "s3-2", "3.2 前向有了，还缺「怎么改参数」"),
            ("2. 反向传播（Backpropagation）在干什么", "s3-3", "3.3 反向传播在干什么"),
            ("3. 为什么不只用「梯度下降」，而用 AdamW", "s3-4", "3.4 为什么用 AdamW"),
            ("4. 学习率调度：warmup + cosine", "s3-5", "3.5 学习率调度：warmup + cosine"),
            ("5. 梯度裁剪（grad clip）", "s3-6", "3.6 梯度裁剪（grad clip）"),
            ("6. 和 loss 曲线的关系", "s3-7", "3.7 和 loss 曲线的关系"),
            ("自测题", "s3-quiz", "自测题"),
        ],
    )
    return move_quiz_to_end(body, EXPAND["ch03"], INTRO["ch03"])


def build_ch04() -> str:
    body = extract_lesson("lesson04")
    body = replace_h2(
        body,
        [
            ("总览：while True 里发生了什么", "s4-1", "4.1 总览：while True 里发生了什么"),
            ("步骤详解（人话版）", "s4-2", "4.2 步骤详解（人话版）"),
            ("终端两行日志分别是什么", "s4-3", "4.3 终端两行日志分别是什么"),
            ("你当时完整命令在循环中的效果", "s4-4", "4.4 完整训练命令在循环中的效果"),
            ("自测题", "s4-quiz", "自测题"),
        ],
    )
    return move_quiz_to_end(body, EXPAND["ch04"], INTRO["ch04"])


def build_ch05() -> str:
    body = extract_lesson("lesson05")
    body = replace_h2(
        body,
        [
            ("1. 生成在代码里怎么走", "s5-1", "5.1 生成在代码里怎么走"),
            ("2. Temperature（温度）", "s5-2", "5.2 Temperature（温度）"),
            ("3. Top-k", "s5-3", "5.3 Top-k"),
            ("4. 如何读 train loss / val loss 曲线", "s5-4", "5.4 如何读 train / val loss 曲线"),
            ("5. 生成质量差 ≠ 训练公式错", "s5-5", "5.5 生成质量差 ≠ 训练公式错"),
            ("自测题", "s5-quiz", "自测题"),
        ],
    )
    return move_quiz_to_end(body, EXPAND["ch05"], INTRO["ch05"])


def build_practice() -> str:
    body = extract_lesson("practice")
    body = replace_h2(
        body,
        [
            ("0. 环境准备（踩过的坑）", "p0", "A.1 环境准备（踩过的坑）"),
            ("1. 数据：莎士比亚字符级", "p1", "A.2 数据：莎士比亚字符级"),
            ("2. 第一轮训练：轻量版 v1（快速走通）", "p2", "A.3 第一轮训练：轻量版 v1"),
            ("3. 第二轮训练：加强版 v2（效果更好，但过拟合）", "p3", "A.4 第二轮训练：加强版 v2"),
            ("4. 怎么用训好的模型", "p4", "A.5 怎么用训好的模型"),
            ("5. 实战时间线（按你真实做过的事）", "p5", "A.6 实战时间线"),
            ("6. 和五课理论的对照", "p6", "A.7 和五章理论的对照"),
            ("7. 一句话结论", "p7", "A.8 一句话结论"),
        ],
    )
    # 五课 → 五章 already
    body = body.replace("和五课理论", "和五章理论")
    return INTRO["practice"] + "\n" + body


def main() -> None:
    SECTIONS.mkdir(exist_ok=True)
    writers = {
        "ch01.body.html": build_ch01,
        "ch02.body.html": build_ch02,
        "ch03.body.html": build_ch03,
        "ch04.body.html": build_ch04,
        "ch05.body.html": build_ch05,
        "practice.body.html": build_practice,
    }
    for name, fn in writers.items():
        text = fn()
        (SECTIONS / name).write_text(text, encoding="utf-8")
        # count h2
        hs = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', text, re.S)
        print(name, "chars", len(text), "h2", len(hs))
        for sid, title in hs[:12]:
            print(" ", sid, re.sub(r"<[^>]+>", "", title)[:50])


if __name__ == "__main__":
    main()
