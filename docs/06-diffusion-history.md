# 06 生成式策略与 on-policy RL：方法脉络与选择

本章回答两个问题：已发表工作怎样把 diffusion 用于动作学习和 PPO 更新，以及在灵巧手场景中下一步怎样选择实验。各篇论文的版本与实验范围见 [注释书目](bibliography.md)。

## Diffusion Policy：从示范学习动作段

[Diffusion Policy](bibliography.md#diffusion-policy-2023) 把策略写成以观测为条件的 denoising diffusion process，学习示范中可能出现的整段动作，而不是为每个状态只回归一个动作。训练使用 demonstration 和噪声预测损失，不使用环境奖励，也不涉及 PPO。

设 `O_t` 为最近 `T_o` 步观测，`A_t^0` 为示范中的动作段。前向过程给动作段加噪，网络学习预测所加的噪声：

```text
O_t = (o_{t−T_o+1}, …, o_t)
A_t^0 = (a_t, a_{t+1}, …, a_{t+T_p−1})
A_t^k = √(ᾱ_k) A_t^0 + √(1−ᾱ_k) ε,   ε ~ N(0, I)
L = E || ε − ε_θ(A_t^k, k, O_t) ||²
```

推理时从 `A_t^K ~ N(0,I)` 出发，反复用 `ε_θ` 和 scheduler 计算下一步较少噪声的样本，最终得到动作段 `A_t^0`。`K` 是模型内部的 denoising step 数，`T_p` 是动作预测长度，二者不是同一时间轴。

执行时只取动作段的前 `T_a` 步，然后读取新观测并重新预测。Action chunk 是一次预测的动作段，receding horizon 是“执行前缀—重新观测—再次预测”的控制循环；论文 v5 §2.3 定义了这三个 horizon，§4.3 讨论执行长度带来的动作一致性与响应速度折中。

## Offline RL：用价值函数筛选动作

[Diffusion-QL](bibliography.md#diffusion-ql-2022) 在 conditional diffusion loss 中加入 action-value 最大化项，使策略在接近行为数据的同时偏向高价值动作。[IDQL](bibliography.md#idql-2023) 从 diffusion behavior policy 采样，再按 critic 权重做 importance sampling，得到目标策略。两者都在静态数据集上训练，不需要在线交互，也不需要对 on-policy 采样动作计算新旧策略 ratio。

## On-policy 更新的概率难题

PPO 需要对同一个已采样变量比较新旧策略的 log-prob，形成 `r_t(θ)=exp(log qθ(a|c)−log qold(a|c))`。Gaussian actor 可以直接计算这个量；diffusion actor 的最终动作段由多步去噪产生，其边缘密度通常难以直接求值。因此，把 diffusion 用于 on-policy 更新时，必须明确 ratio 作用在哪个随机变量上。

## DPPO：把 ratio 放在去噪转移上

[DPPO](bibliography.md#dppo-2024) 不计算最终动作段的边缘密度，而是把每个 Gaussian denoising transition 当作扩展 MDP 中的一次决策。若去噪链为 `A_t^K → … → A_t^0`，扩展 state 是 `(s_t, A_t^{k+1})`，扩展 action 是 `A_t^k`。新旧策略在同一转移上的 log-prob 都可直接计算：

```text
r̄_t^k(θ) = exp( log π̄_θ(A_t^k | s_t, A_t^{k+1})
                 − log π̄_old(A_t^k | s_t, A_t^{k+1}) )
```

因此，DPPO 仍然使用 log-likelihood，只是使用每个去噪转移的 Gaussian log-likelihood。环境奖励在动作执行后给出，中间去噪步没有任务奖励；critic 只依赖环境状态 `s_t`，advantage 再按 denoising discount 分配到各去噪步。论文 v3 §4.1–4.2 给出这一构造，§5 在 locomotion、Robomimic、Furniture-Bench 等任务上评估，并报告 Furniture-Bench 的 zero-shot sim-to-real 结果。

DPPO 的工程代价也来自这一构造。除了 interactive environment、reward、reset 和 termination，还需要保存去噪链、逐步 old log-prob 与对应 conditioning，并承担多次去噪带来的采样和更新开销。相比之下，Gaussian PPO 只需记录动作及其 log-prob，actor 与 rollout schema 都更简单；DPPO 并不会减少环境或奖励设计的工作量。DPPO v3 Appendix D Table A3 的 Lift 单轮训练时间为 Gaussian-MLP 27.7 s、DPPO-MLP 35.6 s、DPPO-UNet 83.6 s；这些数字只说明该配置下的开销，不是全局开销上限。

## 与 exact-inversion 的对照

另一条技术路线是让生成映射可逆，用 change-of-variables 直接计算最终采样变量的密度。这样可以保留最终动作作为概率对象，并进一步估计 entropy 与 KL，但要求 sampler 可逆、逆映射和 Jacobian 可计算，且数值误差可控。两种路线的选择取决于现有 sampler 是否满足这些条件，以及能否承担求逆计算；条件推导见 [04 概率对象](04-onpolicy-diffusion-interface.md#概率对象)。

## 已发表的真机灵巧手部署

本导读核实的真机灵巧手 diffusion 工作主要走 imitation 路线。[DexVLA](bibliography.md#dexvla-2025) 用 diffusion action expert 做跨形态动作学习；[DexWild](bibliography.md#dexwild-2025)、[DexUMI](bibliography.md#dexumi-2025)、[DexCast](bibliography.md#dexcast-2026)、[Human2Dex](bibliography.md#human2dex-2026) 利用人类示范训练 diffusion policy；[SkillWeave](bibliography.md#skillweave-2026) 用 object-mask 条件的 diffusion policy 组合长时技能。这些工作说明 diffusion actor 可以部署到真实多指手上，但不涉及 on-policy ratio。

[MoDex](bibliography.md#modex-2026) 更接近 on-policy 方向：先用 behavior cloning 预训练 diffusion policy，再在仿真中用 DPPO fine-tune，最后报告 Allegro 真机上对 OOD 物体的 zero-shot 部署。其任务是顺序多物体抓取，不是接触丰富的 in-hand 重定向；在本导读核实的文献中，on-policy diffusion 用于这类 in-hand 真机任务仍缺少公开实验证据。

## 推荐方向

没有现成 diffusion policy 或成功 demonstrations 时，先建立 Gaussian PPO baseline。它的 actor、log-prob 和 rollout 都更简单，可以先确认任务、奖励和观测是否可学；只有在相同数据和更新口径下出现明确的动作表示瓶颈，或已经有可复用的 diffusion policy 时，才有理由承担 DPPO 的额外复杂度。

已有 demonstrations 和可交互仿真环境时，可以采用“BC 预训练 → DPPO 仿真 fine-tune → 固定初始状态评估”的顺序。评估应固定 reward、reset、observation、action semantics 和 seed，报告成功率、恢复行为、交互量、显存、更新耗时与推理延迟，并与同条件的 Gaussian PPO 对照。若 sampler 可逆且需要最终动作的精确密度，再把 exact-inversion 作为另一条候选路线，而不是默认它一定优于 DPPO。

对 retargeting 场景，下一步更具体的实验是把 diffusion actor 用在 reference 后的 residual 上，先验证 base-only 与 Gaussian residual，再比较生成式 residual；执行 mapping 和记录要求见 [04 固定执行 mapping](04-onpolicy-diffusion-interface.md#固定执行-mapping)，REGRIND 的接口拆分见 [对接思路](regrind-integration.md)。真机实验应与仿真 fine-tune 分开报告，zero-shot 部署不能写成真机在线训练。
