# Dexterous manipulation × on-policy diffusion 导读

这份导读面向学过 RL、希望把 diffusion 用到灵巧手上的读者。重点是已有研究怎样处理动作学习、接触控制与示范数据，以及这些方法能支持什么实验；REGRIND 的具体尝试另见 [对接思路](docs/regrind-integration.md)。

## 背景

灵巧操作涵盖抓取、在手中转动物体、协调手臂与手指，以及连续完成多个操作阶段。比较这些任务时应同时列出初始接触、可用观测和动作接口，手的自由度或算法名称仅作为辅助信息；任务实例与文献见 [01 问题结构](docs/01-problem-structure.md)。

Diffusion 在机器人学习中的用途，可以按“从哪里学习动作、怎样继续改进”来区分：

- **从示范学习动作**：给定相机观测，让模型学习示范中可能出现的动作序列，以条件动作分布替代逐情况手写控制规则（条件动作生成；[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023)）。
- **从已有数据学习高回报动作**：既学习数据里的动作，又利用价值估计偏向更有希望获得回报的动作，在静态数据集上完成训练（offline RL；[Diffusion-QL](docs/bibliography.md#diffusion-ql-2022)、[IDQL](docs/bibliography.md#idql-2023)）。
- **通过交互改进预训练策略**：把生成动作的去噪过程拆成可更新的步骤，用新交互得到的奖励继续训练，在扩展 state 上逐步计算 denoising likelihood（denoising-step PPO；[DPPO](docs/bibliography.md#dppo-2024)）。
- **用可逆生成过程计算概率**：在生成过程满足可逆、密度可计算等条件时，反推出某个采样变量是怎样生成的，从而计算 PPO 更新所需的概率比；该采样变量与机器人执行命令分别定义并记录（exact-inversion；[概率基础附录](docs/appendix-probability.md#概率对象)）。

这些用途可以组合，按现有数据和计算条件选择。方法之间的区别与历史展开见 [diffusion 历史](docs/06-diffusion-history.md)。

读这些路线前，先分清三个时间尺度。denoising step 仅描述模型内部生成动作的迭代；action prediction horizon `T_p` 是一次生成的动作段长度，action execution horizon `T_a` 是其中实际执行的前缀长度。Action chunk 指这一段动作，receding horizon 指执行前缀后取得新观测、再生成下一段：

```text
最近观测 → 生成 T_p 步动作（一个 action chunk）→ 执行前 T_a 步 → 新观测 → 重新生成
```

DPPO 的 PPO ratio 作用于每个 Gaussian 去噪转移，用同一转移的新旧策略 log-prob 之比形成更新。数学展开见 [diffusion 历史](docs/06-diffusion-history.md)。

## 关键术语

术语在首次出现时定义，后文沿用同一含义。

- **Gaussian PPO baseline**：以高斯（对角协方差）为 actor、用 PPO 更新的对照基线，所有增强方案都与它比，用于分离 actor 表示与训练实现的影响。
- **auxiliary action ξ**：生成式 actor 采样出的原始随机变量（去噪链末端或中间量），PPO ratio 作用在它上面，与最终下发给机器人的执行动作分别记录。
- **conditioning**：策略实际读入的条件，含观测、reference/phase、history 或 recurrent state，以及当时的 normalization 约定；冻结它才能比较新旧策略。
- **residual / residual scale**：base controller 输出之上由 RL 学习的修正量，residual scale 是其幅度系数；组合 `u = base + α·ξ` 中 α 即 scale。
- **tracking reference**：作为 policy 时变跟踪目标的 retargeted motion，与作为动作标签的 BC 数据是两种用途。
- **privileged state**：训练时仿真可得、部署时需要由感知估计的物体状态；actor 使用该状态时应配套 state estimator。

## 起步路线

这四类问题分别对应四组研究方法与实验切入点，每节先说明相关研究如何使用该类方法，再给出可执行的实验建议。

```text
动作表示：同一观测下有多种可行动作 -> 路线 1：比较 Gaussian 与生成式 actor
策略更新：生成动作后如何利用奖励改进 -> 路线 2：denoising-step PPO
接触执行：参考轨迹执行时产生接触误差 -> 路线 3：base controller + residual
数据来源：以人类运动作为示范来源 -> 路线 4：运动映射、数据扩增与模仿学习
```

### 路线 1 · 在灵巧手上评估 on-policy diffusion

灵巧手策略需要根据观测选择手指动作，并在执行后利用新观测继续调整。同一个操作目标可能允许不同的手指协调方式，因此动作学习需要覆盖多种可行轨迹。

动作表示的问题是怎样在同一条件下保留这些不同选择。Gaussian actor 用高斯分布描述动作，diffusion 则通过逐步去噪生成动作序列；在灵巧手实验中，需要比较的是这些表示对闭环成功率和接触恢复的影响。

[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023) 从示范学习多模态动作分布，将视觉观测作为条件，并结合 receding horizon control：每次预测一段动作，执行其中若干步，再根据新观测重新预测。这为生成式 actor 提供了示范学习中的实现参照；接入 on-policy RL 时，还需定义新旧策略比较的采样变量，具体见 [概率基础附录](docs/appendix-probability.md#概率对象)。

策略表示的比较还需要控制训练实现的差异。[Implementation Matters](docs/bibliography.md#implementation-matters-2020) 研究 PPO/TRPO 的实现优化对回报的影响。对应到灵巧手实验，可先建立可复现的 Gaussian PPO baseline，再保持奖励、观测、动作含义和测试初始状态一致，比较生成式 actor 的成功率、掉落率、交互量、训练时间与推理延迟；若更新方法也改变，应把它作为组合方案评估。

比较前先验证采样记录支持概率重算，并确认推理速度满足控制周期；两项检查通过后再开始训练。

### 路线 2 · 用去噪转移计算 PPO ratio

从示范训练的 diffusion policy 可以作为交互学习的起点。示范提供动作样本，环境奖励则提供任务完成情况的反馈，研究目标是利用这种反馈继续改善策略的成功率与失败恢复。

PPO 更新需要比较新旧策略生成同一个样本的概率。Diffusion 的最终动作由多步去噪组合而成，逐步 Gaussian 转移因而成为可直接求值的概率对象。已有成功 demonstrations 和可交互环境后，即可按这一对象组织 PPO 更新。

[DPPO](docs/bibliography.md#dppo-2024) v3 §4–5 把每一步去噪看作一次决策，对该步生成的动作计算 Gaussian likelihood，再用环境奖励更新策略。这把概率求值转到去噪过程中的每一步，训练记录也需要保存这些步骤的状态与动作，详见 [概率基础附录的 Rollout 记录](docs/appendix-probability.md#rollout-记录)。

[MoDex](docs/bibliography.md#modex-2026) 将这一方法用于顺序多物体抓取：先通过 behavior cloning 预训练 diffusion policy，再在仿真中进行 DPPO fine-tuning，最后报告 Allegro 真机上的 zero-shot 部署。它提供了从示范学习、仿真交互改进到真机执行的具体案例。

在灵巧手任务中，可以沿用这一训练顺序，比较 fine-tuning 前后的成功率、恢复行为、交互量与新增计算开销。实施前需统一示范数据与环境的观测、动作定义，并确认逐步 likelihood 能够重算；完成这两项检查后再评估更新效果。

### 路线 3 · 在 retargeting 与 base controller 上学习 residual

Retargeting 为机器人提供参考运动，已有 controller 则负责把控制目标转换为执行动作。在这种设置下，策略学习可以复用现有控制，把学习集中在修正量上。

需要处理的是参考运动与实际接触之间的偏差。几何上贴合的轨迹在执行时仍可能出现滑动、跟踪误差或动作饱和，因此应区分参考轨迹的可执行性与控制器需要补偿的误差。

[Residual RL](docs/bibliography.md#residual-rl-2018) 将传统 controller 的输出与 RL 学习的修正量相加，用已有控制处理可建模的部分，把接触、摩擦等误差交给学习策略，并在真机 block assembly 中进行验证。运动跟踪提供另一种学习信号：[DeepMimic](docs/bibliography.md#deepmimic-2018) 将 motion-imitation objective 与 task objective 结合，让 physics-based policy 同时学习参考动作与任务行为。

将这些思路用于 retargeting 时，可先比较 base-only 与 Gaussian residual，再研究生成式 residual 如何影响接触稳定性。比较应使用相同的 reference、controller、residual scale 与执行限制，并记录任务成功率、跟踪误差、修正幅度与饱和率。

这种比较以 reference 可执行、base controller 能独立闭环为前提。训练前先验证这两项条件，再固定轨迹与控制配置；训练 residual 时保留 policy 的原始采样动作，以支持后续概率计算。

### 路线 4 · 从人类运动数据学习策略

人类操作记录可以为灵巧手学习提供动作示例，数据来源包括视频、mocap 和可穿戴采集设备。这类记录可以用于建立机器人动作监督，也可以提供 tracking reference 或训练时的初始状态。

主要问题是把人手运动转换成机器人能够执行的数据。人手与机器人手的运动学不同，记录还需要对齐观测与动作；用作动作监督时，应先确认转换后的动作能完成所需接触，再训练 imitation policy。

[DexUMI](docs/bibliography.md#dexumi-2025) 用可穿戴外骨骼缩小运动学差距，并将视觉特征与触觉读数输入 diffusion policy，预测多步机器人动作。[DexWild](docs/bibliography.md#dexwild-2025) 则联合人手与机器人数据训练 diffusion-based policy，研究策略对新环境的泛化。这些工作把数据采集、形态映射和动作学习组合起来，其中 diffusion 负责学习动作分布。

已有示范还可以通过轨迹合成扩大训练数据覆盖。[DexMimicGen](docs/bibliography.md#dexmimicgen-2024) 从少量示范在仿真中自动合成轨迹，并提供 real-to-sim-to-real pipeline。这是一条数据扩增方法，可以与下游策略学习分别评估。

Diffusion 也可把生成目标限定为抓取候选。[DexDiffuser](docs/bibliography.md#dexdiffuser-2023) 从物体的 partial point cloud 生成 grasp，再通过评分与 refinement 改进候选，并评估仿真与真机抓取成功率。

在这些方法之间选择，首先取决于现有记录能提供什么学习信号。可先判断数据适合作为动作监督、tracking reference 还是 reset，再分别测量数据覆盖、候选动作可行率与下游闭环成功率；数据转换阶段先验证观测与动作同步、候选动作完成所需接触，再进入策略训练。

## 使用与证据约定

真机灵巧手 diffusion 部署可按跨形态学习、人类示范模仿和技能组合分类，逐篇综述见 [06 已发表的真机灵巧手部署](docs/06-diffusion-history.md#已发表的真机灵巧手部署)。

其中与 on-policy 最接近的案例是 [MoDex](docs/bibliography.md#modex-2026)：先在仿真中使用 DPPO fine-tuning，再在 Allegro 真机上对 OOD 物体 zero-shot 部署。其任务范围是顺序多物体抓取，后续实验可进一步评估 in-hand 重定向和真机在线训练。各篇论文的具体实验设置与证据范围见 [注释书目](docs/bibliography.md#证据约定)。

## 文件导航

按当前问题选读：先用 01 明确任务，再从 02 选择方法；已有方向时可直接读对应专题。

- [01 问题结构](docs/01-problem-structure.md)：确定灵巧手任务、观测与硬件条件，或比较不同论文实验设置时读。
- [02 方法选择](docs/02-method-landscape.md)：资源已明确，需要在 imitation、RL 与组合方案之间做选择时读。
- [03 Retargeting 到 policy](docs/03-retargeting-to-policy.md)：已有运动轨迹，需要判断怎样用于训练、怎样检查接触可行性时读。
- [04 On-policy diffusion 执行与任务接口](docs/04-onpolicy-diffusion-interface.md)：准备实现路线 1、2，或核对 residual 的执行 mapping 与任务配置时读。
- [概率基础附录](docs/appendix-probability.md)：需要实现 likelihood、entropy/KL 或 exact-inversion 时读。
- [05 PPO 增强](docs/05-ppo-enhancement.md)：已有训练结果，需要定位失败原因或设计隔离实验时读。
- [06 Diffusion 历史](docs/06-diffusion-history.md)：需要进一步区分 imitation、offline RL 与 on-policy 方法时读。
- [REGRIND 对接思路](docs/regrind-integration.md)：需要把生成式策略用于 REGRIND 的 reference、residual 或部署扰动试验时读。
- [仓库检查与维护](scripts/README.md)：需要运行结构、链接与来源检查时读。
- [注释书目](docs/bibliography.md)：需要查某篇论文解决的问题、所做实验与原文来源时读。

## 快速答案与参考论文

如果只能先选一条路线：有成功 demonstrations 时，先用 Diffusion Policy 做 BC 预训练，再用 DPPO 在仿真中 fine-tune；没有 demonstrations 时，先建立 Gaussian PPO baseline，确认任务、奖励和观测是否可学，再决定是否引入 diffusion actor。

按现有资源可以这样选择：

- **已有可交互仿真**：先跑 Gaussian PPO，再考虑替换 actor。[PPO](docs/bibliography.md#ppo-2017) 提供 ratio 与更新基线，[Implementation Matters](docs/bibliography.md#implementation-matters-2020) 说明为什么要先固定实现细节，[DPPO](docs/bibliography.md#dppo-2024) 则提供 diffusion actor 的 on-policy 更新方式。
- **已有成功 demonstrations**：先验证 imitation 闭环，再考虑 DPPO fine-tuning。[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023) 提供条件动作生成，[DPPO](docs/bibliography.md#dppo-2024) 提供 denoising-step PPO，[MoDex](docs/bibliography.md#modex-2026) 展示 BC 预训练、仿真 DPPO fine-tune 和 Allegro 真机 zero-shot 部署的完整链条；其任务是顺序抓取，in-hand 重定向可作为后续实验。
- **已有 retargeting 或 base controller**：优先评估 residual。[Residual RL](docs/bibliography.md#residual-rl-2018) 提供 base 与 RL 修正量的控制分工，[DeepMimic](docs/bibliography.md#deepmimic-2018) 提供 tracking、phase 与 RSI 参照，[DemoStart](docs/bibliography.md#demostart-2024) 提供 demonstration-led curriculum 与 reset 思路。
- **希望采用 exact-inversion**：先验证 sampler 的可逆性、Jacobian 和数值稳定性，再与 DPPO 比较。[概率基础附录](docs/appendix-probability.md) 给出密度与 rollout 约定，[06 的 exact-inversion 教程](docs/06-diffusion-history.md#与-exact-inversion-的对照) 给出从 toy model 到简单任务的实现路线。

更完整的方法脉络与部署证据见 [06](docs/06-diffusion-history.md)。
