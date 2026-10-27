# 06 生成式策略与 on-policy RL：方法脉络与选择

> 本章回答三个问题：Diffusion Policy 怎样学习动作，DPPO 怎样在去噪转移上计算 PPO ratio，exact-inversion 怎样通过可逆映射直接求最终采样变量的密度。建议先读“DPPO：把 ratio 放在去噪转移上”，再读“与 exact-inversion 的对照”和“推荐方向”；已熟悉 imitation 的读者可略过前几节。

本章梳理生成式策略从动作学习到 PPO 更新的技术脉络，并给出灵巧手场景的实验选择。各篇论文的版本与实验范围见 [注释书目](bibliography.md)。

## Diffusion Policy：从示范学习动作段

[Diffusion Policy](bibliography.md#diffusion-policy-2023) 把策略写成以观测为条件的 denoising diffusion process，将单状态动作回归扩展为整段动作分布学习。训练使用 demonstration 和噪声预测损失，属于 behavior cloning；环境奖励与 PPO 在后续 online fine-tuning 中引入。

设 `O_t` 为最近 `T_o` 步观测，`A_t^0` 为示范中的动作段。前向过程给动作段加噪，网络学习预测所加的噪声：

```text
O_t = (o_{t−T_o+1}, …, o_t)
A_t^0 = (a_t, a_{t+1}, …, a_{t+T_p−1})
A_t^k = √(ᾱ_k) A_t^0 + √(1−ᾱ_k) ε,   ε ~ N(0, I)
L = E || ε − ε_θ(A_t^k, k, O_t) ||²
```

推理时从 `A_t^K ~ N(0,I)` 出发，反复用 `ε_θ` 和 scheduler 计算下一步较少噪声的样本，最终得到动作段 `A_t^0`。`K` 表示模型内部的 denoising 迭代步数，`T_p` 表示动作预测长度，两个指标分别描述生成过程与控制时序。

执行时只取动作段的前 `T_a` 步，然后读取新观测并重新预测。Action chunk 是一次预测的动作段，receding horizon 是“执行前缀—重新观测—再次预测”的控制循环；论文 v5 §2.3 定义了这三个 horizon，§4.3 讨论执行长度带来的动作一致性与响应速度折中。

## Offline RL：用价值函数筛选动作

[Diffusion-QL](bibliography.md#diffusion-ql-2022) 在 conditional diffusion loss 中加入 action-value 最大化项，使策略在接近行为数据的同时偏向高价值动作。[IDQL](bibliography.md#idql-2023) 从 diffusion behavior policy 采样，再按 critic 权重做 importance sampling，得到目标策略。两者都在静态数据集上训练，适合已有数据、暂不进行在线交互的场景；它们与 DPPO 的在线 fine-tuning 解决不同阶段的问题。

## On-policy 更新的概率难题

PPO 需要对同一个已采样变量比较新旧策略的 log-prob，形成 `r_t(θ)=exp(log qθ(a|c)−log qold(a|c))`。Gaussian actor 可以直接计算这个量；diffusion actor 的最终动作段由多步去噪产生，其边缘密度需要通过生成链的分解或变换来求值。因此，把 diffusion 用于 on-policy 更新时，必须明确 ratio 作用在哪个随机变量上。

## DPPO：把 ratio 放在去噪转移上

[DPPO](bibliography.md#dppo-2024) 将概率求值放在每个 Gaussian denoising transition 上，并把该转移当作扩展 MDP 中的一次决策。若去噪链为 `A_t^K → … → A_t^0`，扩展 state 是 `(s_t, A_t^{k+1})`，扩展 action 是 `A_t^k`。新旧策略在同一转移上的 log-prob 都可直接计算：

```text
r̄_t^k(θ) = exp( log π̄_θ(A_t^k | s_t, A_t^{k+1})
                 − log π̄_old(A_t^k | s_t, A_t^{k+1}) )
```

因此，DPPO 使用每个去噪转移的 Gaussian log-likelihood 形成 PPO ratio。环境奖励在动作执行后给出，中间去噪步的奖励记为 0；critic 只依赖环境状态 `s_t`，advantage 再按 denoising discount 分配到各去噪步。论文 v3 §4.1–4.2 给出这一构造，§5 在 locomotion、Robomimic、Furniture-Bench 等任务上评估，并报告 Furniture-Bench 的 zero-shot sim-to-real 结果。

DPPO 的工程代价也来自这一构造。除了 interactive environment、reward、reset 和 termination，还需要保存去噪链、逐步 old log-prob 与对应 conditioning，并承担多次去噪带来的采样和更新开销。相比之下，Gaussian PPO 只需记录动作及其 log-prob，actor 与 rollout schema 都更简单；环境与奖励设计在两种方法中都需要完成，DPPO 的额外工作集中在去噪链记录与计算。

DPPO v3 Appendix D Table A3 的时间指一次 training iteration 的耗时，并非完整训练耗时。以 Robomimic Lift、state input 为例，每轮从 50 个并行环境各采集 4 episodes；Lift 中每个环境的这 4 episodes 合计 1200 timesteps，因此 50 个环境共 60000 timesteps，运行配置为 50 个 CPU threads 和一张 NVIDIA L40；该轮耗时为 Gaussian-MLP 27.7 s、DPPO-MLP 35.6 s、DPPO-UNet 83.6 s。论文将 DPPO-MLP 的平均额外开销归于 diffusion sampling，并将 DPPO-UNet 的进一步开销归于卷积与归一化层。这些数字用于说明 actor 与采样结构如何影响训练成本，其他任务需按同口径实测。

## 与 exact-inversion 的对照

Exact-inversion 也从同一个 PPO 问题出发：rollout 中已经保存了采样变量 `ξ`，现在需要计算 `log qθ(ξ|c)`。它直接对最终采样变量求密度，求值对象与 DPPO 的逐步去噪转移不同。

### 从生成结果找回 latent

设基础变量 `z` 来自已知分布，例如标准高斯，生成过程为 `ξ=Fθ(z;c)`。若 `Fθ` 在支持集上是 C¹ diffeomorphism（正逆映射连续可微、Jacobian 非奇异），且逆映射与 log-determinant 可计算，给定 `ξ` 就能求出 `z=Fθ⁻¹(ξ;c)`。这里的“逆”是从生成结果找回唯一的 latent，与机器人动作的时间顺序和噪声预测网络的反向运行是两个不同概念。

有了 `z` 和映射的局部体积变化，就可以使用 change-of-variables：

```text
z = Fθ⁻¹(ξ;c)
log qθ(ξ|c) = log p₀(z|c) − log |det D_z Fθ(z;c)|
```

`p₀(z|c)` 是基础分布的密度，Jacobian determinant 则修正映射造成的体积变化。用一维例子 `ξ=2z` 来看，映射把样本拉开到两倍尺度，密度相应降低，公式中因此要减去 `log 2`。这就是 log-determinant 在概率计算中的作用。

### 在 PPO 中怎样使用

对 rollout 中保存的同一个 `ξ`，旧策略与新策略分别执行自己的逆变换：`z_old=F_old⁻¹(ξ)`、`z_new=F_new⁻¹(ξ)`，再计算 `log q_old(ξ|c)` 与 `log q_new(ξ|c)`。两者取差得到 log-ratio，再通过 `r=exp(log q_new(ξ|c)−log q_old(ξ|c))` 得到 PPO ratio。两次逆变换得到的 latent 可以不同；必须保持一致的是采样变量 `ξ` 与 conditioning `c`。

这个密度还可以用于估计 entropy 与 KL，但估计方式仍取决于样本来源和数值稳定性。可求值的 log-density 只提供输入，具体估计仍需按 [04 Entropy/KL 与优化控制](04-onpolicy-diffusion-interface.md#entropykl-与优化控制) 检查。

### 实现时需要验证什么

首先检查映射在支持集上是否满足 C¹ diffeomorphism、Jacobian 是否非奇异，以及逆映射和 log-determinant 是否可计算。Stochastic 或 many-to-one 的采样过程需要另行设计可逆结构，确认这些条件后再使用这套公式。实际方法通常通过可逆 ODE/flow 或专门设计的 coupling 结构来构造这种结构，每个分支的逆映射与 Jacobian 都需要单独验证。

随后做数值验证：检查 round-trip `Fθ(Fθ⁻¹(ξ))` 是否回到原样本，比较 autograd 与有限差分得到的 Jacobian，并记录 inverse error、log-prob 和 log-determinant 的数值范围。开始训练前，还应测量逆变换的 wall-clock 与显存开销。

### 一条入门实现路线

1. 用一维或二维 toy model 写出 `z→ξ`，手算 Jacobian 与密度，先确认体积修正的符号。
2. 用线性可逆映射实现 `F⁻¹`，检查 round-trip，再换成非线性可逆映射。
3. 用 autograd 计算 Jacobian，与有限差分对照，记录 inverse error 和 log-prob 稳定性。
4. 在 toy PPO 中保存同一批 `ξ`，比较 old/new ratio 与 clipped loss，检查 log-determinant 是否引起数值异常。
5. 在 Isaac 的简单任务中固定 reward、reset、observation 和 seed，与 Gaussian PPO 比较成功率、KL/clip fraction、wall-clock 和显存，再决定是否进入灵巧手或 residual 场景。

若现有 sampler 已满足可逆与可计算条件，并且需要最终变量的密度、entropy 或 KL，exact-inversion 是自然候选；若希望避开求逆和 Jacobian 计算，DPPO 的逐步 Gaussian likelihood 提供更直接的实现路径。两条路线都应先与相同配置的 Gaussian PPO 对照。

## 已发表的真机灵巧手部署

本导读核实的真机灵巧手 diffusion 工作主要走 imitation 路线。[DexVLA](bibliography.md#dexvla-2025) 用 diffusion action expert 做跨形态动作学习；[DexWild](bibliography.md#dexwild-2025)、[DexUMI](bibliography.md#dexumi-2025)、[DexCast](bibliography.md#dexcast-2026)、[Human2Dex](bibliography.md#human2dex-2026) 利用人类示范训练 diffusion policy；[SkillWeave](bibliography.md#skillweave-2026) 用 object-mask 条件的 diffusion policy 组合长时技能。这些工作以 imitation learning 为主，on-policy 证据主要来自下文的 MoDex。

[MoDex](bibliography.md#modex-2026) 更接近 on-policy 方向：先用 behavior cloning 预训练 diffusion policy，再在仿真中用 DPPO fine-tune，最后报告 Allegro 真机上对 OOD 物体的 zero-shot 部署。其任务聚焦顺序多物体抓取，为接触丰富的 in-hand 重定向提供了明确的后续实验目标。

## 推荐方向

从 Gaussian PPO baseline 开始，先确认在该奖励与观测条件下任务是否可学，并建立成功率、交互量与延迟的参照。出现明确的动作表示瓶颈，或已有可复用的 diffusion policy 时，再评估 DPPO 的额外复杂度是否值得。

已有 demonstrations 和可交互仿真环境时，可以采用“BC 预训练 → DPPO 仿真 fine-tune → 固定初始状态评估”的顺序。评估应固定 reward、reset、observation、action semantics 和 seed，报告成功率、恢复行为、交互量、显存、更新耗时与推理延迟，并与同条件的 Gaussian PPO 对照。选择依据是概率对象与计算预算；sampler 可逆且需要最终动作的精确密度时，可将 exact-inversion 作为候选路线。

对 retargeting 场景，下一步更具体的实验是把 diffusion actor 用在 reference 后的 residual 上，先验证 base-only 与 Gaussian residual，再比较生成式 residual；执行 mapping 和记录要求见 [04 固定执行 mapping](04-onpolicy-diffusion-interface.md#固定执行-mapping)，REGRIND 的接口拆分见 [对接思路](regrind-integration.md)。真机实验与仿真 fine-tune 应分别报告，并单独规划真机在线训练实验。
