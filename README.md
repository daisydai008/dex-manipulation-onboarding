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

## 关键术语

首次使用后不再重复定义。

- **Gaussian PPO baseline**：以高斯（对角协方差）为 actor、用 PPO 更新的对照基线，所有增强方案都与它比，不把实现细节差异误算成 policy class 收益。
- **auxiliary action ξ**：生成式 actor 采样出的原始随机变量（去噪链末端或中间量），PPO ratio 作用在它上面，不等于最终下发给机器人的执行动作。
- **conditioning**：策略实际读入的条件，含观测、reference/phase、history 或 recurrent state，以及当时的 normalization 约定；冻结它才能比较新旧策略。
- **residual / residual scale**：base controller 输出之上由 RL 学习的修正量，residual scale 是其幅度系数；组合 `u = base + α·ξ` 中 α 即 scale。
- **tracking reference**：作为 policy 时变跟踪目标的 retargeted motion，与作为动作标签的 BC 数据是两种用途。
- **privileged state**：训练时仿真可得、部署时真实机器人拿不到的物体状态；actor 用了它就必须另补估计器。

## 起步路线

灵巧操作中的 RL 实验要分别处理动作表示、策略更新、接触执行和数据来源。下面按这四类问题介绍已有方法，再给出可尝试的实验。

```text
动作表示：同一观测下有多种可行动作 -> 路线 1：比较 Gaussian 与生成式 actor
策略更新：生成动作后如何利用奖励改进 -> 路线 2：denoising-step PPO
接触执行：参考轨迹不能消除执行误差 -> 路线 3：base controller + residual
数据来源：缺少机器人示范、只有人类运动 -> 路线 4：运动映射、数据扩增与模仿学习
```

### 路线 1 · on-policy diffusion 能直接在灵巧手上跑吗

生成式 actor 用来表达同一观测下多种合理的动作选择。Diffusion Policy 在示范学习中使用这一表示；把它用于 on-policy RL，还需要解决新旧策略怎样比较同一动作的问题，因此不能把 imitation 的结果直接当作 PPO 收益。

【需新证据】适合先研究的问题是：任务、数据与训练预算一致时，更换动作表示能否改善灵巧手的闭环成功率。概率计算与执行命令的区分见 [04](docs/04-onpolicy-diffusion-interface.md#概率对象)。

- 前置：可复现的仿真任务、成功判据与 Gaussian PPO baseline，以及候选 actor 的概率计算方法。
- 第一步：保持奖励、观测、动作含义和测试初始状态一致，更换 actor，并配套实现所需的采样记录与更新；若更新方法也改变，结果归因于组合而非 actor 单项。
- 预期产出：成功率、掉落率、交互量、训练时间与推理延迟的对照结果。
- 停止条件：同一采样变量的旧 log-prob 无法重算一致，或推理延迟超过控制周期预算。
- 支撑：[Diffusion Policy](docs/bibliography.md#diffusion-policy-2023) 提供动作表示参照；[Implementation Matters](docs/bibliography.md#implementation-matters-2020) 说明为何必须控制实现差异。

### 路线 2 · 没有精确 log-likelihood 怎么办

DPPO 把难以直接求解的最终动作概率，改成逐步计算去噪动作的概率，再用环境奖励更新策略。它通常从示范预训练出发；MoDex 将这套 fine-tuning 方法用于顺序多物体抓取，并报告 Allegro 真机的 zero-shot 部署，不是在真机上在线训练。

【需新证据】这条路线适合检验示范策略能否通过交互学习改善失败恢复或任务成功率；已有抓取结果不能代替 in-hand 重定向的实验。

- 前置：可用于预训练的成功 demonstrations、可交互环境，以及能重建去噪过程的记录。
- 第一步：先测预训练策略，再加入 DPPO 更新；按 [04 Rollout 记录](docs/04-onpolicy-diffusion-interface.md#rollout-记录) 保存逐步概率求值所需的信息。
- 预期产出：fine-tuning 前后的成功率、恢复行为与交互量，以及新增训练开销。
- 停止条件：逐步 likelihood 无法重算，或预训练数据与环境的观测、动作定义不一致。
- 支撑：[DPPO](docs/bibliography.md#dppo-2024) v3 §4–5 提供更新方法与实验；[MoDex](docs/bibliography.md#modex-2026) 提供顺序抓取与真机部署参照。

### 路线 3 · 已经有 retargeting 或 base controller 了呢

Residual RL 不要求策略重新学习全部控制，而是在已有 controller 输出上叠加修正量，用来处理接触、摩擦等模型误差。Residual RL 的真机 block assembly 支持这种分工；DeepMimic 则说明运动跟踪目标可以与任务目标组合，但两者都不能直接证明生成式 residual 对灵巧手有效。

【推测】【需新证据】Retargeting 场景可以据此比较 Gaussian residual 与生成式 residual，检验修正动作的表示是否影响接触稳定性，而不是直接把参考轨迹当作成功动作。

- 前置：reference 可执行、base controller 能独立闭环，且 residual scale 与执行限制已明确。
- 第一步：先记录 base-only 和 Gaussian residual，再在相同 reference 与 controller 下比较生成式 residual，保留 policy 原始采样动作。
- 预期产出：任务成功率、跟踪误差、residual 幅度与饱和率，区分控制修正和 reference 本身的问题。
- 停止条件：base-only 已失稳或 reference 不可执行；此时先检查接触与控制配置。
- 支撑：[Residual RL](docs/bibliography.md#residual-rl-2018) 提供控制叠加的实验；[DeepMimic](docs/bibliography.md#deepmimic-2018) 提供运动模仿与任务目标组合的参照。

### 路线 4 · 没有现成策略、只有人类运动数据呢

人类运动可以先转换成机器人学习所需的数据，再训练 diffusion policy。DexUMI 用外骨骼与视觉转换缩小人手和机器人手的差异，DexWild 联合人手与机器人数据训练策略；这里 diffusion 学的是动作，不能把整条数据转换过程都称为 diffusion。

数据扩增与候选生成是另一种用途。DexMimicGen 从少量示范合成仿真轨迹，但不是 diffusion 方法；DexDiffuser 则用 diffusion 生成候选 grasp，其抓取结果不能直接外推为连续的运动生成或闭环操作能力。

- 前置：人类运动或视频记录、机器人形态映射，以及动作执行与接触检查方法。
- 第一步：先判断数据适合作为动作监督、tracking reference 还是 reset，再测试 imitation 闭环；若尝试生成候选动作，先验证其可执行性。
- 预期产出：可用数据覆盖、候选动作可行率与下游策略成功率，分别评估数据处理和策略学习的贡献。
- 停止条件：无法得到同步观测与有效动作，或候选动作不能完成所需接触。
- 支撑：[DexUMI](docs/bibliography.md#dexumi-2025)、[DexWild](docs/bibliography.md#dexwild-2025) 展示人类数据到 diffusion policy；[DexMimicGen](docs/bibliography.md#dexmimicgen-2024)、[DexDiffuser](docs/bibliography.md#dexdiffuser-2023) 分别提供轨迹合成与 grasp 生成参照。

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
