# 04 On-policy diffusion 的执行与任务接口

> 本章面向实现：如何固定执行 mapping、记录任务配置，以及按检查目的选择任务。概率定义与推导见 [附录](appendix-probability.md)。

On-policy diffusion 的实现除了 actor 本身，还需要固定执行命令的生成方式和任务评估条件。下面先说明执行 mapping，再给出三个任务的配置与比较设置。

## 固定执行 mapping

固定且与待更新 policy 参数无关的执行 mapping 可以并入环境动力学。令 `s` 为包含 controller 状态的完整环境状态，`c=h(s)` 为本次决策的 conditioning；若 `u=g(s,ξ)` 在数据收集与相关更新期间固定，则可定义 `P̃(s'|s,ξ)=P(s'|s,g(s,ξ))`、`R̃(s,ξ)=R(s,g(s,ξ))`。这个构造允许不可逆的 `g`，policy 在辅助动作环境中按 `qθ(ξ|c)` 采样，并对同一个 `ξ` 计算 ratio；PPO 仍使用其原有的近似目标。

固定的 base controller、residual scale 与 clipping 可以组成这样的 mapping。例如 `u=clip(b(s)+αξ)` 中，只要 `b`、`α`、clipping 规则和相关 controller 状态转移独立于待更新参数，并保留原始 `ξ`，就可以在辅助动作空间进行 PPO 更新。此时 `qθ` 仍表示辅助密度，执行动作密度需按 composition 另外确定。[residual-rl-2018](bibliography.md#residual-rl-2018) 提供 control-signal superposition 的工程参照；这里的概率关系来自上述固定 mapping 条件。

带内部状态的 controller 或 filter 需要连同状态转移一起描述。若 `m_t` 影响执行 command，就应定义 `(s_t,m_t)` 的转移与 reset；policy 使用该状态时，还需将其保存到 conditioning 中或提供重建信息。这样才能完整描述当前动作对后续状态的影响。

执行规则改变后，需要重新确认 rollout 的有效性。更新 reference、base controller、normalization、safety filter 或内部状态规则，都可能改变环境或 conditioning；old log-prob 记录解决的是策略概率比较，执行条件还需单独检查。Controller 与 actor 共同学习需要另行建立相应推导。对 REGRIND 的 reference-conditioned residual，可以先按 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟) 验证可执行性，再检查概率记录与数据收集时的约定是否一致。

## 按检查目的选择任务

三个任务用于检查不同环节，可以分别开展实验。Shadow Hand 直接评估灵巧手控制，Franka cube lift 检查较简单的 manipulation 接口，Ant 观察优化实现在其他动力学中的行为。各任务的结果按自身指标解释，跨任务迁移与真机表现另外验证。

环境定义统一引用 Isaac Lab v2.2.0 的 `Available Environments — Isaac Lab Documentation` 页面。下列链接固定了官方 hostname、版本 path、page title 和 section fragment，用于核对环境 ID、任务描述及列出的动作接口。具体实验中的 state/action 维度、观测配置和 actor 表现，分别通过配置检查与训练评估确定。

三个任务共用一套对照实验设置。先建立 Gaussian baseline，再替换 actor，保持 reward、reset、observation、action semantics、训练数据与 seed 一致；若 actor、update schema 和 pretraining 同时改变，结果按组合方案归因。这样可以把每个任务中的特殊指标与共同的比较条件联系起来。

### Shadow Hand cube reorientation：灵巧主任务

`Isaac-Repose-Cube-Shadow-Direct-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 中对应 Shadow hand 的 cube in-hand reorientation。实验固定使用这一 ID；OpenAI-FF、OpenAI-LSTM 和 vision 变体各有自己的配置，sensor specification、state/action 维度与部署条件应按实际配置核验。

该任务可以直接测量多指接触下的姿态控制与掉落。按照共用实验设置固定 observation，明确 privileged split、history 和 delay，比较预定义姿态成功率、掉落率、environment interactions、wall-clock 与 inference latency。初始 grasp、物体或 reference 改变后，重新建立相应 baseline。

### Franka cube lift：较简单 manipulation 接口

`Isaac-Lift-Cube-Franka-v0` 在 [Isaac Lab v2.2.0 / manipulation](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#manipulation) 中对应采用 joint position control 的 Franka cube lift。实验按这一精确 ID 核验接口，IK-Abs 与 IK-Rel 变体分别对应其他动作配置。

该任务可以在较简单的 manipulation 设置下检查采样、command 与奖励闭环。按照共用实验设置预定义 lift success 和掉落事件，报告成功率、掉落率、environment interactions、wall-clock 与 inference latency。灵巧手中的接触与迁移表现由手部任务另行评估。

### Ant：优化实现对照

`Isaac-Ant-v0` 在 [Isaac Lab v2.2.0 / classic](https://isaac-sim.github.io/IsaacLab/v2.2.0/source/overview/environments.html#classic) 中对应 MuJoCo ant robot 的定向运动任务。本节选择 manager-based ID，`Isaac-Ant-Direct-v0` 属于另一环境配置。

Ant 用于观察 ratio、entropy/KL 估计和优化控制的行为。按照共用实验设置预定义该配置的 episodic return、目标方向位移与 episode length，报告 environment interactions、wall-clock、inference latency 和 KL/clip fraction；掉落率记 N/A。Ant return 与 manipulation 指标分别报告，其结果用于优化实现检查。

每个任务都应分别比较交互预算和计算预算。报告固定 interactions 与固定 wall-clock 下的结果，同时记录硬件、batch、denoising steps、action horizon、初始化或预训练来源，以及预算耗尽条件。Action horizon 和 denoising horizon 是两个独立维度，可参照 [dppo-2024](bibliography.md#dppo-2024) v3 §3、§4.3；比较 density 计算方式时应控制这些条件，多个条件共同变化时按组合解释结果。

仿真 fine-tuning、真机部署和真机数据训练需要分别规划。[dppo-2024](bibliography.md#dppo-2024) v3 §5.4 的 One-leg hardware evaluation 属于 zero-shot 部署，real-data fine-tuning/co-training 需另行规划。本章的任务方案聚焦仿真接口验证；进入真机实验前，还应核对部署观测、latency、执行限制和硬件安全流程，并完成独立安全检查。
