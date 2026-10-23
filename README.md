# Dexterous manipulation × on-policy diffusion 导读

这份导读面向熟悉 diffusion 理论、正寻找 dexterous hand 落地场景的读者。它支持一个决定：on-policy diffusion 工作可以落在灵巧操作的哪个接口上。它不管排期、分工、硬件预算与真机部署细节，那些属于 REGRIND 侧的执行文档。

## 背景

灵巧操作的核心难点是接触丰富、部分可观测、且任务间动作语义不统一。In-hand reorientation、grasp acquisition、arm-hand 协同、双手、long-horizon 是五个不同问题，不能按手的自由度或算法名称横向比较；观测侧要分别记录视觉、proprioception、tactile 与 privileged simulator state，部署时拿不到训练用的 privileged state 就必须另补 state estimator。这一侧的任务划分与证据见 [01 问题结构](docs/01-problem-structure.md)。

生成式策略接入 on-policy RL 的主线，是把 multimodal 动作分布的表达能力带进 PPO 一类需要逐样本 log-likelihood 的更新里。条件动作生成（diffusion-policy-2023）先解决 imitation 侧的表达；offline 价值引导（diffusion-ql-2022、idql-2023）把 diffusion 用进 RL 但不碰 on-policy ratio；denoising-step PPO（dppo-2024）绕开最终动作的边缘密度，在扩展 state 上对每步 denoising 求 likelihood；再往前是与 DPPO 并列的 exact-inversion 一类：正面恢复最终动作的精确 log-likelihood。本导读不复述这条线，只把它作为对照面。完整的历史展开见 [docs/diffusion-history](docs/diffusion-history/README.md)。

## 关键术语

首次使用后不再重复定义。

- **Gaussian PPO baseline**：以高斯（对角协方差）为 actor、用 PPO 更新的对照基线，所有增强方案都与它比，不把实现细节差异误算成 policy class 收益。
- **auxiliary action ξ**：生成式 actor 采样出的原始随机变量（去噪链末端或中间量），PPO ratio 作用在它上面，不等于最终下发给机器人的执行动作。
- **conditioning**：策略实际读入的条件，含观测、reference/phase、history 或 recurrent state，以及当时的 normalization 约定；冻结它才能比较新旧策略。
- **residual / residual scale**：base controller 输出之上由 RL 学习的修正量，residual scale 是其幅度系数；组合 `u = base + α·ξ` 中 α 即 scale。
- **tracking reference**：作为 policy 时变跟踪目标的 retargeted motion，与作为动作标签的 BC 数据是两种用途。
- **privileged state**：训练时仿真可得、部署时真实机器人拿不到的物体状态；actor 用了它就必须另补估计器。

## 起步路线

四条路线各自回答一个问题（与 [02](docs/02-method-landscape.md) 按资源盘点的三条起步路线不同维度），每条给出前置、第一步、预期产出、停止条件，并标注支撑文献。均为【机制相关】【需新证据】的实验建议，不是训练收益承诺；具体选型与失败信号排查见 [02 决策支持](docs/02-method-landscape.md)。

### 路线 1 · on-policy diffusion 能直接在灵巧手上跑吗

