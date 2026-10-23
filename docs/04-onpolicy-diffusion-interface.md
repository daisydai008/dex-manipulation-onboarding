# 04 On-policy diffusion 的概率与执行接口

本章先定义 PPO 使用的随机变量，再讨论记录、优化与执行条件。下文的【条件推导】是自足的数学契约，不声称任意 diffusion sampler 可逆、可计算 Jacobian 或已有目标任务收益；有名称的方法只承担其自身证据范围内的主张，任务选择建议均标【机制相关】或【需新证据】。

## 概率对象

【条件推导】可求值的密度要求变换条件显式成立。给定固定 conditioning `c`，设基础变量 `z∈R^d` 有相对 Lebesgue measure 的已知密度 `p₀(z|c)`，辅助动作 `ξ=Fθ(z;c)∈R^d`；本推导要求 `Fθ` 在支持集内部是 C¹ diffeomorphism（一一可逆、正逆映射连续可微、Jacobian 非奇异，忽略零测边界），且逆映射和 log-determinant 可计算，才使用 change-of-variables 得到下式。一般 stochastic、多对一或维度改变的 diffusion sampler 不自动满足这些条件。

```text
z = Fθ⁻¹(ξ;c)
log qθ(ξ|c) = log p₀(z|c) − log |det D_z Fθ(z;c)|
```

【条件推导】exact density 仅指该模型的密度公式可求值，不表示不存在数值误差或已知执行动作密度。若执行动作 `u=g(c,ξ)`，多对一的 `g` 通常要对原像积分才能得到 `pθ(u|c)`；不能把某个 `ξ` 的 `qθ(ξ|c)` 直接命名为 `pθ(u|c)`。实现仍需检查 inverse round-trip、Jacobian 求值、支持集及浮点误差；这些是条件验证，不是已有 sampler 性能事实。

