"""
第2课：Embedding → Attention → MLP → Logits（前向传播）
运行：
  cd nanoGPT && source .venv/bin/activate
  python lessons/lesson2_forward.py
"""
import math
import os
import pickle
import numpy as np
import torch
import torch.nn.functional as F

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(root, "data", "shakespeare_char")
with open(os.path.join(data_dir, "meta.pkl"), "rb") as f:
    meta = pickle.load(f)
itos, stoi = meta["itos"], meta["stoi"]
vocab_size = meta["vocab_size"]

torch.manual_seed(42)

# 用和你训练接近、但更小的尺寸，方便打印看清张量形状
n_embd = 8          # 真实训练轻量版是 128
n_head = 2          # 真实是 4
head_dim = n_embd // n_head  # 4
T = 5               # 只看 5 个字符，方便人眼跟踪
text = "Hello"
ids = torch.tensor([[stoi[c] for c in text]], dtype=torch.long)  # (1, T)
print("=" * 60)
print("【输入】文本:", repr(text), "→ token ids:", ids.tolist()[0])

# ---------------------------------------------------------------------------
# 1) Token Embedding + Position Embedding
# ---------------------------------------------------------------------------
wte = torch.nn.Embedding(vocab_size, n_embd)
wpe = torch.nn.Embedding(T, n_embd)
pos = torch.arange(T)
tok_emb = wte(ids)          # (B, T, C)
pos_emb = wpe(pos)          # (T, C)
x = tok_emb + pos_emb       # 广播相加
print("\n" + "=" * 60)
print("【1. Embedding】每个字符 → 一个 n_embd 维向量，再加位置信息")
print(f"tok_emb shape = {tuple(tok_emb.shape)}  # (batch, seq, n_embd)")
print(f"pos_emb shape = {tuple(pos_emb.shape)}")
print(f"x = tok_emb + pos_emb, shape = {tuple(x.shape)}")
print("含义: 同一字母 'l' 在不同位置，因 pos_emb 不同，表示也不同")

# ---------------------------------------------------------------------------
# 2) 手工算一遍 Causal Self-Attention（单头先讲清，再扩到多头）
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("【2. Causal Self-Attention】核心公式: Attention(Q,K,V)=softmax(QK^T/√d) V")

# 为了演示，直接从 x 线性映射出 Q/K/V（这里简化成单头）
Wq = torch.randn(n_embd, head_dim) * 0.1
Wk = torch.randn(n_embd, head_dim) * 0.1
Wv = torch.randn(n_embd, head_dim) * 0.1

# 取 batch=0
h = x[0]  # (T, C)
Q = h @ Wq  # (T, head_dim)
K = h @ Wk
V = h @ Wv

# 注意力分数：每个位置对每个位置的「相关程度」
scores = Q @ K.T / math.sqrt(head_dim)  # (T, T)
print(f"QK^T/√d shape = {tuple(scores.shape)}  # 第 i 行 = 位置i对所有位置的打分")

# Causal mask：只能看自己和左边（不能偷看未来）
causal = torch.tril(torch.ones(T, T))
scores_masked = scores.masked_fill(causal == 0, float("-inf"))
attn = F.softmax(scores_masked, dim=-1)
print("\nCausal Attention 权重矩阵（每行和≈1，右上角被mask成0）:")
print(np.round(attn.detach().numpy(), 3))
print("读法: 第3行第1列 = 位置2在预测时，对位置0信息的关注比例")

out = attn @ V  # (T, head_dim)
print(f"\nattn @ V → shape {tuple(out.shape)}  # 每个位置得到「加权汇总后的前文信息」")

# ---------------------------------------------------------------------------
# 3) 残差 + MLP（Block 的另一半）
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("【3. Transformer Block】x = x + Attn(LN(x)); x = x + MLP(LN(x))")
print("""
为什么加残差(+)?
  - 梯度更容易回传（缓解深层网络消失）
  - 每一层只学习「增量修正」，而不是重写全部表示

MLP 在干什么?
  - 把每个位置的向量单独做非线性变换（扩到 4*n_embd 再压回）
  - Attention 负责「位置之间交换信息」，MLP 负责「位置内部加工特征」
""")

# ---------------------------------------------------------------------------
# 4) 接到 lm_head：向量 → 65 个字符的 logits
# ---------------------------------------------------------------------------
lm_head = torch.nn.Linear(n_embd, vocab_size, bias=False)
# 假装经过多层后仍用 x（形状够用即可）
logits = lm_head(x)  # (1, T, vocab_size)
print("=" * 60)
print("【4. lm_head】每个位置输出 vocab_size 维分数 = logits")
print(f"logits shape = {tuple(logits.shape)}  # (batch, seq, 65)")
print("""
logits 怎么算出来的?
  lm_head = Linear(n_embd → vocab_size, bias=False)
  公式:   logits = x @ W.T
  含义:   第 i 个字符的分数 z_i = x 与 W[i] 的点积（可正可负）
  注意:   Softmax 不负责算分数，只把这 65 个分变成概率
""")

# 手工核对：最后一个位置，z = x @ W.T 应等于 lm_head(x)
W = lm_head.weight  # (vocab_size, n_embd)
last_x = x[0, -1]   # (n_embd,)
manual_logits = last_x @ W.T
auto_logits = logits[0, -1]
print(f"手工点积 vs lm_head，最大绝对差 = {(manual_logits - auto_logits).abs().max().item():.2e}")
print(f"（接近 0 就说明：logits 就是一次矩阵乘法）")

# 看最后一个位置，模型对下一字符的「当前随机偏好」
last_logits = auto_logits
probs = F.softmax(last_logits, dim=-1)
topk = torch.topk(probs, 5)
print(f"\n输入 '{text}' 后，下一字符 Top5（未训练，接近乱猜）:")
for p, idx in zip(topk.values.tolist(), topk.indices.tolist()):
    print(f"  {itos[idx]!r:6s}  P={p:.4f}")

print("""
和 model.py 的对应关系:
  wte/wpe 加法     → GPT.forward 里 tok_emb + pos_emb
  QK^T/√d+mask    → CausalSelfAttention.forward
  Block 残差+MLP  → Block.forward
  lm_head + CE    → GPT.forward 里 logits = self.lm_head(x)
""")
print("=" * 60)
print("第2课结束。回复「继续第3课」→ 反向传播 + AdamW 如何改参数")
