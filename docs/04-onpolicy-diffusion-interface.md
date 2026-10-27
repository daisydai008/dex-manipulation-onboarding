# 04 On-policy diffusion 的概率与执行接口

> 本章讨论 PPO ratio 对应的随机变量、rollout 记录和执行 mapping。阅读后可以根据 sampler 的结构选择 denoising-step likelihood 或满足条件的 exact-inversion，并检查训练与执行约定是否一致。对应 README 的路线 1、2。

On-policy diffusion 首先需要确定更新时求值的概率对象。下面分别讨论满足可逆条件的辅助动作模型和 DPPO 的 denoising transition，再说明各自需要保存的数据。数学推导列出成立条件，论文结果与目标任务中的实验建议分别展开。

## 概率对象

可逆变换的密度公式要求输入、输出同维，并能计算逆映射与 Jacobian。给定固定 conditioning `c`，设基础变量 `z∈R^d` 有相对 Lebesgue measure 的已知密度 `p₀(z|c)`，辅助动作 `ξ=Fθ(z;c)∈R^d`。当 `Fθ` 在支持集内部是 C¹ diffeomorphism（一一可逆、正逆映射连续可微、Jacobian 非奇异，忽略零测集合），且逆映射与 log-determinant 可计算时，change-of-variables 给出下式。选择 sampler 时，需要逐项核对这些条件；stochastic、多对一或改变维度的采样过程需根据自身结构另行推导密度。

```text
z = Fθ⁻¹(ξ;c)
log qθ(ξ|c) = log p₀(z|c) − log |det D_z Fθ(z;c)|
```

这里的 exact density 指模型密度公式可求值，数值实现仍需检查误差。可以验证 inverse round-trip、Jacobian 求值、支持集和浮点精度，确认公式与实现一致。执行动作 `u=g(c,ξ)` 的密度则由另一层变换决定：当 `g` 多对一时，通常需要对原像积分才能得到 `pθ(u|c)`，而 `qθ(ξ|c)` 描述的是辅助动作。

