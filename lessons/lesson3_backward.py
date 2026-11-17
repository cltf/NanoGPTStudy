"""
第3课：反向传播直觉 + 一次参数更新
运行：
  cd nanoGPT && source .venv/bin/activate
  python lessons/lesson3_backward.py
"""
import torch
import torch.nn.functional as F

torch.manual_seed(0)

# 极简：2 维输入 → 线性层 → 3 类 → CrossEntropy
# 用来看清：loss.backward() 后 weight.grad 长什么样，step 后权重怎么变
linear = torch.nn.Linear(2, 3, bias=False)
x = torch.tensor([[1.0, 0.5]])
y = torch.tensor([0])  # 正确答案是第 0 类

print("=" * 60)
print("【1. 前向】")
logits = linear(x)
loss = F.cross_entropy(logits, y)
print(f"logits = {logits.detach().numpy().round(4)}")
print(f"loss   = {loss.item():.4f}")

print("\n" + "=" * 60)
print("【2. 反向】loss.backward() 填充 .grad")
loss.backward()
print(f"weight shape = {tuple(linear.weight.shape)}")
print(f"weight.grad =\n{linear.weight.grad.numpy().round(4)}")
print("含义: 每个权重的梯度 = loss 对该权重的偏导（该往哪拧）")

print("\n" + "=" * 60)
print("【3. 一次 SGD 更新】w <- w - lr * grad")
lr = 0.5
with torch.no_grad():
    w_before = linear.weight.clone()
    linear.weight -= lr * linear.weight.grad
    w_after = linear.weight.clone()
print(f"lr = {lr}")
print(f"Δw =\n{(w_after - w_before).numpy().round(4)}")

# 清梯度再前向，看 loss 是否下降
linear.zero_grad()
loss2 = F.cross_entropy(linear(x), y)
print(f"\n更新前 loss = {loss.item():.4f}")
print(f"更新后 loss = {loss2.item():.4f}")
print("→ 沿负梯度走一小步，通常 loss 会下降（学习率合适时）")

print("\n" + "=" * 60)
print("【4. 和 nanoGPT 的对应】")
print("  loss.backward()     → 给全部参数填 .grad")
print("  AdamW.step()        → 比上面的 SGD 更稳的更新规则")
print("  optimizer.zero_grad → 清空 .grad，避免下一步累加")
print("  get_lr(it)          → 每步可能换学习率（warmup + cosine）")
print("=" * 60)
print("第3课脚本结束。打开 学习笔记/lesson03.html 对照阅读")
