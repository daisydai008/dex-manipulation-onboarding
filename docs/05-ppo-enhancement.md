# 05 面向 retargeting 的 PPO 增强

PPO 增强应按修改位置分成 update/estimation、demonstration/residual 集成、并行训练与课程三层，而不是把新 actor、数据来源和环境吞吐混为一种算法进步。[ppo-2017](bibliography.md#ppo-2017)、[implementation-matters-2020](bibliography.md#implementation-matters-2020) 与 [on-policy-actor-critic-2020](bibliography.md#on-policy-actor-critic-2020) 的 abstract 分别支持多 epoch surrogate update、code-level optimization 的影响和系统化设计选择评估。

本章的所有 REGRIND 插入点都是适配假设，不是源码审计或训练结果。REGRIND 项目的 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练只是接口背景；每个方向均列 baseline 问题、数据/信号、改动接口、证据层级与隔离评估，并用【推测】标注超出 abstract 的实现建议。

## 从失败信号选择接口

【机制相关】【需新证据】update-stage KL/clip fraction 异常时，先排查 log-prob、advantage 与 normalization，再单独改变 LR、epoch 或 clip。记录同一原始 action 的新旧 likelihood、done/truncation 与估计量，避免把记录错误当作优化不稳；何时不选：如果问题发生在 rollout 执行前的 reference/reset 或观测不可得环节，不先调整 optimizer。依据是 [implementation-matters-2020](bibliography.md#implementation-matters-2020) 的实现归因问题，具体顺序是待验证的诊断设计。

【机制相关】【需新证据】几何匹配但接触不可行时，先检查 reference、base controller 和 feasible resets，不先归咎 actor。记录 object support/slip、base-only 失败、residual 饱和与接触一致性，先改变可执行性接口再考虑策略参数化；何时不选：若相同 reference/base 已通过闭环检查、失败明确集中在 update 之后，转查概率与估计接口。依据与边界见 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

【机制相关】【需新证据】早期失败使后续 phase 缺少样本时，先检查分阶段覆盖与 reset 可行率，再比较 phase resets/curriculum。保持 actor/reward 不变，并始终在固定部署初始状态上报告 end-to-end success；何时不选：若中间接触状态无法重建，或各 phase 已有充分覆盖，不以改 reset 掩盖 reference 或 update 缺陷。该路线仅借鉴 [demostart-2024](bibliography.md#demostart-2024) 的课程相关性。

【机制相关】【需新证据】只有 observation、数据与 update 口径一致后仍有动作表示不足的信号，才比较 diffusion actor。先验证多模态成功动作与 Gaussian baseline 的失败关联，再改变 actor 和必要的概率记录接口；何时不选：若主要问题是部署输入缺失、示范未成功、log-prob 错误或 latency 超预算，不用更复杂 actor 替代修复。候选依据 [diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 与 [dppo-2024](bibliography.md#dppo-2024)，目标任务收益仍需实验。

## Update/estimation 层

### 固定 PPO 更新与估计口径

Baseline 问题是同名 PPO 实现可能在 normalization、optimizer 与 rollout 处理上不同，导致增强收益无法归因。【论文直接验证】[implementation-matters-2020](bibliography.md#implementation-matters-2020) 的 abstract 指出 code-level optimization 解释其研究中 PPO 相对 TRPO 的多数回报提升；[on-policy-actor-critic-2020](bibliography.md#on-policy-actor-critic-2020) 研究 50+ choices，但本导读不据 abstract 指定某个 hyperparameter 必然最优。

【机制相关】【推测】所需信号是 rollout 的 reward、done/truncation、value estimate、old log-prob、advantage 与 normalization statistics；改动接口是 estimator、surrogate loss 和 optimizer。面向 REGRIND 的适配假设是先检查 time-limit bootstrapping、advantage normalization、value scale、minibatch/epoch、gradient clipping 与 KL/clip fraction 记录，而不是先改 retargeting objective；这些具体审计项是根据上述实现归因问题提出的检查清单，不冒充论文 abstract 的逐项结论。

【需新证据】【推测】隔离评估应保持 actor、reward、reference、reset 和 environment steps 一致，每次只改变一个实现因素。分别报告多个固定 seed 的 task success、reference error、掉落率、KL/clip fraction、value error 与 wall-clock，先在固定动作接口上确认稳定性，再考虑下层候选；来源与证据上限仍是 [ppo-2017](bibliography.md#ppo-2017) 及两篇 implementation study，不把该方案写成已验证的 dexterous 配方。

### 更换 actor 与 likelihood 对象

Baseline 问题是 Gaussian actor 在一致数据和更新条件下可能仍无法表达任务所需的动作模式，替换 diffusion actor 则会改变 likelihood 与计算量。【论文直接验证】[dppo-2024](bibliography.md#dppo-2024) v3 §4–5 验证 denoising-step PPO 与 demonstration fine-tuning；它不是任意 auxiliary-action 模型可逆、可求 exact density 或已获灵巧手收益的证据。

【机制相关】【需新证据】所需信号由概率对象决定。符合 [04 条件推导](04-onpolicy-diffusion-interface.md#rollout-记录) 的 auxiliary actor 保存原始辅助动作、old log-prob 与 conditioning，DPPO 则保存可重建 denoising trajectory likelihood 的扩展 state/action 信息；改动接口是 sampling、rollout schema 与 likelihood evaluation。面向 REGRIND 的适配假设是先固定 base/reference 与参数无关的执行 mapping，边界见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

【需新证据】隔离评估先建立 Gaussian baseline，再在同任务与同源 demonstrations 条件下比较候选 diffusion actor。分别控制 interactions 和 wall-clock，记录 inference latency、显存、更新耗时、成功率与恢复行为；若 actor、update schema、pretraining 同时改变，只能归因于组合，不能将差异单独解释为 actor expressiveness。[dppo-2024](bibliography.md#dppo-2024) v3 §4.3、Appendix D 的计算讨论不提供目标任务的预设赢家。

## Demonstration/residual 集成层

### Demonstration 初始化与联合训练

Baseline 问题是 sparse success 或高维接触探索导致从零学习成本高。【论文直接验证】[dapg-2018](bibliography.md#dapg-2018) 的 abstract 报告少量 human demonstrations 降低 24-DoF hand 的 sample complexity 并提高 robustness；不把 DAPG 的具体更新式或其原算法直接称为 PPO enhancement。

【机制相关】【推测】所需数据是 observation/action 一致的 robot demonstrations，改动接口是 BC initialization 或辅助 imitation loss。面向 REGRIND 的适配假设是先用经过动力学校验的 retargeted trajectory，再比较初始化与持续 imitation regularization；reference 不能直接被当作已成功的 expert action，数据前置条件见 [03](03-retargeting-to-policy.md#用途一bc-数据)。

【需新证据】【推测】隔离评估应比较无示范、只初始化、持续辅助损失三种设置，固定 demonstration 数量、质量与 interaction budget。记录初始成功率、后续提升、偏离 reference 后恢复能力和 demo-overfitting，依据 [dapg-2018](bibliography.md#dapg-2018) 只提出路线，不承诺 PPO 或 REGRIND 的收益。

### Base controller 与 residual

Baseline 问题是位置级 reference 的几何匹配不能消除真实接触与摩擦误差。【论文直接验证】[residual-rl-2018](bibliography.md#residual-rl-2018) 的 abstract 验证 conventional control 与 RL signal superposition 的真机 block assembly；它没有验证 retargeting、diffusion actor 或灵巧手的任意组合。

【机制相关】【推测】所需信号是 base command、policy 原始动作、执行后 command、tracking error、object state 与接触反馈；改动接口是 action composition 和 reward attribution。面向 REGRIND 的适配假设是冻结 base mapping 与 residual scale 后再训练 residual；对 auxiliary actor 必须保留 policy action，不能用 clipped actuator command 替代 ratio 中的随机变量，理由见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

【需新证据】【推测】隔离评估应比较 base-only、同 reference 的 Gaussian residual、直接控制以及候选 diffusion residual。记录 task success、residual magnitude、饱和比例、接触失败与外推 reference 上的稳定性，且单独测 base controller 变更；[residual-rl-2018](bibliography.md#residual-rl-2018) 只支持该分工的机制相关性，不保证所有不可行 reference 都能由 residual 修复。

### Tracking、RSI 与 demonstration-led reset

Baseline 问题是长 reference 的早期失败让策略无法接触后续状态，而单纯 imitation objective 可能压制任务完成。【论文直接验证】[deepmimic-2018](bibliography.md#deepmimic-2018) 的 abstract 支持 motion imitation 与 task objective，[demostart-2024](bibliography.md#demostart-2024) 支持 sparse reward、少量 simulation demonstrations 与 auto-curriculum；两篇的具体 RSI/reset 算法均不在本导读的 abstract 证据内。

【机制相关】【推测】所需数据是 phase-aligned reference、可恢复的 joint/object state 与成功信号；改动接口分别是 reference observation、tracking reward 和 reset sampler。面向 REGRIND 的适配假设是将 RSI 作为“从 reference 不同阶段初始化”的候选思想，不宣称已核验 DeepMimic 的 RSI 细节；reference state 的接触一致性检查与 [03](03-retargeting-to-policy.md#用途二tracking-reference-与-rsi) 一致。

【需新证据】【推测】隔离评估应固定 actor，分别改变 tracking reward 和 reset distribution，不同时加入二者后归因于课程。对固定部署初始状态报告 end-to-end success，同时报告各 phase 的条件成功率、reset 可行率和 reference error，避免把 [demostart-2024](bibliography.md#demostart-2024) 的课程启发误写为已解决长时手部接触。

### Split-and-aggregate 数据聚合

Baseline 问题是并行数据增加后 PPO 性能饱和，不是示范不足。【论文直接验证】[sapg-2024](bibliography.md#sapg-2024) 的 abstract 提出拆分环境 chunks 再以 importance sampling 聚合；本节因其涉及多来源 rollout 集成而讨论它，但 SAPG 本身不是 demonstration 或 residual 方法。

【机制相关】【推测】所需信号是各采样 policy 的 likelihood、trajectory 来源和对应 advantage；改动接口是 rollout partition、behavior-policy bookkeeping 与 importance weighting。面向 REGRIND 的适配假设是先在同一任务/同一 residual actor 下验证聚合，再考虑不同 reference phase 的数据；abstract 未报告跨 phase 混合或 auxiliary-action actor 集成，这些不能作为现成算法选项宣称。

【需新证据】【推测】隔离评估应固定总环境数量、总 samples 和网络容量，对比 vanilla PPO 与 SAPG-style aggregation，另扫并行规模。记录 importance-weight 分布、有效样本量、回报、GPU 时间和内存；候选是否适合 REGRIND 取决于实测瓶颈，不能从 [sapg-2024](bibliography.md#sapg-2024) 的其他环境结果推断手部收益。

### Multi-agent 条件性参照

Baseline 问题只有在明确存在多个 cooperative agents、各自 observation/action partition 时才成立。【论文直接验证】[mappo-2021](bibliography.md#mappo-2021) 的 abstract 验证四类 cooperative game testbed；[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 另报告部分双手协同任务受益，但二者不能证明任意手指划分最优。

【机制相关】【推测】所需信号是每个 agent 的 local observation/action、shared reward 和可用的 joint training information；改动接口是 policy/critic organization。面向 REGRIND 的适配假设仅在先批准 multi-agent 建模后成立；单 actor residual 不是 MAPPO 的应用理由，不建议为采用方法而强行拆指。

【需新证据】【推测】隔离评估应在相同任务、总参数量与观测权限下比较 single-agent 和已明确分工的 multi-agent 设置。记录 coordination failure 与 sample efficiency；若部署仍只有单 actor，则将 [mappo-2021](bibliography.md#mappo-2021) 保留为条件性阅读而不进入实现计划。

## 并行训练与课程层

### 并行规模与 rollout 长度

Baseline 问题是增加环境数量可能改变每次更新的时序长度、梯度数据分布和计算瓶颈。【论文直接验证】[massively-parallel-2021](bibliography.md#massively-parallel-2021) 的 abstract 在 ANYmal 上分析大规模并行和 curriculum，并验证真机迁移；这不是灵巧手接触结果，也不保证 diffusion actor 有同样加速比。

【机制相关】【推测】所需信号是 environment steps/s、simulation/actor/update 分段耗时、rollout length 与显存占用；改动接口是 environment batching、rollout collection 与 minibatch schedule。面向 REGRIND 的适配假设是先测接触仿真、actor inference 或优化器哪一项主导耗时，再调整并行数，而不只以 GPU utilization 作为目标。

【需新证据】【推测】隔离评估应同时进行固定 total samples 的并行规模实验和固定 wall-clock 的效率实验。保持 reference/reset、task distribution 与 actor 不变，记录 task success、吞吐和时序 credit assignment 的变化；依据 [massively-parallel-2021](bibliography.md#massively-parallel-2021) 只提出测量设计，课程收益另行评估。

### Domain randomization 与 ADR

Baseline 问题是仿真视觉或动力学分布过窄会使部署性能不稳定，但两类 randomization 的证据来源不同。【论文直接验证】[domain-randomization-2017](bibliography.md#domain-randomization-2017) 的 abstract 直接验证 rendering randomization 与 object localization；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 则验证 ADR、memory-augmented control 和复杂真机操作，不能把前者直接称为 contact dynamics randomization 验证。

【机制相关】【推测】所需信号是待随机化参数、success/failure 与部署估计误差，改动接口是 environment parameter sampler、curriculum scheduler 和 evaluation distribution。面向 REGRIND 的适配假设是将相机/感知、摩擦/质量、actuation/delay 分开 randomize；具体范围需由硬件与仿真误差给出，而不是从别的系统抄取。

【需新证据】【推测】隔离评估应比较无 randomization、固定范围和 adaptive range，并冻结测试分布。单独记录各 perturbation family 的性能、平均值与最差条件，以及 privileged state 到部署观测的差异；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 的 ADR 结果不等于 REGRIND 已具备同样 memory/adaptation。

### 多任务并行与 reference 课程

Baseline 问题是多任务数据可能竞争 shared capacity，而不是把单任务环境直接并排即可获得多技能。【论文直接验证】[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 的 abstract 报告多数 multi-task/few-shot 设置失败；[demostart-2024](bibliography.md#demostart-2024) 的课程成功不能抵消该证据边界。

【机制相关】【推测】所需信号是 task/reference ID、各任务成功率、reset 难度和采样比例；改动接口是 task-conditioned observation、reset scheduler 与 sampling weights。面向 REGRIND 的适配假设是先在单 reference 证明闭环可行，再逐步扩展物体/轨迹，避免在算法与任务分布同时改变时声称增强有效。

【需新证据】【推测】隔离评估应比较独立单任务 policy、均匀多任务训练与课程采样，固定总 samples 并报告 per-task success、最差任务和任务间遗忘。选择依据来自 [bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 的 multi-task 限制与 [demostart-2024](bibliography.md#demostart-2024) 的 curriculum 相关性，不承诺 shared policy 一定优于独立策略。

## 评估顺序与停止条件

【机制相关】【推测】选型顺序应先确认 baseline 的观测、动作与 update 记录正确，再按瓶颈选择一个方向。成功示范足够时优先比较 imitation 初始化，几何 reference 可用但动力学偏差明显时比较 residual，探索覆盖不足时比较 reset curriculum，吞吐扩展饱和时比较 aggregation；只有在共同数据和 update 口径固定后，才把 [dppo-2024](bibliography.md#dppo-2024) 或 [04](04-onpolicy-diffusion-interface.md#概率对象) 中满足条件的模型作为 actor 候选。这是基于上述证据的条件选择，不是优劣排名。

【需新证据】【推测】每次实验都应有明确的停止条件和复核节点。若原始 action/log-prob 不一致、reference reset 物理不可行、部署观测不可得或 compute budget 不支持目标控制周期，应先修复接口而不是继续叠加增强；若改善只出现在训练 reward 而非固定测试 task success，则保留负结果。该评估原则呼应 [implementation-matters-2020](bibliography.md#implementation-matters-2020) 的归因问题，不构成本仓库外的代码实施授权。
