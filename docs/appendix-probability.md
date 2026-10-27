# 附录：On-policy diffusion 的概率基础

本附录集中保存 on-policy diffusion 的概率定义、rollout 记录和 entropy/KL 估计，供实现 likelihood 或 exact-inversion 时查阅。主文档 [04](04-onpolicy-diffusion-interface.md) 保留执行 mapping 与任务设置。

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
