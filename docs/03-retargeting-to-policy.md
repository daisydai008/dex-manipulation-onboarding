# 03 从 retargeted motion 到可执行策略

> 本章回答：一段 retargeted 轨迹能当成什么（BC 数据 / tracking reference / reward 与 reset），以及为什么不能直接当 expert action。读完能判断你的人类运动数据走哪条用途、接触可行性是否过关。对应路线：路线 3（residual）与路线 4（人类运动数据）。

Retargeting 输出不是最终闭环控制器，而是可能用于不同学习接口的 reference 或数据。[dexcap-2024](bibliography.md#dexcap-2024) 的 IK 与 imitation、[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 的平滑且无 self-collision trajectory、[deepmimic-2018](bibliography.md#deepmimic-2018) 的 motion-conditioned physics policy，分别覆盖链条的不同部分。

## 链条与数据契约

【机制相关】【推测】建议把链条拆为人类运动与场景观测、robot kinematic reference、接触与动力学校验、学习信号、闭环 policy 五个接口。每段保留坐标系、joint order、时间戳、object pose、contact availability 与真实执行 action；这是面向 [dexcap-2024](bibliography.md#dexcap-2024) 和 [residual-rl-2018](bibliography.md#residual-rl-2018) 的工程综合建议，不是它们共同验证过的标准。

```text
human motion + object/scene observation
  -> robot kinematic reference
  -> contact / dynamics checks
  -> BC data OR tracking reference OR reward/reset signal
  -> closed-loop policy + controller
```

## 用途一：BC 数据

【机制相关】【推测】BC 把 reference 变成 observation-action supervision，而不强制部署策略逐帧复现原 trajectory。[dexcap-2024](bibliography.md#dexcap-2024) 直接验证 mocap、IK 与 point-cloud imitation 的组合，[dapg-2018](bibliography.md#dapg-2018) 直接验证 demonstrations 对 RL sample complexity 的帮助；二者不共同证明任意离线 retargeting 输出都可作为 expert action。

【需新证据】【推测】BC 数据应优先保存部署可见观测与机器人实际执行动作，而非只保存优化器输出 joint target。应分别评估 kinematic reference、经过 controller 后的 executed trajectory、成功与失败 contact segment；[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 可作为 action-generation 模型，但其 abstract 不提供 retargeting-specific data repair 证据。

## 用途二：Tracking reference 与 RSI

【机制相关】【推测】tracking 将 motion 作为 policy 的时变目标，允许反馈控制对扰动和动态误差作修正。[deepmimic-2018](bibliography.md#deepmimic-2018) 的 abstract 直接支持 motion imitation objective 与 task objective 的组合；reference phase、未来窗口和 object-relative contact 目标是灵巧手适配候选，不是该 abstract 已验证的设计。

【需新证据】【推测】Reference State Initialization（RSI）可以把 episode 初始化到 reference 的不同阶段，但 contact-consistent reset 是必要前提。将 RSI 作为 [deepmimic-2018](bibliography.md#deepmimic-2018) 的启发性阅读线索不等于此导读核验过其正文算法；本任务的 abstract 证据不包含 RSI 公式或采样分布，手部应用需另证关节位置/速度、物体状态与接触模式能一致重建。

【需新证据】【推测】tracking 的隔离评估应同时报告 task success 与 reference error，避免“更像示范但更容易掉落”。仅降低 joint-space loss 不能保证 object motion 或接触正确；该推断依据 [deepmimic-2018](bibliography.md#deepmimic-2018) 的 imitation/task 目标区分与 [residual-rl-2018](bibliography.md#residual-rl-2018) 的接触建模动机，不宣称已有灵巧手实验结论。

## 用途三：Reward 与 reset 信号

【机制相关】【推测】轨迹也可以只提供目标、奖励 shaping 或初始状态课程，而不提供 actor 的动作标签。[demostart-2024](bibliography.md#demostart-2024) 直接验证少量仿真 demonstrations、sparse reward 和 auto-curriculum；具体如何从轨迹采样 reset，在本导读的 abstract 证据中未报告。

【需新证据】【推测】将 retargeted motion 用于 reset 比用于 BC 需要不同的可信度检查。可重建的中间状态可以帮助探索，但若 object pose、joint velocity 或接触力学不相容，reset 分布会制造部署时不可能出现的状态；比较固定初始状态、reference reset 与自动课程时，应保持 policy、reward 和总 interaction budget 相同；依据 [demostart-2024](bibliography.md#demostart-2024) 仅提出候选，不复述未核验的实现细节。

## 接触可行性与动力学鸿沟

【机制相关】【推测】运动学匹配只约束几何，不足以保证摩擦、接触力和执行器约束可满足。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 的平滑、无 self-collision 与 [residual-rl-2018](bibliography.md#residual-rl-2018) 的摩擦/接触动机说明应区分这些问题；对某个 retargeted pose，还需要验证 object support、slip、joint limit 和 controller tracking，不能从手型相似推断抓稳。

【机制相关】【推测】residual policy 可以补偿 base controller 未建模的部分，但无法保证任意 reference 都可救回。[residual-rl-2018](bibliography.md#residual-rl-2018) 直接验证传统控制与 RL signal superposition 的真机 block assembly；对灵巧手，应单独检查 residual authority、饱和率、基线失稳和 reference 可行区域，不能把所有失败归为探索不足。

【需新证据】【推测】面向 REGRIND 的插入点是适配假设，不是代码审计结果。以 REGRIND 项目的 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练为背景，可在 reference 导出后检查运动学和接触一致性，在 controller 前定义固定 residual mapping，在 rollout 中保存 policy 原始随机动作；这些约定未通过读取 REGRIND 源码或实验验证，生成式 actor 的具体概率约定见 [04](04-onpolicy-diffusion-interface.md#固定执行-mapping)。

## 遥操作与数据管线

【机制相关】视觉 teleoperation 关注在线映射，而 mocap pipeline 还需要离线对齐。[dexpilot-2020](bibliography.md#dexpilot-2020) 给出裸手视觉到完整 hand-arm 控制，[anyteleop-2023](bibliography.md#anyteleop-2023) 扩展跨 arm/hand/camera 配置，[dexcap-2024](bibliography.md#dexcap-2024) 则结合便携追踪、3D observation、IK 与 imitation；它们属于数据来源，不是三种轨迹用途中的唯一一种。

【论文直接验证】VR 交互与 haptic feedback 分别出现在两篇系统的采集管线中，但下游 policy 仍须独立测量。[openteach-2024](bibliography.md#openteach-2024) 报告基于 VR 的跨机器人 teleoperation 与 policy learning，[bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 报告双手 collision/singularity avoidance、haptic feedback 与 long-horizon imitation；haptic 的单独贡献未分离，abstract 对各自端到端 action latency 的完整定义也未报告。

【需新证据】【推测】比较这些数据管线时，应按动作成功覆盖、接触失配、观测同步和操作者负担计量，而不是按展示视频数量。BC、tracking 和 reset 三条分支可以复用原始记录，但应分别保留有效样本筛选规则；其算法候选和隔离评估顺序见 [05](05-ppo-enhancement.md)。
