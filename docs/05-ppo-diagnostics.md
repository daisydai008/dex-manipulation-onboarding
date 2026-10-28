# 05 PPO 失败排查与对照实验

> 本章的主线是“失败现象 → 改动接口 → 隔离实验”。先判断训练在哪个环节失效，再选择对应机制的论文作为参照，最后只改变一个变量来验证收益。

PPO 增强在这里按实验接口组织，而不是按算法名称罗列：先记录失败现象，再决定改 update/estimation、demonstration/residual 集成，还是并行训练与课程。每个方向都给出问题、论文依据、候选改动和隔离指标，便于把方法转成可执行的对照实验。

PPO 的增强需要按改动接口分别评估。[ppo-2017](bibliography.md#ppo-2017) 介绍多 epoch surrogate update，[implementation-matters-2020](bibliography.md#implementation-matters-2020) 研究 code-level optimization 的影响，[on-policy-actor-critic-2020](bibliography.md#on-policy-actor-critic-2020) 系统评估设计选择。这些工作为固定实现、逐项比较提供依据。

```text
失败现象
  → 定位 update / reference / reset / observation / throughput 中的具体接口
  → 选择相关机制
  → 固定其余条件做对照
  → 用指标决定继续、修复或停止
```

对 REGRIND，可以从 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练的接口出发设计实验。下文将论文结果和适配建议分开说明：先介绍方法解决的问题，再给出候选改动、所需记录和比较指标。项目中的具体实现与收益还需通过源码核查和实验确定。

## 从失败信号选择接口

更新后 KL 或 clip fraction 异常时，可以先核对概率与估计记录。保存同一原始 action 的新旧 likelihood、advantage、normalization 及 done/truncation 处理，确认一致后分别改变 LR、epoch 或 clip。[implementation-matters-2020](bibliography.md#implementation-matters-2020) 提供实现归因的依据；若问题出现在 rollout 执行前，则先检查 reference、reset 与观测来源。

几何匹配而接触失败时，可以先检查 reference、base controller 和 reset 的可执行性。记录 object support/slip、base-only 失败、residual 饱和与接触一致性，再决定调整哪个控制接口。相同 reference/base 已通过闭环检查、失败集中在 update 后时，再转查概率与估计，具体检查见 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

早期失败使后续 phase 很少得到采样时，可以比较 phase resets 或 curriculum。先确认各阶段的覆盖与 reset 可行率，在 actor、reward 固定的条件下改变 reset，并从固定部署初始状态报告 end-to-end success。该思路借鉴 [demostart-2024](bibliography.md#demostart-2024) 的课程设计；实施前需要重建一致的中间接触状态，各阶段覆盖充分时则优先检查 reference 或 update。

动作表示的比较应建立在观测、数据和更新口径一致的基础上。可以先分析多模态成功动作与 Gaussian baseline 失败的关联，再参考 [diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 和 [dppo-2024](bibliography.md#dppo-2024) 设计 actor 对照。部署输入、成功示范、log-prob 重算和 latency 预算需要先通过检查，随后用目标任务结果判断表示是否合适。

## Update/estimation 层

### 固定 PPO 更新与估计口径

同名 PPO 实现的 normalization、optimizer 和 rollout 处理可能不同，比较前需要固定这些细节。[implementation-matters-2020](bibliography.md#implementation-matters-2020) 报告 code-level optimization 解释了其研究中 PPO 相对 TRPO 的多数回报提升；[on-policy-actor-critic-2020](bibliography.md#on-policy-actor-critic-2020) 评估 50+ choices，为系统比较实现选项提供参照。

比较的核心量是同一个 action 在新旧策略下的 ratio，以及由 reward 与 value 估计得到的 advantage：

```text
ρ_t(θ) = exp( log πθ(a_t|s_t) − log π_old(a_t|s_t) )
surrogate = min( ρ_t·A_t, clip(ρ_t, 1−ε, 1+ε)·A_t )
```

这里的 `A_t` 不是额外超参数，而是由 rollout 的 reward、value 和 done/truncation 共同决定。以 GAE 为例，先算 `δ_t = R_t + γV(s_{t+1}) − V(s_t)`，再按 `Â_t = δ_t + γλÂ_{t+1}` 递推，等价于 `Â_t = Σ_{l≥0}(γλ)^l·δ_{t+l}`；done/truncation 的处理会直接改变这个估计。

可以先审查 estimator、surrogate loss 和 optimizer，再调整 retargeting objective。保存 reward、done/truncation、value estimate、old log-prob、advantage 与 normalization statistics，依次核对 time-limit bootstrapping、advantage normalization、value scale、minibatch/epoch、gradient clipping 和 KL/clip fraction 记录。这些是面向 REGRIND 提出的检查项，具体 hyperparameter 由目标任务实验选择。

对照实验可以保持 actor、reward、reference、reset 和 environment steps 一致，每次只改变一个实现因素。按多个固定 seed 报告 task success、reference error、掉落率、KL/clip fraction、value error 与 wall-clock，先确认固定动作接口下的训练行为，再测试其他增强。该方案沿用 [ppo-2017](bibliography.md#ppo-2017) 的更新框架，并结合上述 implementation study 的归因思路。

### 更换 actor 与 likelihood 对象

更换 actor 同时涉及动作表示、概率求值和计算成本。[dppo-2024](bibliography.md#dppo-2024) v3 §4–5 报告 denoising-step PPO 与 demonstration fine-tuning，可以用于设计 Gaussian actor 的对照。若选择其他 auxiliary-action 模型，则需根据 sampler 结构验证可逆性和 exact density 条件，并在目标灵巧手任务上测量收益。

采样与 rollout 记录应围绕所选概率对象实现。符合 [概率基础附录的 rollout 记录约定](appendix-probability.md#rollout-记录) 的 auxiliary actor 保存原始辅助动作、old log-prob 和 conditioning；DPPO 保存能够重建 denoising trajectory likelihood 的扩展 state/action 信息。对 REGRIND，可以先固定 base/reference 与独立于待更新参数的执行 mapping，再调整 sampling、rollout schema 和 likelihood evaluation，具体约定见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

比较可以从同任务、同源 demonstrations 下的 Gaussian baseline 开始。分别控制 interactions 与 wall-clock，记录 inference latency、显存、更新耗时、成功率和恢复行为；actor、update schema 与 pretraining 同时改变时，按组合方案解释结果。[dppo-2024](bibliography.md#dppo-2024) v3 §4.3、Appendix D 的计算讨论可用于选择测量项，目标任务中的成本与性能由实测确定。

## Demonstration/residual 集成层

### Demonstration 初始化与联合训练

Demonstrations 可以为 sparse-success 或高维接触任务提供成功行为的起点。[dapg-2018](bibliography.md#dapg-2018) 报告少量 human demonstrations 降低 24-DoF hand 的 sample complexity 并提高 robustness。将这一思路用于 PPO 时，需要单独定义示范如何进入初始化或训练损失。

可以比较 BC initialization 和持续的辅助 imitation loss。数据应包含 observation/action 一致的 robot demonstrations；采用 retargeted trajectory 时，还需完成动力学校验、动作语义对齐与成功片段筛选，具体要求见 [03](03-retargeting-to-policy.md#用途一bc-数据)。这一步将可执行记录转成监督数据，再用于 REGRIND 的候选训练方案。

持续辅助损失可以写成 `L = L_PPO + β·L_BC`：只初始化对应先在 demonstrations 上训练、随后令 `β=0`，持续辅助对应在 RL 更新中保留非零 `β`。比较时先固定 demonstrations 的数量和质量，再改变初始化方式或 `β`，避免同时改变数据来源。

实验可以设置无示范、只初始化、持续辅助损失三组。固定两组示范方案使用的数据数量与质量，并为各组设置相同 interaction budget，记录初始成功率、后续提升、偏离 reference 后的恢复能力和 demo-overfitting。[dapg-2018](bibliography.md#dapg-2018) 提供 demonstration 的方法依据，PPO 适配的作用通过三组结果判断。

### Base controller 与 residual

Residual learning 利用 base controller 执行已有控制规律，再学习接触与摩擦误差下的修正量。[residual-rl-2018](bibliography.md#residual-rl-2018) 在真机 block assembly 中验证 conventional control 与 RL signal superposition，为位置级 reference 的反馈修正提供参照。

执行合成可以写成 `u = clip(b(s) + αξ)`：`b(s)` 是 base command，`ξ` 是 policy 输出的 residual，`α` 决定 residual scale。记录时同时保存 `ξ`、`b(s)`、合成前的 `v=b(s)+αξ`、执行后的 `u` 和 clipping 规则。饱和率按 `v` 是否超过执行限制统计，多维动作可分别报告逐维比例与任一维触发比例；`u` 与 `v` 的差异用于确认 clipping 是否发生。

对 REGRIND，可以冻结 base mapping 与 residual scale 后训练 residual。保存 base command、policy 原始动作、合成与限制后的执行 command、tracking error、object state 和接触反馈，用于检查 action composition 与 reward attribution。Auxiliary actor 的 ratio 在原始 policy action 上计算，clipped actuator command 用于核对执行，概率条件见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

实验可以比较 base-only、同 reference 的 Gaussian residual、直接控制与候选 diffusion residual。记录 task success、residual magnitude、控制权限（residual authority）、饱和比例、接触失败，以及外推 reference 上的稳定性；base controller 的变更另做对照。以 [residual-rl-2018](bibliography.md#residual-rl-2018) 的控制分工为参照，可以先检查 reference 与 base 的可执行性，再测 residual 在给定权限内能补偿多少误差。

### Tracking、RSI 与 demonstration-led reset

Tracking 目标和 reset 课程分别影响策略追踪什么、从哪些状态开始学习。[deepmimic-2018](bibliography.md#deepmimic-2018) 报告 motion imitation 与 task objective 的组合，[demostart-2024](bibliography.md#demostart-2024) 报告 sparse reward、少量 simulation demonstrations 与 auto-curriculum。它们为长 reference 的目标权衡和后续 phase 覆盖提供不同参照，具体 RSI/reset 算法仍需结合正文核查。

目标权重可以写成 `R = w_imit·R_imit + w_task·R_task`：`R_imit` 衡量与 reference 的贴合，`R_task` 衡量任务完成。消融时固定其余条件，分别改变 `w_imit`、`w_task` 或 reset distribution，才能区分贴合提升是否伴随任务完成改善。

可以分别设计 reference observation、tracking reward 和 reset sampler。准备 phase-aligned reference、可恢复的 joint/object state 与成功信号后，先评估 imitation 目标和任务完成的关系；若早期失败使后续 phase 很少得到采样，再尝试从 reference 不同阶段初始化。REGRIND 的 contact-consistent reset 规则需另行定义，DeepMimic 的 RSI 原则见 [03](03-retargeting-to-policy.md#用途二tracking-reference-与-rsi)。

实验应固定 actor，分别改变 tracking reward 和 reset distribution，再测试二者的组合。单独消融用于识别各接口的作用，组合结果按完整方案报告。指标包括固定部署初始状态上的 end-to-end success、各 phase 的条件成功率、reset 可行率和 reference error；[demostart-2024](bibliography.md#demostart-2024) 的课程结果为实验设计提供参照。

### Split-and-aggregate 数据聚合

SAPG 研究并行数据增加后 PPO 性能趋于饱和的问题。[sapg-2024](bibliography.md#sapg-2024) 提出将环境拆成 chunks，再通过 importance sampling 聚合数据。本节将其放在集成层，是因为它改变了多来源 rollout 的组织方式，其主要作用位置是采样与更新。

对来自 behavior policy `μ` 的样本，importance weight 写成 `w_i = πθ(a_i|s_i) / μ(a_i|s_i)`；有效样本量可以用 `ESS = (Σ_i w_i)² / Σ_i w_i²` 估计。`w_i` 的分布和 ESS 用来判断聚合是否把不同采样来源混成了有效更新，而不是只增加了样本数量。

可以先在同一任务、同一 residual actor 下比较聚合方式。记录各 behavior policy 的 likelihood、trajectory 来源和对应 advantage，再实现 rollout partition、behavior-policy bookkeeping 与 importance weighting。不同 reference phase 的混合或 auxiliary-action actor 的集成，作为后续独立假设在小规模实验中验证。

对照可以固定总环境数量、总 samples 与网络容量，比较 vanilla PPO 和 SAPG-style aggregation，再单独扫描并行规模。记录 importance-weight 分布、有效样本量（effective sample size）、回报、GPU 时间与内存，判断聚合是否针对当前瓶颈产生作用。[sapg-2024](bibliography.md#sapg-2024) 提供方法参照，REGRIND 中的选择取决于这些测量结果。

### Multi-agent 条件性参照

Multi-agent 方法适用于已定义多个 cooperative agents 及各自 observation/action partition 的任务。[mappo-2021](bibliography.md#mappo-2021) 在四类 cooperative game testbed 中验证 MAPPO，[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 报告部分双手协同任务的收益。具体的手部划分方式需要由任务分工和实验结果确定。

采用这一建模时，需要为每个 agent 定义 local observation/action、shared reward，以及训练可用的 joint information，再设计 policy 与 critic 的组织方式。对 REGRIND，可以在明确分工后测试 multi-agent residual；现有单 actor 方案则保留为共同任务上的对照。

实验可以固定任务、总参数量与观测权限，比较 single-agent 和已定义分工的 multi-agent 设置，记录 coordination failure 与 sample efficiency。部署仍采用单 actor 时，[mappo-2021](bibliography.md#mappo-2021) 可保留为条件性参考；实施 multi-agent 的前提仍是明确的 observation/action partition。

## 并行训练与课程层

### 并行规模与 rollout 长度

增加环境数量会同时影响吞吐、每次更新的时序长度和梯度数据分布。[massively-parallel-2021](bibliography.md#massively-parallel-2021) 在 ANYmal 上研究大规模并行与 curriculum，并验证真机迁移。手部接触仿真与 diffusion actor 的计算组成需要按各自配置重新测量。

每次 update 的样本量可写成 `N_samples = N_envs × T_rollout`：增大 `N_envs` 会提高并行采样量，但 `T_rollout` 同时决定 advantage 与 minibatch 的时序结构。比较并行规模时分别进行固定 `N_samples` 的规模对照和固定 wall-clock 的效率对照，另一项作为测量结果，从而区分采样吞吐与更新开销。

可以先分段计时，再调整 environment batching、rollout collection 和 minibatch schedule。记录 environment steps/s、simulation/actor/update 耗时、rollout length 与显存，确定主要成本来自接触仿真、actor inference 还是优化器。并行数的选择应结合训练表现与这些成本，GPU utilization 作为辅助记录。

实验可以同时设置固定 total samples 的规模对照和固定 wall-clock 的效率对照。保持 reference/reset、task distribution 与 actor 一致，记录 task success、吞吐和时序 credit assignment 的变化。[massively-parallel-2021](bibliography.md#massively-parallel-2021) 为并行与课程提供参照，二者的收益通过独立对照分别报告。

### Domain randomization 与 ADR

Domain randomization 用训练分布变化应对部署差异，视觉与动力学需要分别设计。[domain-randomization-2017](bibliography.md#domain-randomization-2017) 报告 rendering randomization 对 object localization 的作用；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 报告 ADR、memory-augmented control 与复杂真机操作，提供另一类系统证据。

对 REGRIND，可以将相机/感知、摩擦/质量、actuation/delay 分组随机化。先记录待随机化参数、success/failure 与部署估计误差，再调整 environment parameter sampler、curriculum scheduler 和 evaluation distribution。范围应根据硬件与仿真误差确定，其他系统的参数用于设计参照。

实验可以比较无 randomization、固定范围与 adaptive range，并冻结测试分布。分别报告各 perturbation family 的表现、平均值和最差条件，同时检查 privileged state 与部署观测的差异。Memory/adaptation 另做对照，以 [openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 的 ADR 结果为参照评估各部分的作用。

### 多任务并行与 reference 课程

多任务训练需要显式分配任务数据，并检查 shared capacity 的竞争。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 报告多数 multi-task/few-shot 设置失败；[demostart-2024](bibliography.md#demostart-2024) 提供课程学习的参照。增加并行环境可以提高数据吞吐，多技能学习还需单独评估每项任务。

独立单任务 policy 与最终 shared policy 的差值可以记为 `G_i = S_i^single − S_i^multi`，它表示 negative transfer；采样比例和优化干扰也会影响这个差值。若要报告遗忘，需要记录同一 shared policy 在多个训练时点的 per-task success，并用 `S_i(t_before) − S_i(t_after)` 衡量学习后续任务后的性能下降。

可以从单 reference 的闭环开始，逐步扩展物体和轨迹。记录 task/reference ID、各任务成功率、reset 难度与采样比例，再调整 task-conditioned observation、reset scheduler 和 sampling weights。算法与任务分布分别改变，有助于区分表示、采样和课程各自的影响。

实验可以比较独立单任务 policy、均匀多任务训练与课程采样。固定总 samples，报告 per-task success、最差任务表现与任务间遗忘，判断 shared policy 的实际收益。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 和 [demostart-2024](bibliography.md#demostart-2024) 分别为多任务困难与课程设计提供参照。

## 评估顺序与停止条件

增强实验可以从正确记录 baseline 的观测、动作和 update 开始，再按主要瓶颈选择一个接口。成功示范充足时比较 imitation 初始化，几何 reference 可用而动力学偏差明显时比较 residual，后续阶段覆盖不足时比较 reset curriculum，并行扩展饱和时比较 aggregation。共同数据与更新口径固定后，再将 [dppo-2024](bibliography.md#dppo-2024) 或 [概率基础附录](appendix-probability.md#概率对象) 中满足条件的模型加入 actor 对照。

每次实验都应预先定义停止条件和复核节点。原始 action/log-prob、reference reset、部署观测或目标控制周期检查失败时，先修复对应接口；预算耗尽而任务指标持平或变差时，保留负结果和预算记录。训练 reward 与固定测试 task success 的变化出现分歧时，再检查奖励是否对应任务目标。这个评估顺序结合 [implementation-matters-2020](bibliography.md#implementation-matters-2020) 的归因问题，将结果落实到具体接口与任务指标。
