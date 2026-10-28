# 04 On-policy diffusion 的执行与任务接口

> 本章回答两个实现问题：policy 输出的采样变量怎样变成机器人 command，以及用哪些任务检查这个接口是否正确。概率定义与推导见 [附录](appendix-probability.md)。

On-policy diffusion 的实现除了 actor 本身，还需要固定执行命令的生成方式和任务评估条件。下面先说明执行 mapping，再给出三个任务的配置与比较设置。

## 固定执行 mapping

Policy 输出的 `ξ` 还不是机器人最终执行的 command。中间还有一层执行 mapping：它根据当前状态 `s` 和采样变量 `ξ`，计算下发给机器人的 `u`。可以把这层规则理解为“策略输出到执行器之间的转换”。

```text
状态 s
  → 组成本次决策的 conditioning c=h(s)
  → policy 按 qθ(ξ|c) 采样 ξ
  → 执行 mapping 计算 u=g(s,ξ)
  → 机器人执行 u
  → 环境进入下一状态 s′
```

以 residual control 为例，转换规则可以写成 `u=clip(b(s)+αξ)`。其中 `b(s)` 是 base controller 的输出，`α` 是 residual scale，`ξ` 是 policy 学出的修正量，clipping 限制最终 command 的幅度。PPO 关心的是 `ξ` 在新旧策略下的概率，因此只要 `g` 及相关 controller 状态转移在数据收集与相关更新期间不依赖待更新参数 `θ`，就可以把 `g` 当作环境的一部分，在 auxiliary action 空间中做 PPO。`qθ(ξ|c)` 是辅助动作的密度，执行动作 `u` 的密度则需要由 `g` 与 `qθ` 的 composition 另行确定；PPO 仍使用其原有的近似目标，这一构造不提供额外保证。

这也是为什么必须保存原始 `ξ`。执行后的 `u` 可能经过缩放和 clipping，多个不同的 `ξ` 可能得到同一个 `u`，所以仅保存 `u` 不足以确定 `ξ`。正确做法是分别保存：用于概率计算的原始 `ξ` 与 old log-prob，以及用于执行核对的 `u`。

执行规则一旦改变，环境也可能随之改变。更换 base controller、reference、residual scale、normalization 或 clipping 规则后，`u`、conditioning `c` 或环境转移都可能变化。当实际环境或 conditioning 定义发生变化时，旧 rollout 需要按新定义重新采集，old log-prob 只用于比较策略概率。

如果 controller 或 filter 还有内部状态 `m_t`，它也应作为环境状态的一部分：记录 `(s_t,m_t)` 的转移和 reset；policy 若使用该状态，还要把它放进 conditioning 或保存重建信息。这样才能说明当前动作如何影响后续状态。

对 REGRIND，实施顺序是：先固定 base/reference、residual scale 和 clipping 规则，再保存原始 `ξ` 与执行 command，最后比较不同 actor。每次修改这些规则后重新建立 baseline；controller 与 actor 共同学习则需要另行建立推导。

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
