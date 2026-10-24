# Dexterous manipulation × on-policy diffusion 导读

这份导读面向学过 RL、希望把 diffusion 用到灵巧手上的读者。重点是已有研究怎样处理动作学习、接触控制与示范数据，以及这些方法能支持什么实验；REGRIND 的具体尝试另见 [对接思路](docs/regrind-integration.md)。

## 背景

灵巧操作不只是把物体抓起来，还包括在手中转动物体、协调手臂与手指、连续完成多个操作阶段。这些任务的初始接触、可用观测和动作接口不同，不能只按手的自由度或算法名称比较；任务实例与文献见 [01 问题结构](docs/01-problem-structure.md)。

Diffusion 在机器人学习中的用途，可以按“从哪里学习动作、怎样继续改进”来区分：

- **从示范学习动作**：给定相机观测，让模型学习示范中可能出现的动作序列，而不是为每种情况手写控制规则（条件动作生成；[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023)）。
- **从已有数据学习高回报动作**：既学习数据里的动作，又利用价值估计偏向更有希望获得回报的动作，不依赖持续采集新交互（offline RL；[Diffusion-QL](docs/bibliography.md#diffusion-ql-2022)、[IDQL](docs/bibliography.md#idql-2023)）。
- **通过交互改进预训练策略**：把生成动作的去噪过程拆成可更新的步骤，用新交互得到的奖励继续训练，不必直接算出最终动作的概率密度（denoising-step PPO；[DPPO](docs/bibliography.md#dppo-2024)）。
- **用可逆生成过程计算概率**：在生成过程满足可逆、密度可计算等条件时，反推出某个采样变量是怎样生成的，从而计算 PPO 更新所需的概率比；该变量不一定就是机器人执行的命令（exact-inversion；[04 概率对象](docs/04-onpolicy-diffusion-interface.md#概率对象)）。

这些用途可以组合，不是必须依次采用的阶段。方法之间的区别与历史展开见 [diffusion 历史](docs/diffusion-history/README.md)。

读这些路线前，先分清三个时间尺度。denoising step 是模型内部生成动作的迭代，不是机器人控制步；action prediction horizon `T_p` 是一次生成的动作段长度，action execution horizon `T_a` 是其中实际执行的前缀长度。Action chunk 指这一段动作，receding horizon 指执行前缀后取得新观测、再生成下一段：

```text
最近观测 → 生成 T_p 步动作（一个 action chunk）→ 执行前 T_a 步 → 新观测 → 重新生成
```

DPPO 的 PPO ratio 也不是在整段动作上求一个边缘密度，而是在每个 Gaussian 去噪转移上比较新旧策略。下面的数学展开见 [diffusion 历史](docs/diffusion-history/README.md)。

## 关键术语

首次使用后不再重复定义。

- **Gaussian PPO baseline**：以高斯（对角协方差）为 actor、用 PPO 更新的对照基线，所有增强方案都与它比，不把实现细节差异误算成 policy class 收益。
- **auxiliary action ξ**：生成式 actor 采样出的原始随机变量（去噪链末端或中间量），PPO ratio 作用在它上面，不等于最终下发给机器人的执行动作。
- **conditioning**：策略实际读入的条件，含观测、reference/phase、history 或 recurrent state，以及当时的 normalization 约定；冻结它才能比较新旧策略。
- **residual / residual scale**：base controller 输出之上由 RL 学习的修正量，residual scale 是其幅度系数；组合 `u = base + α·ξ` 中 α 即 scale。
- **tracking reference**：作为 policy 时变跟踪目标的 retargeted motion，与作为动作标签的 BC 数据是两种用途。
- **privileged state**：训练时仿真可得、部署时真实机器人拿不到的物体状态；actor 用了它就必须另补估计器。

## 起步路线

灵巧操作研究既要解决动作怎样表示和改进，也要处理接触执行与训练数据。下面从这四类问题出发，介绍已有工作的应用场景、解决方法，以及可以继续研究的方向。

```text
动作表示：同一观测下有多种可行动作 -> 路线 1：比较 Gaussian 与生成式 actor
策略更新：生成动作后如何利用奖励改进 -> 路线 2：denoising-step PPO
接触执行：参考轨迹不能消除执行误差 -> 路线 3：base controller + residual
数据来源：缺少机器人示范、只有人类运动 -> 路线 4：运动映射、数据扩增与模仿学习
```

### 路线 1 · on-policy diffusion 能直接在灵巧手上跑吗

灵巧手策略需要根据观测选择手指动作，并在执行后利用新观测继续调整。同一个操作目标可能允许不同的手指协调方式，因此动作学习需要考虑多种可行选择，而不只拟合一条轨迹。

动作表示的问题是怎样在同一条件下保留这些不同选择。Gaussian actor 用高斯分布描述动作，diffusion 则通过逐步去噪生成动作序列；在灵巧手实验中，需要比较的是这些表示对闭环成功率和接触恢复的影响。

[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023) 从示范学习多模态动作分布，将视觉观测作为条件，并结合 receding horizon control：每次预测一段动作，执行其中若干步，再根据新观测重新预测。这为生成式 actor 提供了示范学习中的实现参照；接入 on-policy RL 时，还需定义新旧策略比较的采样变量，具体见 [04 概率对象](docs/04-onpolicy-diffusion-interface.md#概率对象)。

策略表示的比较还需要控制训练实现的差异。[Implementation Matters](docs/bibliography.md#implementation-matters-2020) 研究 PPO/TRPO 的实现优化对回报的影响。对应到灵巧手实验，可先建立可复现的 Gaussian PPO baseline，再保持奖励、观测、动作含义和测试初始状态一致，比较生成式 actor 的成功率、掉落率、交互量、训练时间与推理延迟；若更新方法也改变，应把它作为组合方案评估。

比较前应先确认采样记录能够支持概率重算，推理速度能够满足控制周期。若同一采样变量的旧 log-prob 无法重算一致，或推理延迟超过预算，应先修复记录与执行问题，再继续训练。

### 路线 2 · 没有精确 log-likelihood 怎么办

从示范训练的 diffusion policy 可以作为交互学习的起点。示范提供动作样本，环境奖励则提供任务完成情况的反馈，研究目标是利用这种反馈继续改善策略的成功率与失败恢复。

PPO 更新需要比较新旧策略生成同一个样本的概率，而 diffusion 的最终动作经过多步去噪得到，直接计算其概率密度较困难。已有成功 demonstrations 和可交互环境之后，还需要找到能计算概率、并能据此更新策略的方法。

[DPPO](docs/bibliography.md#dppo-2024) v3 §4–5 把每一步去噪看作一次决策，对该步生成的动作计算 Gaussian likelihood，再用环境奖励更新策略。这把概率求值转到去噪过程中的每一步，训练记录也需要保存这些步骤的状态与动作，详见 [04 Rollout 记录](docs/04-onpolicy-diffusion-interface.md#rollout-记录)。

[MoDex](docs/bibliography.md#modex-2026) 将这一方法用于顺序多物体抓取：先通过 behavior cloning 预训练 diffusion policy，再在仿真中进行 DPPO fine-tuning，最后报告 Allegro 真机上的 zero-shot 部署。它提供了从示范学习、仿真交互改进到真机执行的具体案例。

在灵巧手任务中，可以沿用这一训练顺序，比较 fine-tuning 前后的成功率、恢复行为、交互量与新增计算开销。实施前需统一示范数据与环境的观测、动作定义，并确认逐步 likelihood 能够重算；发现定义不一致或记录缺失时，应先修复数据与记录，再评估更新效果。

### 路线 3 · 已经有 retargeting 或 base controller 了呢

Retargeting 为机器人提供参考运动，已有 controller 则负责把控制目标转换为执行动作。在这种设置下，策略学习可以利用现有控制，而不必从零学习整个动作过程。

需要处理的是参考运动与实际接触之间的偏差。几何上贴合的轨迹在执行时仍可能出现滑动、跟踪误差或动作饱和，因此应区分参考轨迹的可执行性与控制器需要补偿的误差。

[Residual RL](docs/bibliography.md#residual-rl-2018) 将传统 controller 的输出与 RL 学习的修正量相加，用已有控制处理可建模的部分，把接触、摩擦等误差交给学习策略，并在真机 block assembly 中进行验证。运动跟踪提供另一种学习信号：[DeepMimic](docs/bibliography.md#deepmimic-2018) 将 motion-imitation objective 与 task objective 结合，让 physics-based policy 同时学习参考动作与任务行为。

将这些思路用于 retargeting 时，可先比较 base-only 与 Gaussian residual，再研究生成式 residual 如何影响接触稳定性。比较应使用相同的 reference、controller、residual scale 与执行限制，并记录任务成功率、跟踪误差、修正幅度与饱和率。

这种比较需要先确认 reference 可执行、base controller 能独立闭环。若 base-only 已失稳或参考轨迹无法完成所需接触，应先检查轨迹与控制配置；训练 residual 时则保留 policy 的原始采样动作，以支持后续概率计算。

### 路线 4 · 没有现成策略、只有人类运动数据呢

人类操作记录可以为灵巧手学习提供动作示例，数据来源包括视频、mocap 和可穿戴采集设备。这类记录可以用于建立机器人动作监督，也可以提供 tracking reference 或训练时的初始状态。

主要问题是把人手运动转换成机器人能够执行的数据。人手与机器人手的运动学不同，记录还需要对齐观测与动作；用作动作监督时，应先确认转换后的动作能完成所需接触，再训练 imitation policy。

[DexUMI](docs/bibliography.md#dexumi-2025) 用可穿戴外骨骼缩小运动学差距，并将视觉特征与触觉读数输入 diffusion policy，预测多步机器人动作。[DexWild](docs/bibliography.md#dexwild-2025) 则联合人手与机器人数据训练 diffusion-based policy，研究策略对新环境的泛化。这些工作把数据采集、形态映射和动作学习组合起来，其中 diffusion 负责学习动作分布。

已有示范还可以通过轨迹合成扩大训练数据覆盖。[DexMimicGen](docs/bibliography.md#dexmimicgen-2024) 从少量示范在仿真中自动合成轨迹，并提供 real-to-sim-to-real pipeline。这是一条数据扩增方法，可以与下游策略学习分别评估。

Diffusion 也可用于生成抓取候选，而不必直接生成连续控制动作。[DexDiffuser](docs/bibliography.md#dexdiffuser-2023) 从物体的 partial point cloud 生成 grasp，再通过评分与 refinement 改进候选，并评估仿真与真机抓取成功率。

在这些方法之间选择，首先取决于现有记录能提供什么学习信号。可先判断数据适合作为动作监督、tracking reference 还是 reset，再分别测量数据覆盖、候选动作可行率与下游闭环成功率；若观测与动作无法同步，或候选动作不能完成所需接触，应先修复数据转换与执行问题。

## 使用与证据约定

书目中的真机灵巧手 diffusion 工作覆盖了不同的数据与控制方式：[DexVLA](docs/bibliography.md#dexvla-2025) 研究跨形态动作学习，[DexWild](docs/bibliography.md#dexwild-2025)、[DexUMI](docs/bibliography.md#dexumi-2025)、[DexCast](docs/bibliography.md#dexcast-2026)、[Human2Dex](docs/bibliography.md#human2dex-2026) 利用人类示范训练策略，[SkillWeave](docs/bibliography.md#skillweave-2026) 组合多个技能。

[MoDex](docs/bibliography.md#modex-2026) 进一步使用 DPPO fine-tuning，并报告顺序抓取策略在 Allegro 上的 zero-shot 部署，这与在真机上在线训练或完成 in-hand 重定向不是同一结果。

【论文直接验证】指所引论文实际做过的实验；【机制相关】表示方法可作参照；【需新证据】与【推测】标出尚待检验的应用或解释，各篇的具体实验范围见 [注释书目](docs/bibliography.md#证据约定)。

## 文件导航

按当前问题选读：先用 01 明确任务，再从 02 选择方法；已有方向时可直接读对应专题。

- [01 问题结构](docs/01-problem-structure.md)：确定灵巧手任务、观测与硬件条件，或比较不同论文实验设置时读。
- [02 方法选择](docs/02-method-landscape.md)：资源已明确，但还未确定先做 imitation、RL 还是组合方案时读。
- [03 Retargeting 到 policy](docs/03-retargeting-to-policy.md)：已有运动轨迹，需要判断怎样用于训练、怎样检查接触可行性时读。
- [04 On-policy diffusion 接口](docs/04-onpolicy-diffusion-interface.md)：准备实现路线 1、2，或核对 residual 的概率与执行记录时读。
- [05 PPO 增强](docs/05-ppo-enhancement.md)：已有训练结果，需要定位失败原因或设计隔离实验时读。
- [Diffusion 历史](docs/diffusion-history/README.md)：需要进一步区分 imitation、offline RL 与 on-policy 方法时读。
- [REGRIND 对接思路](docs/regrind-integration.md)：需要把生成式策略用于 REGRIND 的 reference、residual 或部署扰动试验时读；文末附仓库维护检查。
- [注释书目](docs/bibliography.md)：需要查某篇论文解决的问题、所做实验与原文来源时读。
