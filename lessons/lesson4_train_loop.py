"""
第4课：对照 train.py 主循环结构（不真正长训，只打印流程说明）
运行：
  cd nanoGPT && source .venv/bin/activate
  python lessons/lesson4_train_loop.py
"""
print(
    """
============================================================
【train.py 主循环地图】
============================================================

启动一次（循环外）
  · 读 config / 命令行覆盖
  · 建 GPT、搬到 device、AdamW
  · get_batch 取第一个 (X, Y)

while True:
  1) lr = get_lr(iter_num)          # 第3课：学习率调度
  2) if iter % eval_interval == 0:
        estimate_loss()             # no_grad + eval
        记录 step/train/val         # 你加的曲线列表
        可能 torch.save(ckpt.pt)
  3) logits, loss = model(X, Y)     # 第1–2课：前向 + CE
     loss.backward()                # 第3课：反向
     clip_grad_norm_
     optimizer.step()               # AdamW 更新
     optimizer.zero_grad()
     X, Y = get_batch('train')      # 下一批（代码里在 micro step 内预取）
  4) 打印 iter loss；iter_num += 1
  5) if iter_num > max_iters: break

循环后
  · matplotlib 画 loss_curve.png

------------------------------------------------------------
关键词搜索（在 train.py 里）
  get_batch | estimate_loss | get_lr | while True
  loss.backward | optimizer.step | max_iters | loss_curve
------------------------------------------------------------
打开 学习笔记/lesson04.html 看逐步对照表
============================================================
"""
)