能，但先在固定执行 mapping 下做 actor 替换，把概率对象按 [04](docs/04-onpolicy-diffusion-interface.md#概率对象) 的条件推导约定清楚，再谈收益。

- 前置：可复现 simulator、reward/reset、已一致的 Gaussian PPO baseline。
- 第一步：只替换 actor 为生成式策略，rollout schema、reward、观测、seed 全部冻结。
- 预期产出：与 baseline 归因隔离的 actor 对照（成功率、KL/clip fraction、latency）。
- 停止条件：log-prob 对不上、或 inference latency 超出控制周期预算。
- 支撑：[ppo-2017](docs/bibliography.md#ppo-2017)、[implementation-matters-2020](docs/bibliography.md#implementation-matters-2020)、[dppo-2024](docs/bibliography.md#dppo-2024)。

### 路线 2 · 没有精确 log-likelihood 怎么办

用 DPPO 式：不需求最终 action chunk 的边缘密度，在扩展 state 上对每步 denoising 的 Gaussian transition 求 likelihood 形成 PPO ratio。这与 exact-inversion 路线互为对照——一个绕开边缘密度，一个正面恢复它。

- 前置：成功 demonstrations 用于预训练、可交互环境、可重建 denoising trajectory 的记录。
- 第一步：按 [04 rollout 记录](docs/04-onpolicy-diffusion-interface.md#rollout-记录) 存扩展 state 的逐步 likelihood，再做 demonstration fine-tuning。
- 预期产出：demo 初始化的 on-policy fine-tuning 闭环与样本复杂度记录。
- 停止条件：训练/部署数据版本失配，或逐步 likelihood 无法重算。
- 支撑：[dppo-2024](docs/bibliography.md#dppo-2024)、[diffusion-policy-2023](docs/bibliography.md#diffusion-policy-2023)。

### 路线 3 · 已经有 retargeting 或 base controller 了呢

让生成式 actor 只学 residual，base controller 固定不动。这把"生成式策略的表达"和"底层控制的可行性"解耦，也最贴近 retargeting 场景。

- 前置：reference 物理可行、base controller 能独立闭环、residual scale 冻结。
- 第一步：固定 base 与执行 mapping，用生成式 residual 替换 Gaussian residual，保留 policy 的原始 auxiliary action。
- 预期产出：控制分工与 residual 作用范围、饱和率。
- 停止条件：base-only 已失稳、或 reference 本身不可行（先修接口，不用 actor 掩盖）。
- 支撑：[residual-rl-2018](docs/bibliography.md#residual-rl-2018)、[deepmimic-2018](docs/bibliography.md#deepmimic-2018)、[demostart-2024](docs/bibliography.md#demostart-2024)。

### 路线 4 · 没有现成策略、只有人类运动数据呢

diffusion 也可以不在 actor 上，而在数据与运动生成一侧：把人类视频 / mocap 变成 policy-ready 的 reference 或 demonstration。这是把生成模型当作数据扩增与 retargeting 工具，而非策略参数化。

- 前置：人类运动或视频记录、跨 embodiment 对齐手段、接触可行性校验。
- 第一步：生成 / retarget 候选轨迹，先做动力学与接触可行性筛选，再决定用作 BC、tracking 还是 reset。
- 预期产出：可执行 reference 的可行率与覆盖、以及它们的下游用途分类。
- 停止条件：接触可行性筛选通过率过低，或生成轨迹与真实接触分布系统性失配。
- 支撑：[dexcap-2024](docs/bibliography.md#dexcap-2024)、[robotic-telekinesis-2022](docs/bibliography.md#robotic-telekinesis-2022)、[dexmimicgen-2024](docs/bibliography.md#dexmimicgen-2024)、[dexdiffuser-2023](docs/bibliography.md#dexdiffuser-2023)。

## 对接 REGRIND

以下是把生成式 actor 插进 REGRIND 当前 retargeting 管线的候选接口，全部为【推测】【需新证据】的适配假设，不是代码审计或训练结果。REGRIND 侧是 Drake 位置级 retargeting 加 residual RL 加 Isaac 并行训练；三个可插入位置是：位置级 reference 导出之后的 residual（对应路线 3）、多步 action chunk 的生成（对应路线 1/2 的 horizon 选择）、以及部署噪声模型标定时的扰动生成。这些接口的具体概率约定与记录要求见 [04](docs/04-onpolicy-diffusion-interface.md#固定执行-mapping) 与 [03](docs/03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。本节不含硬件、排期与分工，那些在 REGRIND 侧文档。

## 使用与证据约定

文献库收录 43 篇作品，其中 19 篇 core、24 篇 extended；不要求全部先读。逐篇四问注释集中于 [bibliography](docs/bibliography.md)，主题章节负责跨文献综合，稳定 paper ID 不随标题或年份勘误变化。书目不冻结，可经全文核实后新增。本仓库不包含训练代码，REGRIND 插入点均为待验证的适配假设。

其中七篇是全文核实的真机灵巧手 diffusion 部署：[dexvla-2025](docs/bibliography.md#dexvla-2025)、[dexwild-2025](docs/bibliography.md#dexwild-2025)、[dexumi-2025](docs/bibliography.md#dexumi-2025)、[dexcast-2026](docs/bibliography.md#dexcast-2026)、[human2dex-2026](docs/bibliography.md#human2dex-2026)、[skillweave-2026](docs/bibliography.md#skillweave-2026) 走 imitation 路线，[modex-2026](docs/bibliography.md#modex-2026) 在真机 Allegro 上用 DPPO 对 diffusion policy 在线 fine-tune。它们证明 diffusion 能上真机灵巧手，但除 MoDex 外都不碰 on-policy ratio；on-policy diffusion 在接触丰富的 in-hand 真机上仍是空缺。

适配建议不等于已有实验结果。【论文直接验证】限定于所引论文实际机制、任务与指标；【机制相关】说明接口相关而非组合已验证；【需新证据】标出目标任务、硬件或组合尚待验证。除 DPPO v3 的指定全文外，其他论文仅使用所记录版本的 abstract 与公开元数据，越出该范围另标【推测】；“未报告”仅指本导读查阅的证据范围未报告。

推导与工程事实另列证据类别。【条件推导】只在列明前提下成立，不代表任意 diffusion sampler 满足条件或已取得收益；【官方工程文档】只支持固定版本的 registry/interface 事实，不支持 actor-gain 结论。完整约定见 [书目证据说明](docs/bibliography.md#证据约定)。

## 文件导航

按处境选读，不必全读。想直接选方向：读本 README 的四条路线，再按路线跳到对应章节。关心某条路线的数学/接口约束：路线 1、2 看 [04](docs/04-onpolicy-diffusion-interface.md)，路线 3、4 看 [03](docs/03-retargeting-to-policy.md)。需要选方法族或排查失败：看 [02](docs/02-method-landscape.md) 与 [05](docs/05-ppo-enhancement.md)。要查证某篇论文的证据范围：查 [bibliography](docs/bibliography.md)。想了解 diffusion 接入 on-policy RL 的来龙去脉：看 [diffusion 历史](docs/diffusion-history/README.md)。

- [01 问题结构](docs/01-problem-structure.md)：确定任务、观测与 benchmark 比较口径。
- [02 方法选择](docs/02-method-landscape.md)：按资源和可观察失败信号选择五族候选。
- [03 Retargeting 到 policy](docs/03-retargeting-to-policy.md)：检查轨迹用途、接触可行性与执行数据契约。
- [04 On-policy diffusion 接口](docs/04-onpolicy-diffusion-interface.md)：定义概率对象、rollout 记录、执行 mapping 与诊断任务协议。
- [05 PPO 增强](docs/05-ppo-enhancement.md)：从失败信号选择排查项，设计隔离实验。
- [diffusion 历史](docs/diffusion-history/README.md)：生成式策略接入 on-policy RL 的展开梳理。
- [注释书目](docs/bibliography.md)：维护 43 篇作品的身份、版本、证据与四问。
- [检查器](scripts/check_links.py)：检查交付文件的结构、条目、相对链接、机械风格及外部来源。

## 检查与接受范围

检查器只用 Python 标准库，不写 cache、日志或 fixture。交付文件清单显式登记在 `scripts/check_links.py` 的 `FILES` 集合，新文件须登记加入，编辑器与运行时辅助文件（如 `.vscode/`、`.pi-subagents/`、`.gitignore`）不属于交付树，运行检查前须从树中删除，本地忽略规则放全局 gitignore 或 `.git/info/exclude`。`--lint` 不联网，按内嵌身份映射锚定原有 36 篇 core/extended 身份，新增条目经登记与 arXiv 核验后接受（当前 43 条、19 core、24 extended）；完整模式核验记录版本的 arXiv API title/ID、书目外链、全部交付 Markdown 中的官方工程文档链接与内部 anchor。网络请求单次 15 秒、至多重试 2 次、同 host 间隔至少 1 秒、总联网预算 15 分钟；退出码为 0 全部通过、2 内容失败、3 网络未完成，内容失败优先，只有 failed=0 且 unverified=0 才通过。

```bash
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py --lint
python3 scripts/check_links.py
```

自动检查通过不等于内容接受。条件推导、DPPO 机制与选型建议仍需人工核对；执行者交回与独立内容核验分开，不以链接可达代替技术判断。