【论文直接验证】DPPO 提供另一种明确的 on-policy 概率对象。[dppo-2024](bibliography.md#dppo-2024) v3 §4.1 Eq. (4.1)–(4.4)、§4.2 Eq. (4.5)–(4.8) 在扩展 state `(s,a^{k+1})` 上使用 Gaussian denoising transition 的 likelihood 形成 PPO 更新，不要求求出最终 action chunk 的边缘密度；§4.3 还分别给出采样时与 Gaussian likelihood 求值时不同的 denoising noise 下限（σ^exp_min 与 σ^prob_min）。该方法不是上述可逆变换条件已满足的证据。

【机制相关】offline action generation 与 on-policy density evaluation 是不同接口。[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 与 [idql-2023](bibliography.md#idql-2023) 的 abstract 分别支持 value-guided diffusion 和 critic-weighted behavior samples；它们不能证明任意生成动作能直接用于 PPO ratio，也不能替未指定的 sampler 提供 entropy/KL 结论。

## Rollout 记录

【条件推导】PPO ratio 必须比较同一个已采样的辅助动作。对旧策略采到的 `ξ_t~qold(·|c_t)`，冻结其 conditioning `c_t`，新旧策略比较为 `r_t(θ)=exp(log qθ(ξ_t|c_t)−log qold(ξ_t|c_t))`；不能在 update 时重新采一个新 `ξ` 来替换分子对象，也不能从 clipped executed action 反推唯一原始变量。该 ratio 使用 [ppo-2017](bibliography.md#ppo-2017) 的新旧策略比较思想，这里明确其适用的随机变量。

【条件推导】rollout 至少应保存原始 `ξ_t`、采样时的 old log-prob 与完整 conditioning。conditioning 包括 policy 实际输入、reference/phase、history 或 recurrent state 的重建信息及当时的 normalization 约定；reward、done/truncation、value 与 advantage 另按 estimator 契约记录。旧参数下重算 log-prob 应与记录值在预定义数值容差内一致；只保存执行 command 不足以完成此检查。

【机制相关】【需新证据】更换概率对象会改变 rollout schema，不能只替换 actor 网络。DPPO 的记录需支持其 denoising trajectory 和扩展 state/action 的逐步 likelihood，依据 [dppo-2024](bibliography.md#dppo-2024) v3 §4；采用条件可逆模型时则按上面的 `ξ` 记录约定实现。两种 schema 都需独立验证数据一致性，不把其中一种的可用性外推到另一种。

## Entropy/KL 与优化控制

【条件推导】可求值的 log-density 不等于 exact entropy 或 exact KL。对固定 `c`，若支持集条件满足且期望存在，则定义如下；第二式方向是 `old‖new`，需要 `qold` 对 `qθ` 绝对连续，否则 KL 可以无穷大。

```text
H(qθ|c) = E_{ξ~qθ(·|c)}[−log qθ(ξ|c)]
D_KL(qold || qθ | c) = E_{ξ~qold(·|c)}[log qold(ξ|c) − log qθ(ξ|c)]
```

【条件推导】有限样本只能估计这些期望。直接 Monte Carlo 估计当前 entropy 应使用当前策略样本；若复用旧样本，则需满足支持集条件并作相应 importance weighting，直接把旧 rollout 上的 `−log qθ` 平均得到的是交叉熵估计。用旧 rollout 的 log-prob difference 估计 `old‖new` KL 时，还要说明 conditioning 来自旧 rollout 的经验分布。样本数、相关性与有限样本误差都影响估计，经验 KL 甚至可能为负；它们不是执行动作 entropy/KL，也不保证接触探索或性能改善。

【需新证据】KL-adaptive LR 仅是待验证的候选控制逻辑。可以预先指定辅助空间 `old‖new` KL 的目标区间与估计方法，在估计偏高时降低后续 update 的 LR、持续偏低时尝试提高，并与固定 LR 做单因素对照；区间、调节幅度和时序须由实验协议确定，这里不给未经验证的常数或稳定性承诺。先检查 log-prob、advantage 和 normalization，再分别比较 LR、epoch、clip，参见 [05](05-ppo-enhancement.md#从失败信号选择接口)。

## 固定执行 mapping

【条件推导】固定且与待更新 policy 参数无关的执行 mapping 可以折入环境，不要求 mapping 可逆。令 `s` 是包含 controller 状态的完整环境状态、`c=h(s)` 是本次决策的 conditioning，`u=g(s,ξ)` 在数据收集与相关更新期间不变，则可定义 `P̃(s'|s,ξ)=P(s'|s,g(s,ξ))`、`R̃(s,ξ)=R(s,g(s,ξ))`。在这个辅助动作环境中，policy 仍按 `qθ(ξ|c)` 采样并按同一个 `ξ` 计算 ratio；此推导不赋予 PPO 超出其原有近似目标的保证。

【条件推导】固定 base controller、residual scale 与 clipping 不因非可逆而自动破坏 auxiliary-space PPO。例如 `u=clip(b(s)+αξ)` 可作为 `g`，前提是 `b`、`α`、clipping 规则与相关 controller 状态转移不依赖待更新参数，并保存原始 `ξ`。被否定的是“auxiliary density 就是 executed-action density”的解释，而不是 residual composition 本身；[residual-rl-2018](bibliography.md#residual-rl-2018) 只提供 control-signal superposition 的独立工程动机，不是本推导的实验验证。

【条件推导】带内部状态的 controller/filter 必须作为环境动力学的一部分描述。若状态 `h_t` 会影响执行 command，应明确 `(s_t,h_t)` 的转移和 reset；policy 若使用该状态，则还须在 conditioning 中保存或可重建。把有记忆 controller 当作仅依赖当前 observation 的无状态函数，会遗漏本推导的前提。

【需新证据】固定 mapping 推导不覆盖 controller 与 actor 共同学习，也不允许随意复用过期 rollout。更新 reference、base controller、normalization、safety filter 或其内部状态规则后，旧数据未必仍来自相同环境和 conditioning 契约；仅保存 old log-prob 不能修正这些变化。面向 REGRIND 的 reference-conditioned residual 因而是适配假设，需先按 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟) 验证可执行性，再验证概率记录。

## 按诊断目的的任务验证

【机制相关】【需新证据】三个任务承担不同诊断目的，不是课程，也不按跨任务 return 排名。Shadow Hand 是灵巧主任务，Franka cube lift 检查较简单 manipulation 接口，Ant 隔离部分优化实现问题；任何一个任务上的改进都不能直接证明另外两个任务或真机有效。

【官方工程文档】registry 事实统一固定在 Isaac Lab v2.2.0 的 `Available Environments — Isaac Lab Documentation` 页面。下列链接各自绑定官方 hostname、版本 path、该 page title 与 section fragment；该页只支持环境 ID、任务描述及列出的动作接口，不承担 actor-gain 或默认维度证据。

### Shadow Hand cube reorientation：灵巧主任务

【官方工程文档】`Isaac-Repose-Cube-Shadow-Direct-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 列为 Shadow hand 的 cube in-hand reorientation。这里使用这一精确 ID，不与 OpenAI-FF、OpenAI-LSTM 或 vision 变体混用，也不从名称推断 sensor specification、state/action 维度或部署配置。

【机制相关】【需新证据】选择该任务是为了直接观察多指接触下的姿态控制与掉落，而不是把更广泛的 arm-hand 能力当作已覆盖。先建立 Gaussian baseline，再替换 actor；两组固定 reward、reset、observation（含 privileged split/history/delay）、action semantics、训练数据与 seed，比较预定义姿态成功率、掉落率、environment interactions、wall-clock 与 inference latency。若 actor、update schema、pretraining 同时改变，结果只能归因于组合；更换初始 grasp、物体或 reference 后须重新建立 baseline。

### Franka cube lift：较简单 manipulation 接口

【官方工程文档】`Isaac-Lift-Cube-Franka-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 列为 Franka cube lift，并明确是 joint position control。该 ID 不是 IK-Abs 或 IK-Rel 变体；接口核验不能由动作名称相似替代。

【机制相关】【需新证据】选择该任务是为了在不同于多指重定向的 manipulation 设置下检查采样、command 与奖励闭环。先建立 Gaussian baseline，再替换 actor；固定 reward、reset、observation、action semantics、训练数据与 seed，预定义 lift success 和掉落事件，报告成功率/掉落率、environment interactions、wall-clock 与 inference latency。若 actor、update schema、pretraining 同时改变，只能归因于组合；通过该检查不构成灵巧手迁移证据。

### Ant：优化实现对照

【官方工程文档】`Isaac-Ant-v0` 在 [Isaac Lab v2.2.0 / classic](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#classic) 列为 MuJoCo ant robot 的定向运动任务。这里选 manager-based ID，不与 `Isaac-Ant-Direct-v0` 混用。

【机制相关】【需新证据】选择 Ant 是为了检查 ratio、entropy/KL 估计与优化控制在非 manipulation 任务中的行为，而不是把 locomotion 成绩当作抓取证据。先建立 Gaussian baseline，再替换 actor；固定 reward、reset、observation、action semantics、训练数据与 seed，事先定义任务指标（如该配置的 episodic return、目标方向位移与 episode length），并报告 environment interactions、wall-clock、inference latency 和 KL/clip fraction；掉落率记 N/A。若 actor、update schema、pretraining 同时改变，只能归因于组合；不把 Ant return 与两个 manipulation 任务做统一排名。

【需新证据】任务协议还应分开交互预算和计算预算。每个任务报告固定 interactions 下的结果和固定 wall-clock 下的结果，注明硬件、batch、denoising steps、action horizon、初始化/预训练来源及预算耗尽条件；action horizon 与 denoising horizon 是不同维度，参见 [dppo-2024](bibliography.md#dppo-2024) v3 §3、§4.3。更换这些条件后，不能将差异单独归因于 density 计算方式。

【需新证据】仿真验证与真机在线 fine-tuning 必须分开规划。[dppo-2024](bibliography.md#dppo-2024) v3 §5.4 的 One-leg hardware evaluation 是 zero-shot 部署而非 real-data fine-tuning/co-training；本章任务设计也不提供真机在线学习证据。真机前需另行核对部署观测、latency、执行限制与硬件安全流程，概率接口正确并不等于安全认证。
