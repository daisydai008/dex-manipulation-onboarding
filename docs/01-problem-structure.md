# 01 问题结构

> 本章回答：灵巧操作该按什么维度拆开比较，为什么不能只看手的自由度或算法名。读完能判断一个任务属于哪个谱系、观测是否部分可观测、所用硬件/benchmark 能否与文献横向比较。对应路线：所有路线的任务与观测前提。

Dexterous manipulation 需要先按任务、观测与执行接口分解，不能只按手的自由度或算法名称比较。本导读用 [注释书目](bibliography.md) 中已限定来源的证据说明差异；未由所据 abstract 或指定全文给出的配置记为“未报告”。

## 任务谱系

In-hand reorientation 关注已建立接触后的物体姿态控制，并不自动包含从桌面拿起物体的能力。[openai-inhand-2020](bibliography.md#openai-inhand-2020)、[dextreme-2022](bibliography.md#dextreme-2022) 与 [visual-dexterity-2022](bibliography.md#visual-dexterity-2022) 覆盖仿真训练到真机重定向；它们支持讨论 finger gaiting、物体观测与形状泛化，但各自初始接触分布在 abstract 中未报告，不能默认相同。

Grasp acquisition 与后续 manipulation 应分别计量。[dexdiffuser-2023](bibliography.md#dexdiffuser-2023) 从 partial point cloud 生成、评估和 refine grasps，其验证对象是 grasp success；【机制相关】【推测】regrasp 可以作为重定向失败后的恢复过程，但 grasp generation 的证据不能推出该过程可连续完成；状态切换与恢复成功率【需新证据】。

Arm-hand 协同需要同时处理到达、姿态和手部接触，而不是只把 hand-only policy 的维度加宽。[dexpilot-2020](bibliography.md#dexpilot-2020) 与 [anyteleop-2023](bibliography.md#anyteleop-2023) 的证据属于 teleoperation，[demostart-2024](bibliography.md#demostart-2024) 则包含三指手臂-手的 learned policy；它们的相机、动作接口和示范使用方式不同。

双手协同既包含控制耦合，也包含任务角色分配。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 对 single-agent 与 multi-agent 设置作比较，[bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 和 [dexmimicgen-2024](bibliography.md#dexmimicgen-2024) 则处理数据采集与合成；【机制相关】【推测】是否拆成多个 agent 应由 observation/action partition 决定，不由“两只手”这个名称决定。

Long-horizon 组合的困难包括子任务之间的可达性和失败恢复。[sequential-dexterity-2023](bibliography.md#sequential-dexterity-2023) 以 transition feasibility 和 policy switching 处理衔接；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 报告复杂序列的真机迁移；两者不能被压缩成一次短时重定向的 success rate。

## 观测与部分可观测性

Observation modality 是所有方法族的横切变量，不是算法附注。视觉、proprioception、tactile、privileged simulator state 应分别记录 actor 与 critic 能看到什么；【需新证据】【推测】若训练 actor 可直接访问真实部署不可得的物体状态，就必须补充 state estimator 或训练/部署观测一致性实验，不能用更强 actor 参数化代替感知验证。

已核验的视觉证据有明确范围。[dextreme-2022](bibliography.md#dextreme-2022) 比较 vision policy 与 privileged motion-capture state，[visual-dexterity-2022](bibliography.md#visual-dexterity-2022) 使用单 depth camera，[demostart-2024](bibliography.md#demostart-2024) 使用多相机 raw pixels 和 proprioception；abstract 未报告它们完整的 actor/critic privileged split、history 长度或端到端延迟。

Tactile 能提供视觉不能直接推断的接触信号，但不能从传感器存在推导出完整可观测性。[rotate-touch-2023](bibliography.md#rotate-touch-2023) 的证据是 binary touch-only in-hand rotation 及新物体真机部署；传感器硬件综述不在本仓库范围，history、recurrence 与测量延迟在本条证据中未报告。

History、recurrence 与延迟应独立于 modality 报告。[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 的 abstract 明确提到 memory-augmented model，但不报告本导读所需的历史窗口长度。State-space 维度不等于可部署 sensor specification，diffusion timestep embedding 也不等于 observation history。

【需新证据】【推测】比较 partial observability 时应固定观测权限、采样时间和失效注入协议。建议分别评估 privileged state、可部署感知、加入 history/recurrence、加入 observation/action delay 四种变化，并报告 state-estimation error、控制成功率和失败类型；它们是未来评估设计，不是任何入选论文已经共同完成的协议。

## 硬件与 benchmark 可比性

Shadow Hand、Allegro 与 LEAP 不是同一控制问题的可交换设备。[openai-inhand-2020](bibliography.md#openai-inhand-2020) 给出物理 Shadow Hand，[dextreme-2022](bibliography.md#dextreme-2022) 给出 Allegro 与 Isaac Gym，[leap-hand-2023](bibliography.md#leap-hand-2023) 给出低成本硬件及多类真机任务；joint limits、actuation、触觉配置、控制频率和动作归一化在这些 abstract 中不足以形成统一排名。

Adroit 在本导读中是 demonstration-augmented dexterous RL 的检索入口，而不是已经完整核验的 task protocol。[dapg-2018](bibliography.md#dapg-2018) 的 abstract 直接支持 24-DoF hand、仿真从零学习和 demonstrations 降低样本复杂度；【推测】将其对应到 Adroit 任务族属于索引背景，具体 task name、初始化与动作语义需另查正文，本导读不把它们写成已核验事实。

Bi-DexHands 的大规模 simulation 证据不等于多任务已经解决。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 的 abstract 明确区分单任务成功与多数 multi-task/few-shot 设置失败，并报告 single-/multi-agent 设置；每项任务的动作语义、初始握持状态和 sim-to-real 在该证据中未报告。

IsaacLab 任务族提供可复用仿真接口，但名字相近不保证 benchmark 一致。[isaac-lab-2023](bibliography.md#isaac-lab-2023) 的原文题名是 Orbit，不能凭稳定 ID 推断所有当前 IsaacLab API；固定版本的 registry ID 与任务用途见 [04](04-onpolicy-diffusion-interface.md#按诊断目的的任务验证)，不从论文题名推断当前环境配置。

【需新证据】【推测】跨论文比较前应逐项填写 hand-only/arm-hand、动作语义、初始状态、物体泛化与 sim/real 五类条件。动作是 position target、delta target、velocity 还是 torque；物体是否已在手中；测试是新初姿、新实例还是新形状；指标是在仿真、zero-shot 真机还是在线真机训练取得，任何一项未报告都应保留空缺而非按常见配置补全。

下一步应先选择数据与策略的组合路径，再选择 actor 参数化；对应 [02 方法选择](02-method-landscape.md) 与 [03 retargeting 到 policy](03-retargeting-to-policy.md)。
