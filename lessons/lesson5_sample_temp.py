"""
第5课：Temperature 如何改变采样分布
运行：
  cd nanoGPT && source .venv/bin/activate
  python lessons/lesson5_sample_temp.py
"""
import numpy as np
import torch
import torch.nn.functional as F

# 假造 5 个字符的 logits（分数越高越被偏好）
# 真实训练里这些分数来自 lm_head：logits = x @ W.T（见 lesson1 / lesson2）
chars = ["a", "b", "c", "d", "e"]
logits = torch.tensor([2.0, 1.2, 0.5, -0.3, -1.0])

print("=" * 60)
print("原始 logits（示意；真实来自 lm_head，不是 Softmax）:", logits.tolist())
print("字符:      ", chars)


def show_temp(T: float):
    probs = F.softmax(logits / T, dim=-1).numpy()
    print(f"\n--- temperature T={T} ---")
    for c, p in zip(chars, probs):
        bar = "█" * int(p * 40)
        print(f"  {c}: {p:.3f} {bar}")
    print(f"  熵(越大越均匀) ≈ {-np.sum(probs * np.log(probs + 1e-12)):.3f}")


for T in [0.2, 0.8, 1.0, 2.0]:
    show_temp(T)

print(
    """
============================================================
读法:
  T 小 → 概率集中在最高分字符 → 生成更保守、易重复
  T 大 → 分布变平 → 更随机、更多样，也可能更胡言
sample.py 默认 temperature=0.8

过拟合提醒:
  train loss 持续下降而 val loss 上升 → 模型在「背」训练集
  生成可能像训练片段，但换 prompt 就崩
============================================================
打开 学习笔记/lesson05.html 对照阅读
"""
)
