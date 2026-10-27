# 03 从 retargeted motion 到可执行策略

> 本章讨论 retargeted motion 的三种训练用途：BC 数据、tracking reference，以及 reward/reset 信号。阅读后可以判断现有记录适合哪种用途，并明确接触与动力学校验需要准备的状态。对应 README 的路线 3、4。

Retargeting 将人类运动转换为机器人参考运动，后续学习接口决定怎样使用这些结果。[dexcap-2024](bibliography.md#dexcap-2024) 将 IK 与 imitation 结合，[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 生成平滑、无 self-collision 的轨迹，[deepmimic-2018](bibliography.md#deepmimic-2018) 则训练以 motion 为条件的 physics-based policy。三篇工作分别提供数据采集、轨迹处理和运动跟踪的参照。

## 链条与数据契约

从人类运动到闭环策略，可以分成运动与场景观测、机器人运动学 reference、接触与动力学校验、学习信号、policy 与 controller 五段。每段应保留坐标系、joint order、时间戳、object pose、接触信息的可用性，以及实际下发的机器人动作。这种接口拆分是结合 [dexcap-2024](bibliography.md#dexcap-2024) 和 [residual-rl-2018](bibliography.md#residual-rl-2018) 提出的工程建议，可以据此检查目标任务的数据是否完整。

```text
human motion + object/scene observation
  -> robot kinematic reference
  -> contact / dynamics checks
  -> BC data OR tracking reference OR reward/reset signal
  -> closed-loop policy + controller
```

动作命令与机器人测得的运动轨迹应分别保存。Joint target、delta target、velocity 或 torque 描述下发给 controller 的动作，测得的 joint/object trajectory 描述执行结果；比较二者可以定位 tracking error 与接触失配。三种学习用途都需要执行检查，reset 还需要在指定时刻一致地重建关节、物体和接触状态。

## 用途一：BC 数据

BC 使用时间对齐的 observation-action pairs 学习策略，action 是监督标签。选用 retargeted 数据时，先确定策略将输出哪种命令，再按相同动作语义保存标签与部署可见观测。训练以任务相关动作为目标，轨迹复现程度按任务需求评估。[dexcap-2024](bibliography.md#dexcap-2024) 报告 mocap、IK 与 point-cloud imitation 的组合，[dapg-2018](bibliography.md#dapg-2018) 报告 demonstrations 对 RL sample complexity 的帮助，为数据到策略的训练路径提供参照。

可以同时保存优化器输出的 joint target（kinematic reference）、controller 实际接收的 command，以及测得的 executed trajectory，分别筛选成功与失败 contact segment。这样既能训练 observation-action supervision，也能检查优化器 target 在执行中产生的偏差。[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 可用于学习这些动作标签的条件分布；采用它之前，先验证 retargeting 数据的同步、可执行性与修复方法。

## 用途二：Tracking reference 与 RSI

Tracking 把 motion 作为随时间变化的目标，让 policy 根据反馈调整动作。[deepmimic-2018](bibliography.md#deepmimic-2018) 报告 motion-imitation objective 与 task objective 的组合。对灵巧手，可以尝试将 reference phase、未来目标窗口和 object-relative contact 目标加入训练，并分别测量这些设计的作用。

Reference State Initialization（RSI）提供了从 reference 不同阶段开始 episode 的思路。[deepmimic-2018](bibliography.md#deepmimic-2018) 可作为进一步阅读入口，具体公式和采样分布需结合正文核查。手部应用首先需要 contact-consistent reset：在同一阶段重建关节位置与速度、物体状态和接触模式，再检查该状态能否继续执行。

Tracking 实验应同时测量轨迹贴合与任务完成。可以固定其余训练条件，报告 task success、reference error、object motion 和接触结果，观察 joint-space loss 的变化是否对应稳定的物体运动。这种评估结合了 [deepmimic-2018](bibliography.md#deepmimic-2018) 的 imitation/task 目标区分和 [residual-rl-2018](bibliography.md#residual-rl-2018) 对接触误差的关注。

## 用途三：Reward 与 reset 信号

轨迹也可以提供任务目标、奖励 shaping、成功信号或初始状态课程，直接作用于 reward 和 reset 接口。[demostart-2024](bibliography.md#demostart-2024) 报告少量仿真 demonstrations、sparse reward 与 auto-curriculum 的组合。采用这类路线时，先写明轨迹向训练提供的是哪种信号：纯 RL 从策略与环境交互中采集动作，联合 BC 时再单独准备监督标签。

Reset 的关键是重建一个物理一致、可以继续演化的状态，使初始化分布贴近部署中可达的状态。可以检查 object pose、joint position/velocity 与接触力学，再比较固定初始状态、reference reset 和自动课程，保持 policy、reward 及总 interaction budget 相同。[demostart-2024](bibliography.md#demostart-2024) 提供课程设计的参照，REGRIND 中的具体采样规则还需定义并通过执行验证。

## 接触可行性与动力学鸿沟

运动学匹配完成后，还需要验证物体支撑、摩擦、接触力和执行器约束。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 关注轨迹平滑与 self-collision，[residual-rl-2018](bibliography.md#residual-rl-2018) 关注接触和摩擦带来的模型误差。对每个候选 reference，可以检查 object support、slip、joint limit 与 controller tracking，再决定它适合 BC、tracking 还是 reset。

Residual policy 在 base controller 输出上学习修正量，以补偿模型与实际接触之间的偏差。[residual-rl-2018](bibliography.md#residual-rl-2018) 在真机 block assembly 中验证传统控制与 RL signal superposition。迁移到灵巧手时，可以结合控制权限（residual authority）、residual 幅度、饱和率、base-only 稳定性与 reference 的可行区域，评估补偿范围并定位控制和接触问题。

REGRIND 可以在 reference 导出、动作合成和 rollout 记录三个位置开展适配实验。以 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练为项目背景，先检查 reference 的运动学和接触一致性，再在 controller 前固定 residual mapping，并保存 policy 原始随机动作。具体实现需经源码审查与实验确认，生成式 actor 的概率和记录要求见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

## 遥操作与数据管线

视觉 teleoperation 在线完成操作者运动到机器人动作的映射，mocap 数据还需在训练前完成对齐。[dexpilot-2020](bibliography.md#dexpilot-2020) 介绍裸手视觉到 hand-arm 控制，[anyteleop-2023](bibliography.md#anyteleop-2023) 扩展到不同 arm、hand 和 camera 配置，[dexcap-2024](bibliography.md#dexcap-2024) 结合便携追踪、3D observation、IK 与 imitation。这些方法提供原始数据，同一份记录可按后续需求用于 BC、tracking 或 reset。

VR 与 haptic feedback 是采集交互的不同组成部分。[openteach-2024](bibliography.md#openteach-2024) 报告基于 VR 的跨机器人 teleoperation 与 policy learning，[bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 报告双手 collision/singularity avoidance、haptic feedback 与 long-horizon imitation。比较采集方案时，可以单独测量 haptic 对下游 policy 的贡献，并明确端到端 action latency 的起止时间与测量方式。

数据管线的比较应同时覆盖数据质量和操作者成本。可以记录成功动作与接触片段的覆盖、接触失配、观测同步误差及操作者负担，并为 BC、tracking 和 reset 分别制定样本筛选规则。展示视频作为这些指标的补充，算法候选与对照实验顺序见 [05](05-ppo-enhancement.md)。
