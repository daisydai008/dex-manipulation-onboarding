# 生成式策略接入 on-policy RL 的历史线

本文件展开 README 背景节的第二段,供需要完整历史脉络的读者。它只覆盖"如何把 diffusion/flow 一类生成模型用进需要逐样本 log-likelihood 的 on-policy 更新"这条线,不做整个 diffusion-RL 的综述。所有文献身份、版本与所据证据以 [../bibliography](../bibliography.md) 为准；除 dppo-2024 的指定全文、diffusion-policy-2023 v5 §2.1–2.3 与 §4.3，以及七篇真机灵巧手 diffusion 部署条目外，其余仅到所记录版本的 abstract，越出另标【推测】。

## 起点：条件动作生成

【论文直接验证】[diffusion-policy-2023](../bibliography.md#diffusion-policy-2023) 用条件 denoising diffusion process 表示 multimodal、高维的 visuomotor 动作分布，配合 receding horizon control 与 time-series diffusion transformer。它解决的是 imitation 侧的表达问题——同一状态下存在的多种合理动作能被一个模型覆盖，而不是被高斯均值为唯一模式的假设压平。这一阶段的 diffusion 还不碰 RL 的 ratio，只负责把动作分布建模好。

## 先分清 action chunk、执行窗口与 denoising step

【论文直接验证】Diffusion Policy v5 §2.2–2.3 的学习对象不是单个动作，而是以最近 `T_o` 步观测为条件的整段动作分布。设 `O_t` 是观测历史、`A_t^0` 是示范中的动作段，训练时先给动作段加噪，再让网络预测所加的噪声；用常见 DDPM 记号可写为：

```text
O_t = (o_{t−T_o+1}, …, o_t)
A_t^0 = (a_t, a_{t+1}, …, a_{t+T_p−1})
A_t^k = √(ᾱ_k) A_t^0 + √(1−ᾱ_k) ε,   ε ~ N(0, I)
L = E || ε − ε_θ(A_t^k, k, O_t) ||²
```

推理时则从 `A_t^K ~ N(0,I)` 出发，反复用 `ε_θ` 和 scheduler 去噪，得到 `A_t^0`。这里的 `K` 是模型内部的 denoising step 数，`T_p` 是动作预测长度，二者不是同一时间轴；一次去噪完成才得到一个 action chunk，而不是得到完整 episode。

【论文直接验证】v5 §2.3 将实际执行的动作前缀长度记为 `T_a`：一次预测 `T_p` 步，只执行前 `T_a` 步，随后读取新观测并重新预测。Action chunk 是这次预测的动作段，receding horizon 是“执行前缀—重新观测—再次预测”的控制循环。

## 把 diffusion 带进 RL：offline 价值引导

【论文直接验证】[diffusion-ql-2022](../bibliography.md#diffusion-ql-2022) 把 conditional diffusion loss 与 behavior cloning、action-value maximization 联合，在训练损失中加入 Q 最大化项以改进策略，在 offline RL 里同时限制 out-of-distribution 动作并保留 multimodal 表达。[idql-2023](../bibliography.md#idql-2023) 则从 IQL 隐含的复杂 actor 出发，先采 diffusion behavior policy 的样本，再按 critic 权重做 importance sample 得到目标策略。这两条路线的共同点是：它们用 diffusion 改进动作分布的质量，但更新发生在 offline 数据上，不需要对 on-policy 采样动作求精确 log-likelihood，因此绕开了本文件的核心难题。

## 核心难题：on-policy 需要逐样本 log-likelihood

PPO 一类 on-policy 算法的 ratio 是 `exp(log qθ(a|c) − log qold(a|c))`，要求对同一个已采样动作在新旧两个策略下都能求 log-prob。高斯策略这点很容易，但 diffusion/flow 策略的动作来自一条迭代去噪链，最终动作的边缘密度通常不可解——这正是 diffusion 长期没能进入 on-policy RL 的原因。【条件推导】把这个难题拆成两个可解方向的约定见 [04 概率对象](../04-onpolicy-diffusion-interface.md#概率对象)：要么让变换可逆以用 change-of-variables，要么改在别的随机变量上定义 ratio。下面两条技术路线分别对应这两个方向。

## 路线一：denoising-step PPO（绕开边缘密度）

【论文直接验证】[dppo-2024](../bibliography.md#dppo-2024) 不要求最终 action chunk 的边缘密度，而是把每个 Gaussian denoising transition 当作扩展 MDP 的 policy action，ratio 对象是逐步 denoising likelihood。它通常从 demonstrations 预训练，再在线 fine-tune。这条路的代价是 rollout 要记录整条去噪轨迹的扩展 state/action，而不是只记一个最终动作。它证明了 diffusion 可以进入 on-policy 更新，但没有回答“最终动作的精确密度”。

【论文直接验证】DPPO v3 §4.1–4.2 的具体做法是：在环境决策时刻 `t`，若去噪链为 `A_t^K → … → A_t^0`，就把扩展 state 写成 `(s_t, A_t^{k+1})`，把下一步去噪结果 `A_t^k` 当作扩展 action。由于该转移本身是 Gaussian，新旧策略在同一转移上的 log-prob 都能直接计算，PPO ratio 因而是：

```text
r̄_t^k(θ) = exp( log π̄_θ(A_t^k | s_t, A_t^{k+1})
                 − log π̄_old(A_t^k | s_t, A_t^{k+1}) )
```

这与在最终 `A_t^0` 上求 `π(A_t^0|s_t)` 是不同对象。环境奖励仍在动作执行后给出，critic 只依赖环境状态 `s_t`，advantage 再按 denoising discount 分配到各去噪步；所以 DPPO 并非“不用 log-likelihood”，而是只用每个去噪转移的 Gaussian log-likelihood。

## 路线二：exact-inversion（正面恢复 log-likelihood）

【机制相关】【推测】与绕开相对，另一条技术路线是让生成分布的动作映射本身可逆，从而用 change-of-variables 精确求出执行动作的 log-likelihood。一旦 log-likelihood 可得，entropy 与 KL 也可无偏估计，KL-adaptive 学习率与 entropy regularization 就能进 on-policy 更新。这条路线对采样器的可逆性、Jacobian 可计算性与数值稳定性有明确要求，【条件推导】成立的前提见 [04 概率对象](../04-onpolicy-diffusion-interface.md#概率对象)；它不等于任意 diffusion sampler 自动满足这些条件。

## 两条路线的对照

【机制相关】路线一以"换一个随机变量"回避边缘密度，工程上更通用，但 ratio 作用在去噪链而非最终动作；路线二保留"最终动作"作为概率对象，理论上更直接，但把难度转移到了可逆性与精确求逆上。选哪条不取决于哪个更新潮，而取决于 sampler 是否可逆、能否承受求逆/ Jacobian 的计算，以及 rollout 记录愿意承担多大开销。两条路的隔离评估口径见 [05 更换 actor 与 likelihood 对象](../05-ppo-enhancement.md#更换-actor-与-likelihood-对象)。

## 尚未解决的灵巧手迁移缺口

【需新证据】【推测】上述两条路线的验证主要来自 locomotion、Franka Kitchen、Robomimic、Furniture-Bench 等任务；灵巧手接触丰富、动作维数高、sim-to-real 间隙大，是否继承这些收益尚待验证。这正是本导读的四条起步路线要回答的：先在固定执行 mapping 下做 actor 隔离替换，再按瓶颈选择 denoising-step 或 exact-inversion，最后才谈真机。

【需新证据】【推测】更具体地说，早期 diffusion 证据几乎没有落在真实多指灵巧手上：diffusion-policy-2023、diffusion-ql-2022、idql-2023 的 abstract 真机或仿真评估均不是多指灵巧手；dppo-2024 v3 全文为 locomotion / Franka Kitchen / Robomimic / Furniture-Bench 加 Furniture-Bench 的 zero-shot 真机转移，无灵巧手；dp3-2024 的 abstract 报告仿真与真机任务，但其灵巧手部分不在本仓库记录的 abstract 证据内。

【需新证据】【推测】本导读经全文核实补入七篇真机灵巧手 diffusion 部署：imitation 路线的 [dexvla-2025](../bibliography.md#dexvla-2025)、[dexwild-2025](../bibliography.md#dexwild-2025)、[dexumi-2025](../bibliography.md#dexumi-2025)、[dexcast-2026](../bibliography.md#dexcast-2026)、[human2dex-2026](../bibliography.md#human2dex-2026)、[skillweave-2026](../bibliography.md#skillweave-2026)，以及最接近本主线的 [modex-2026](../bibliography.md#modex-2026)——它用 DPPO 对 diffusion policy 做仿真 fine-tune，并报告 Allegro 真机的 zero-shot 部署。

【需新证据】【推测】但 MoDex 的任务是顺序多物体抓取，不是接触丰富的 in-hand 重定向。对做 on-policy diffusion 的读者，真正的空缺据此收窄为：把生成式 on-policy 更新用到接触丰富的 in-hand 灵巧操作真机上，这条组合仍无人占住。要落地最新部署时应另行检索并验证其手部形态与策略类型。
