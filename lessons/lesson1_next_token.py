"""
第1课：自回归下一个字符预测 + Cross-Entropy Loss
运行：
  cd nanoGPT && source .venv/bin/activate
  python lessons/lesson1_next_token.py
"""
import os
import pickle
import numpy as np
import torch
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# 1) 读你已经准备好的莎士比亚字符数据
# ---------------------------------------------------------------------------
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(root, "data", "shakespeare_char")

with open(os.path.join(data_dir, "meta.pkl"), "rb") as f:
    meta = pickle.load(f)

stoi, itos = meta["stoi"], meta["itos"]
vocab_size = meta["vocab_size"]  # 65
print("=" * 60)
print("【1. 词表】字符级 GPT 的「词」就是单个字符")
print(f"vocab_size = {vocab_size}")
print(f"前20个字符: {[itos[i] for i in range(20)]}")

# ---------------------------------------------------------------------------
# 2) 取一小段真实文本，看「输入 X → 标签 Y」怎么构造
# ---------------------------------------------------------------------------
data = np.memmap(os.path.join(data_dir, "train.bin"), dtype=np.uint16, mode="r")
# 固定起点，方便你对照阅读
start = 1000
T = 16  # 上下文长度（真实训练里是 256）
chunk = data[start : start + T + 1].astype(np.int64)

chars = [itos[int(i)] for i in chunk]
print("\n" + "=" * 60)
print("【2. 一段真实文本】")
print("原文:", repr("".join(chars)))

# 训练时的关键构造：Y 是 X 向右平移 1 位
# 含义：看到前面的字符，预测「下一个」字符
x = chunk[:-1]  # 长度 T
y = chunk[1:]   # 长度 T
print("\n位置 | 输入X(看到的) | 标签Y(要预测的下一个)")
print("-" * 50)
for t in range(T):
    print(f"{t:4d} | {itos[int(x[t])]!r:14s} | {itos[int(y[t])]!r}")

print("""
数学含义（自回归 / next-token prediction）:
  给定前文 x_0, x_1, ..., x_{t-1}，模型要估计 P(x_t | x_<t)
  整段序列的联合概率可分解为:
    P(x_0,x_1,...,x_T) = Π_t P(x_t | x_<t)
""")

# ---------------------------------------------------------------------------
# 3) 随机猜测的理论 loss：完全不懂语言时，loss 应该是多少？
# ---------------------------------------------------------------------------
# 若均匀猜 65 个字符中的任意一个：
#   P(correct) = 1/65
#   CrossEntropy = -log(1/65) = log(65)
random_ce = float(np.log(vocab_size))
print("=" * 60)
print("【3. 随机基线】完全瞎猜时的 Cross-Entropy")
print(f"-log(1/{vocab_size}) = log({vocab_size}) = {random_ce:.4f}")
print("对照你训练日志: step 0 的 train/val loss ≈ 4.19，几乎就是这个数！")
print("→ 说明训练刚开始时，模型几乎等于「随机猜下一个字符」。")

# ---------------------------------------------------------------------------
# 4) logits 从哪来 + 用 PyTorch 亲手算一次 Cross-Entropy
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("【4. logits 怎么来】不是 Softmax 算的，是 lm_head 线性层算的")
print("""
真实前向（model.py）:
  字符 → Embedding → [Attn+MLP]×n → 隐向量 x（如 128 维）
  → lm_head: Linear(n_embd → vocab_size, bias=False)
  → logits = x @ W.T     # 形状 (..., 65)
  → Softmax(logits) → 概率

  第 i 个字符的分数: z_i = x · W[i]   （点积，可正可负）
  Softmax 只负责「分数 → 概率」，不负责产生分数本身。
""")

print("【4b. Loss 公式】Cross-Entropy = -log Softmax(logits)[正确类别]")
print("下面用「假造的 logits」演示 CE；真实训练里这些分数来自上面的 lm_head。")

# 假设某个位置的真实标签是字符 'e'（随便举例）
target_char = "e"
target_id = stoi[target_char]

# 造一组「很差」的 logits：所有字符分数差不多
bad_logits = torch.zeros(vocab_size)
# 造一组「很好」的 logits：正确字符分数远高于别人
good_logits = torch.zeros(vocab_size)
good_logits[target_id] = 5.0  # 正确类得分高

for name, logits in [("很差(接近均匀)", bad_logits), ("很好(正确类突出)", good_logits)]:
    # Softmax: 把分数变成概率，和为 1
    probs = F.softmax(logits, dim=-1)
    p_correct = probs[target_id].item()
    # 手动 CE
    manual_loss = -np.log(p_correct)
    # PyTorch 官方 CE（和手动应一致）
    torch_loss = F.cross_entropy(logits.unsqueeze(0), torch.tensor([target_id])).item()
    print(f"\n{name}:")
    print(f"  P('{target_char}') = {p_correct:.6f}")
    print(f"  -log P = {manual_loss:.4f}")
    print(f"  F.cross_entropy = {torch_loss:.4f}")

print("""
记忆口诀:
  logits = lm_head(x) = x @ W.T   ← 原始分数从这里来
  Softmax(logits)                 ← 只把分数收成概率
  loss 小  → 模型给正确答案的概率大 → 学得越好
  loss 大  → 模型几乎没把概率分给正确答案
  训练目标 = 最小化平均 Cross-Entropy（最大似然）
""")

# ---------------------------------------------------------------------------
# 5) 一个 mini-batch 里有多少个预测任务？
# ---------------------------------------------------------------------------
batch_size, block_size = 64, 256
print("=" * 60)
print("【5. 你真实训练时每个 step 在优化什么】")
print(f"batch_size={batch_size}, block_size={block_size}")
print(f"每个 step 的预测次数 = {batch_size} × {block_size} = {batch_size * block_size:,}")
print("每一个 (位置) 都贡献一个 -log P(正确下一字符)，再取平均 → 就是那一步的 loss")
print("=" * 60)
print("第1课结束。回复「继续第2课」→ Embedding + Transformer 前向传播")