DPPO 直接以 Gaussian denoising transition 为概率对象。[dppo-2024](bibliography.md#dppo-2024) v3 §4.1 Eq. (4.1)–(4.4)、§4.2 Eq. (4.5)–(4.8) 在扩展 state `(s,a^{k+1})` 上，用各步 transition likelihood 构造 PPO 更新，从而将求值对象放在去噪链内部。§4.3 还区分了采样时的 noise 下限 σ^exp_min 与 Gaussian likelihood 求值时的下限 σ^prob_min。复现时需要分别核对两者的用途；最终 action chunk 的边缘密度与可逆变换条件属于各自独立的问题。

Offline action generation 关注利用静态数据和价值信息选择动作。[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 与 [idql-2023](bibliography.md#idql-2023) 分别介绍 value-guided diffusion 和 critic-weighted behavior samples。若进一步采用 on-policy 更新，需要另外定义 PPO ratio 的随机变量与 likelihood，并按对应分布建立 entropy/KL 估计。

## Rollout 记录

PPO ratio 比较的是同一个已采样动作在新旧策略下的密度。对旧策略采到的 `ξ_t~qold(·|c_t)`，保持 `ξ_t` 与 conditioning `c_t` 固定，计算 `r_t(θ)=exp(log qθ(ξ_t|c_t)−log qold(ξ_t|c_t))`。因此，update 应读取 rollout 中的原始样本；clipped executed action 可能对应多个 `ξ`，原始变量需要直接保存。这个定义沿用 [ppo-2017](bibliography.md#ppo-2017) 的新旧策略比较，并明确了本节使用的辅助动作空间。

Rollout 至少应保存原始 `ξ_t`、采样时的 old log-prob 和完整 conditioning。Conditioning 包括 policy 实际输入、reference/phase、history 或 recurrent state 的重建信息，以及当时的 normalization 约定；reward、done/truncation、value 和 advantage 按 estimator 的要求另行记录。随后在旧参数下重算 log-prob，确认它与保存值落在预定义数值容差内；执行 command 可用于核对控制过程，原始样本用于核对概率。

更换概率对象时，rollout schema 需要随之调整。DPPO 的数据应支持 denoising trajectory 和扩展 state/action 的逐步 likelihood，依据 [dppo-2024](bibliography.md#dppo-2024) v3 §4；条件可逆模型则按上面的 `ξ` 约定记录。每种实现都应完成自己的重算检查，再进入策略比较。

## Entropy/KL 与优化控制

Entropy 与 KL 由相应分布下的期望定义，可求值的 log-density 是计算这些期望的基础。对固定 `c`，在支持集条件满足且期望存在时，定义如下。第二式的方向是 `old‖new`，要求 `qold` 对 `qθ` 绝对连续；违反这一支持集条件时，KL 可以为无穷大。

```text
H(qθ|c) = E_{ξ~qθ(·|c)}[−log qθ(ξ|c)]
D_KL(qold || qθ | c) = E_{ξ~qold(·|c)}[log qold(ξ|c) − log qθ(ξ|c)]
```

当前策略的 entropy 应使用当前策略样本进行直接 Monte Carlo 估计。复用旧样本时，需要满足支持集条件并进行相应 importance weighting；直接平均旧 rollout 上的 `−log qθ` 得到的是交叉熵估计。报告时应注明样本来源、样本数与相关性，使估计对象和误差来源明确。

旧 rollout 上的 log-prob difference 可以估计 `old‖new` KL，此时 conditioning 取自旧 rollout 的经验分布。有限样本误差可能使这个经验 KL 为负，解释结果时需结合样本数与相关性。这里的 entropy/KL 都位于辅助动作空间；执行动作的分布、接触探索和任务性能需要各自的测量。

KL-adaptive LR 可以作为优化控制的候选实验。预先定义辅助空间 `old‖new` KL 的目标区间、估计方法、调节幅度和时序：估计偏高时降低后续 update 的 LR，持续偏低时尝试提高，并与固定 LR 做单因素对照。开始对照前先核对 log-prob、advantage 和 normalization，再分别测试 LR、epoch 与 clip，检查顺序见 [05](05-ppo-enhancement.md#从失败信号选择接口)。

## 固定执行 mapping

固定且与待更新 policy 参数无关的执行 mapping 可以并入环境动力学。令 `s` 为包含 controller 状态的完整环境状态，`c=h(s)` 为本次决策的 conditioning；若 `u=g(s,ξ)` 在数据收集与相关更新期间固定，则可定义 `P̃(s'|s,ξ)=P(s'|s,g(s,ξ))`、`R̃(s,ξ)=R(s,g(s,ξ))`。这个构造允许不可逆的 `g`，policy 在辅助动作环境中按 `qθ(ξ|c)` 采样，并对同一个 `ξ` 计算 ratio；PPO 仍使用其原有的近似目标。

固定的 base controller、residual scale 与 clipping 可以组成这样的 mapping。例如 `u=clip(b(s)+αξ)` 中，只要 `b`、`α`、clipping 规则和相关 controller 状态转移独立于待更新参数，并保留原始 `ξ`，就可以在辅助动作空间进行 PPO 更新。此时 `qθ` 仍表示辅助密度，执行动作密度需按 composition 另外确定。[residual-rl-2018](bibliography.md#residual-rl-2018) 提供 control-signal superposition 的工程参照；这里的概率关系来自上述固定 mapping 条件。

带内部状态的 controller 或 filter 需要连同状态转移一起描述。若 `m_t` 影响执行 command，就应定义 `(s_t,m_t)` 的转移与 reset；policy 使用该状态时，还需将其保存到 conditioning 中或提供重建信息。这样才能完整描述当前动作对后续状态的影响。

执行规则改变后，需要重新确认 rollout 的有效性。更新 reference、base controller、normalization、safety filter 或内部状态规则，都可能改变环境或 conditioning；old log-prob 记录解决的是策略概率比较，执行条件还需单独检查。Controller 与 actor 共同学习需要另行建立相应推导。对 REGRIND 的 reference-conditioned residual，可以先按 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟) 验证可执行性，再检查概率记录与数据收集时的约定是否一致。

## 按诊断目的的任务验证

三个任务用于检查不同环节，可以分别开展实验。Shadow Hand 直接评估灵巧手控制，Franka cube lift 检查较简单的 manipulation 接口，Ant 观察优化实现在其他动力学中的行为。各任务的结果按自身指标解释，跨任务迁移与真机表现另外验证。

环境定义统一引用 Isaac Lab v2.2.0 的 `Available Environments — Isaac Lab Documentation` 页面。下列链接固定了官方 hostname、版本 path、page title 和 section fragment，用于核对环境 ID、任务描述及列出的动作接口。具体实验中的 state/action 维度、观测配置和 actor 表现，分别通过配置检查与训练评估确定。

三个任务共用一套比较协议。先建立 Gaussian baseline，再替换 actor，保持 reward、reset、observation、action semantics、训练数据与 seed 一致；若 actor、update schema 和 pretraining 同时改变，结果按组合方案归因。这样可以把每个任务中的特殊指标与共同的比较条件联系起来。

### Shadow Hand cube reorientation：灵巧主任务

`Isaac-Repose-Cube-Shadow-Direct-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 中对应 Shadow hand 的 cube in-hand reorientation。实验固定使用这一 ID；OpenAI-FF、OpenAI-LSTM 和 vision 变体各有自己的配置，sensor specification、state/action 维度与部署条件应按实际配置核验。

该任务可以直接测量多指接触下的姿态控制与掉落。按照共用协议固定 observation，明确 privileged split、history 和 delay，比较预定义姿态成功率、掉落率、environment interactions、wall-clock 与 inference latency。初始 grasp、物体或 reference 改变后，重新建立相应 baseline。

### Franka cube lift：较简单 manipulation 接口

`Isaac-Lift-Cube-Franka-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 中对应采用 joint position control 的 Franka cube lift。实验按这一精确 ID 核验接口，IK-Abs 与 IK-Rel 变体分别对应其他动作配置。

该任务可以在较简单的 manipulation 设置下检查采样、command 与奖励闭环。按照共用协议预定义 lift success 和掉落事件，报告成功率、掉落率、environment interactions、wall-clock 与 inference latency。灵巧手中的接触与迁移表现由手部任务另行评估。

### Ant：优化实现对照

`Isaac-Ant-v0` 在 [Isaac Lab v2.2.0 / classic](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#classic) 中对应 MuJoCo ant robot 的定向运动任务。本节选择 manager-based ID，`Isaac-Ant-Direct-v0` 属于另一环境配置。

Ant 用于观察 ratio、entropy/KL 估计和优化控制的行为。按照共用协议预定义该配置的 episodic return、目标方向位移与 episode length，报告 environment interactions、wall-clock、inference latency 和 KL/clip fraction；掉落率记 N/A。Ant return 与 manipulation 指标分别报告，其结果用于优化实现诊断。

每个任务都应分别比较交互预算和计算预算。报告固定 interactions 与固定 wall-clock 下的结果，同时记录硬件、batch、denoising steps、action horizon、初始化或预训练来源，以及预算耗尽条件。Action horizon 和 denoising horizon 是两个独立维度，可参照 [dppo-2024](bibliography.md#dppo-2024) v3 §3、§4.3；比较 density 计算方式时应控制这些条件，多个条件共同变化时按组合解释结果。

仿真 fine-tuning、真机部署和真机数据训练需要分别规划。[dppo-2024](bibliography.md#dppo-2024) v3 §5.4 的 One-leg hardware evaluation 是 zero-shot 部署，real-data fine-tuning/co-training 仍需独立设计。本章的任务方案聚焦仿真接口验证；进入真机实验前，还应核对部署观测、latency、执行限制和硬件安全流程，并完成独立安全检查。
