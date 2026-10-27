# 03 从 retargeted motion 到可执行策略

> 本章回答：一段 retargeted 轨迹能当成什么（BC 数据 / tracking reference / reward 与 reset），以及为什么不能直接当 expert action。读完能判断一段人类运动数据走哪条用途、接触可行性是否过关。对应路线：路线 3（residual）与路线 4（人类运动数据）。

Retargeting 输出可作为不同学习接口的 reference 或数据，闭环控制还需要后续 policy 与 controller。[dexcap-2024](bibliography.md#dexcap-2024) 的 IK 与 imitation、[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 的平滑且无 self-collision trajectory、[deepmimic-2018](bibliography.md#deepmimic-2018) 的 motion-conditioned physics policy，分别对应数据采集、轨迹处理和运动跟踪三个环节。

## 链条与数据契约

【机制相关】【推测】建议把链条拆为人类运动与场景观测、robot kinematic reference、接触与动力学校验、学习信号、闭环 policy 五个接口。每段保留坐标系、joint order、时间戳、object pose、contact availability 与真实执行 action；这是面向 [dexcap-2024](bibliography.md#dexcap-2024) 和 [residual-rl-2018](bibliography.md#residual-rl-2018) 的工程综合建议，具体组合需在目标任务上验证。

```text
human motion + object/scene observation
  -> robot kinematic reference
  -> contact / dynamics checks
  -> BC data OR tracking reference OR reward/reset signal
  -> closed-loop policy + controller
```

## 用途一：BC 数据

【机制相关】【推测】BC 把 reference 变成 observation-action supervision，部署策略可以学习任务相关动作，而非逐帧复现原 trajectory。[dexcap-2024](bibliography.md#dexcap-2024) 直接验证 mocap、IK 与 point-cloud imitation 的组合，[dapg-2018](bibliography.md#dapg-2018) 直接验证 demonstrations 对 RL sample complexity 的帮助；二者是否适用于任意离线 retargeting 输出，需按数据质量单独评估。

一种可行做法是同时保存部署可见观测、机器人实际执行动作与优化器输出的 joint target，并分别评估 kinematic reference、经过 controller 后的 executed trajectory、成功与失败 contact segment；[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 可作为 action-generation 模型，retargeting-specific data repair 则需另行验证。

## 用途二：Tracking reference 与 RSI

【机制相关】【推测】tracking 将 motion 作为 policy 的时变目标，允许反馈控制对扰动和动态误差作修正。[deepmimic-2018](bibliography.md#deepmimic-2018) 的 abstract 直接支持 motion imitation objective 与 task objective 的组合；reference phase、未来窗口和 object-relative contact 目标可作为灵巧手适配候选，需单独评估。

Reference State Initialization（RSI）可以把 episode 初始化到 reference 的不同阶段，实施前先确认 contact-consistent reset。这里仅把 RSI 作为 [deepmimic-2018](bibliography.md#deepmimic-2018) 的启发性阅读线索，RSI 公式与采样分布需另查正文；手部应用还需验证关节位置/速度、物体状态与接触模式能一致重建。

tracking 的隔离评估可以同时报告 task success 与 reference error，用于区分轨迹贴合与任务完成。仅降低 joint-space loss 时，还应检查 object motion 与接触是否正确；该评估借鉴 [deepmimic-2018](bibliography.md#deepmimic-2018) 的 imitation/task 目标区分与 [residual-rl-2018](bibliography.md#residual-rl-2018) 的接触建模动机，具体效果由实验结果判定。

## 用途三：Reward 与 reset 信号

【机制相关】【推测】轨迹也可以只提供目标、奖励 shaping 或初始状态课程，动作标签则由其他数据源提供。[demostart-2024](bibliography.md#demostart-2024) 直接验证少量仿真 demonstrations、sparse reward 和 auto-curriculum；具体 reset 采样规则需结合正文与实现另行确定。

将 retargeted motion 用于 reset 时，可以比 BC 增加 object pose、joint velocity 和接触力学的一致性检查，使 reset 分布贴近部署可达状态。比较固定初始状态、reference reset 与自动课程时，保持 policy、reward 和总 interaction budget 相同；该比较以 [demostart-2024](bibliography.md#demostart-2024) 的课程结果为参照，具体 reset 采样规则需在 REGRIND 中另行定义。

## 接触可行性与动力学鸿沟

【机制相关】【推测】运动学匹配只约束几何，摩擦、接触力和执行器约束需通过动力学校验。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 的平滑、无 self-collision 与 [residual-rl-2018](bibliography.md#residual-rl-2018) 的摩擦/接触动机说明应区分这些问题；对某个 retargeted pose，还需要验证 object support、slip、joint limit 和 controller tracking，并用这些结果判断抓握稳定性。

【机制相关】【推测】residual policy 可以补偿 base controller 未建模的部分，其补偿范围应通过 residual authority、饱和率和 reference 可行区域评估。[residual-rl-2018](bibliography.md#residual-rl-2018) 直接验证传统控制与 RL signal superposition 的真机 block assembly；对灵巧手，还应单独检查基线失稳与接触失败原因，再决定是否调整 actor。

面向 REGRIND 的插入点可作为待验证的适配假设：以 REGRIND 项目的 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练为背景，可在 reference 导出后检查运动学和接触一致性，在 controller 前定义固定 residual mapping，在 rollout 中保存 policy 原始随机动作；这些约定需通过源码审查与实验确认，生成式 actor 的具体概率约定见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

## 遥操作与数据管线

【机制相关】视觉 teleoperation 关注在线映射，而 mocap pipeline 还需要离线对齐。[dexpilot-2020](bibliography.md#dexpilot-2020) 给出裸手视觉到完整 hand-arm 控制，[anyteleop-2023](bibliography.md#anyteleop-2023) 扩展跨 arm/hand/camera 配置，[dexcap-2024](bibliography.md#dexcap-2024) 则结合便携追踪、3D observation、IK 与 imitation；它们位于链条的数据来源段，同一份采集记录可以分别用于 BC、tracking 和 reset，具体用途由后续学习接口决定。

【论文直接验证】VR 交互与 haptic feedback 分别出现在两篇系统的采集管线中，它们对下游 policy 的贡献仍需独立测量。[openteach-2024](bibliography.md#openteach-2024) 报告基于 VR 的跨机器人 teleoperation 与 policy learning，[bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 报告双手 collision/singularity avoidance、haptic feedback 与 long-horizon imitation；后续实验应分离 haptic 的单独贡献，并明确各自端到端 action latency 的定义与测量方式。

比较这些数据管线时，可以按动作成功覆盖、接触失配、观测同步和操作者负担计量，展示视频仅作补充。BC、tracking 和 reset 三条分支可以复用原始记录，但应分别保留有效样本筛选规则；其算法候选和隔离评估顺序见 [05](05-ppo-enhancement.md)。
