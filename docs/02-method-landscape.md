# 02 方法全景

五个方法族是可交叉组合的标签，不是先后取代的线性路线。每个标签回答不同问题：sim-RL 决定交互从哪里来，teleoperation 与视频决定数据如何形成，diffusion policy 决定动作分布如何表示，diffusion × RL 决定如何用 reward 改进策略；PPO 工程另在 [05](05-ppo-enhancement.md) 按修改接口组织。

## 大规模 sim-RL 与 sim-to-real

【论文直接验证】仿真 RL 可以产生真机灵巧操作，但验证常与特定观测和 randomization 配置绑定。[openai-inhand-2020](bibliography.md#openai-inhand-2020)、[dextreme-2022](bibliography.md#dextreme-2022) 和 [visual-dexterity-2022](bibliography.md#visual-dexterity-2022) 分别提供 Shadow、Allegro 和复杂形状视觉重定向证据；[massively-parallel-2021](bibliography.md#massively-parallel-2021) 则只直接验证 locomotion 的并行与课程，不是灵巧手结果。

【机制相关】【推测】本族可与 demonstrations、residual control 和 diffusion actor 组合，前提是分开控制感知与动力学误差。Privileged state 可以用于仿真测算法上限，却不等于部署观测；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 明确使用 memory，其他上述 abstract 的 history/recurrence 与延迟未报告，不能假定它们都是完全可观测 MDP。

## 遥操作与数据采集

【论文直接验证】teleoperation 系统把人的意图转为 robot trajectory，而不是自动提供可部署的 autonomous policy。[dexpilot-2020](bibliography.md#dexpilot-2020) 提供裸手视觉控制，[anyteleop-2023](bibliography.md#anyteleop-2023) 提供跨形态配置，[dexcap-2024](bibliography.md#dexcap-2024) 结合 mocap、3D observation 与 imitation；[openteach-2024](bibliography.md#openteach-2024) 和 [bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 补充 VR 与双手采集。

【机制相关】【推测】本族可以给 BC、diffusion pretraining 或 reset curriculum 提供数据，但三者要求的字段不同。BC 需要部署可见 observation 与真实执行 action 的配对，tracking 需要时间对齐 reference，reset 需要可重建物理状态；操作者视觉反馈、系统 action latency 和 robot-side sensor history 在多数所据 abstract 中未报告，不能从视频质量推断数据时序一致性。

## 人类视频与模仿

【论文直接验证】人类视频既可提供 retargeting representation，也可提供高层 task structure。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 从互联网视频学习单 RGB 的 hand-arm imitator，[mimicplay-2023](bibliography.md#mimicplay-2023) 从 human play 学 latent plan 并结合 robot demonstrations；两者都不等于单凭人手 keypoint 获得 robot contact dynamics。

【机制相关】【推测】视频到 retargeted motion 再到 policy 的组合，应把 embodiment mismatch、遮挡与任务阶段歧义分开评估。[dexmimicgen-2024](bibliography.md#dexmimicgen-2024) 提供从少量示范生成更多双手 trajectory 的不同路线；是否能保留 tactile contact、准确 action delay 或 privileged state，在本导读证据中未报告，不能把合成数量当作有效覆盖量。

## Diffusion policy

【论文直接验证】Diffusion Policy 的证据支持条件动作生成与 receding horizon，而不是 online reward optimization。[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 使用视觉条件与 multimodal action distribution，[dp3-2024](bibliography.md#dp3-2024) 改变的是 3D observation representation，[dexdiffuser-2023](bibliography.md#dexdiffuser-2023) 则生成 grasp configuration，三者输出语义不同。

【机制相关】【推测】retargeted demonstrations 可以作为 diffusion imitation 数据，但需保持 robot action 的执行语义和时间尺度一致。Action chunk 带来未来动作的表示，不自动提供过去 observation history 或对延迟的补偿；在上述 abstract 范围内，privileged-state split、history 长度与 latency policy 未报告，接触失败恢复能力【需新证据】。

## Diffusion 与 RL

【论文直接验证】diffusion × RL 内部首先要区分 offline/off-policy 与 on-policy 更新。[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 在 diffusion training loss 中使用 action value，[idql-2023](bibliography.md#idql-2023) 用 critic 权重从 behavior diffusion samples 提取 policy；[dppo-2024](bibliography.md#dppo-2024) v3 §4 把 denoising 过程扩展为 MDP，[genpo-2025](bibliography.md#genpo-2025) v4 §4 则构造 doubled auxiliary action 的可逆分布。

【机制相关】DPPO 与 GenPO 的差别不能简化为“能不能做 on-policy diffusion RL”。DPPO 对逐 denoising-step Gaussian likelihood 做 PPO，GenPO 对 auxiliary action likelihood 做 PPO；两者都不要求直接知道最终执行动作的 marginal density，具体对象与训练数据保存约定见 [04](04-genpo-interface.md#概率对象与-rollout-约定)。

【需新证据】【推测】partial observability 仍需单独验证，不能由 exact likelihood 推导为已解决。[dppo-2024](bibliography.md#dppo-2024) v3 §3、§5 含 state/pixel 条件及 POMDP 说明，[genpo-2025](bibliography.md#genpo-2025) v4 Appendix A 的 state dimension 不等于实际视觉/触觉部署输入；跨方法统一的 privileged split、history 和 delay protocol 未报告。

## 组合关系与取舍

【机制相关】【推测】三条组合路线分别对应不同现有资源。已有 robot demonstrations 时，可用 [diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 接 [dppo-2024](bibliography.md#dppo-2024)；已有仿真任务与奖励但没有示范时，可比较 Gaussian PPO 与 [genpo-2025](bibliography.md#genpo-2025)；已有 retargeted reference 和 base controller 时，可先验证 [residual-rl-2018](bibliography.md#residual-rl-2018) 式集成，再决定是否更换 actor。

【需新证据】【推测】三条路线都需要同样的观测横切审计。视觉、point cloud、tactile 与 proprioception 决定可得信息，privileged critic、history/recurrence 与延迟决定训练部署差异；[rotate-touch-2023](bibliography.md#rotate-touch-2023) 的 touch-only 真机结果说明 tactile 应保留为比较变量，但不证明任意 diffusion/residual 组合已适配。
