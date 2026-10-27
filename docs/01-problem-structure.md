# 01 问题结构

> 本章回答：灵巧操作该按什么维度拆开比较，以及为什么需要同时记录任务、观测与执行接口。读完能判断一个任务属于哪个谱系、需要记录哪些观测与硬件条件，以及所用 benchmark 能否与文献横向比较。对应路线：所有路线的任务与观测前提。

Dexterous manipulation 需要先按任务、观测与执行接口分解，比较时同时列出这些条件。本导读用 [注释书目](bibliography.md) 中已限定来源的证据说明差异；需要另查正文或实验的配置列入后续核查。

## 任务谱系

In-hand reorientation 关注已建立接触后的物体姿态控制，抓取获取则另行计量。三篇工作的初始接触条件具体不同：[openai-inhand-2020](bibliography.md#openai-inhand-2020) 在 Appendix C.1 中先把物体以随机朝向放在掌心，再执行 100 步随机动作，并丢弃期间掉落的 trial；[dextreme-2022](bibliography.md#dextreme-2022) §2.1 从掌心物体开始并采样 SO(3) 目标，官方 `reset_idx` 在默认 `apply_random_quat=True` 时为物体采样随机四元数，并对物体位置与默认手型加噪、清零物体速度；[visual-dexterity-2022](bibliography.md#visual-dexterity-2022) Summary 采用手指范围内的随机 SE(3) 初始配置，物体由桌面放置或人手递交，hand 采用 downward-facing，并分别测试有支撑桌面与无支撑桌面的设置。比较结果时应按这些初始条件分组，分别报告连续重定向次数与适用设置。

Grasp acquisition 与后续 manipulation 应分别计量。[dexdiffuser-2023](bibliography.md#dexdiffuser-2023) 从 partial point cloud 生成、评估和 refine grasps，其验证对象是单次 grasp success。Regrasp 则是闭环恢复过程：物体滑落后，系统重新建立稳定接触并继续原任务。[visual-dexterity-2022](bibliography.md#visual-dexterity-2022) 在带桌面支撑的设置中报告了这种现象：物体掉落后，控制器会再次拾起并继续重定向。评估 regrasp 时，可分别记录掉落检测、重新抓取成功率、恢复后任务完成率和恢复耗时，与单次 grasp generation success 分开统计。

Arm-hand 协同需要同时处理到达、姿态和手部接触，动作与观测设计应覆盖 arm 和 hand 的联合状态。[dexpilot-2020](bibliography.md#dexpilot-2020) 与 [anyteleop-2023](bibliography.md#anyteleop-2023) 的证据属于 teleoperation，[demostart-2024](bibliography.md#demostart-2024) 则包含三指手臂-手的 learned policy；它们的相机、动作接口和示范使用方式不同。

双手协同既包含控制耦合，也包含任务角色分配。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 对 single-agent 与 multi-agent 设置作比较，[bunny-visionpro-2024](bibliography.md#bunny-visionpro-2024) 和 [dexmimicgen-2024](bibliography.md#dexmimicgen-2024) 则处理数据采集与合成；【机制相关】【推测】是否拆成多个 agent 应由 observation/action partition 决定，双手的物理形态仅作为任务背景。

Long-horizon 组合的困难包括子任务之间的可达性和失败恢复。[sequential-dexterity-2023](bibliography.md#sequential-dexterity-2023) 以 transition feasibility 和 policy switching 处理衔接；[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 报告复杂序列的真机迁移；评估时应分别报告子任务成功率、切换可行性与长序列完成率。

## 观测与部分可观测性

Observation modality 应作为所有方法族的横切变量单独记录。视觉、proprioception、tactile、privileged simulator state 应分别记录 actor 与 critic 的输入；若 actor 在训练时可直接访问部署阶段无法获得的物体状态，一种可行做法是补充 state estimator，或开展训练/部署观测一致性实验，再用结果判断感知与 actor 参数化各自的影响。

已核验的视觉证据有明确范围。[dextreme-2022](bibliography.md#dextreme-2022) 比较 vision policy 与 privileged motion-capture state，[visual-dexterity-2022](bibliography.md#visual-dexterity-2022) 使用单 depth camera，[demostart-2024](bibliography.md#demostart-2024) 使用多相机 raw pixels 和 proprioception；后续核查应分别记录它们的 actor/critic privileged split、history 长度与端到端延迟。

Tactile 可补充视觉难以推断的接触信号，完整可观测性还需结合 history、recurrence 与测量延迟评估。[rotate-touch-2023](bibliography.md#rotate-touch-2023) 的证据是 binary touch-only in-hand rotation 及新物体真机部署；后续评估应单独记录 history、recurrence 与测量延迟，传感器硬件选型则结合具体设备核查。

History、recurrence 与延迟应独立于 modality 报告。[openai-rubiks-2019](bibliography.md#openai-rubiks-2019) 的 abstract 明确提到 memory-augmented model，后续核查应确定其历史窗口长度。State-space 维度描述模型输入，deployable sensor specification 需另列硬件与采样配置；diffusion timestep embedding 描述去噪迭代，observation history 需单独定义。

比较 partial observability 时，可以固定观测权限、采样时间和失效注入协议，分别评估 privileged state、可部署感知、加入 history/recurrence、加入 observation/action delay 四种变化，并报告 state-estimation error、控制成功率和失败类型；这些结果用于判断各因素的实际影响。

## 硬件与 benchmark 可比性

比较 Shadow Hand、Allegro 与 LEAP 时，应分别记录 joint limits、actuation、触觉配置、控制频率和动作归一化，再判断结果是否可比。[openai-inhand-2020](bibliography.md#openai-inhand-2020) 给出物理 Shadow Hand，[dextreme-2022](bibliography.md#dextreme-2022) 给出 Allegro 与 Isaac Gym，[leap-hand-2023](bibliography.md#leap-hand-2023) 给出低成本硬件及多类真机任务。

本导读仅把 Adroit 作为 demonstration-augmented dexterous RL 的检索入口，具体 task protocol 需另查正文。[dapg-2018](bibliography.md#dapg-2018) 的 abstract 直接支持 24-DoF hand、仿真从零学习和 demonstrations 降低样本复杂度；【推测】将其对应到 Adroit 任务族属于索引背景，具体 task name、初始化与动作语义也需逐项核对。

Bi-DexHands 的结果应区分单任务与 multi-task 设置。[bi-dexhands-2023](bibliography.md#bi-dexhands-2023) 的 abstract 明确区分单任务成功与多数 multi-task/few-shot 设置失败，并报告 single-/multi-agent 设置；后续比较应逐项记录动作语义、初始握持状态与 sim-to-real 设置。

比较 IsaacLab 任务时应固定版本与 registry ID，名字相近的任务需逐项核对配置。[isaac-lab-2023](bibliography.md#isaac-lab-2023) 的原文题名是 Orbit，固定版本的 registry ID 与任务用途见 [04](04-onpolicy-diffusion-interface.md#按诊断目的的任务验证)，当前环境配置以所选版本的官方文档为准。

跨论文比较前，可以逐项填写 hand-only/arm-hand、动作语义、初始状态、物体泛化与 sim/real 五类条件：动作是 position target、delta target、velocity 还是 torque；物体是否已在手中；测试是新初姿、新实例还是新形状；指标是在仿真、zero-shot 真机还是在线真机训练取得。信息缺失的字段列入后续核查，并按论文或实测结果补全。

下一步应先选择数据与策略的组合路径，再选择 actor 参数化；对应 [02 方法选择](02-method-landscape.md) 与 [03 retargeting 到 policy](03-retargeting-to-policy.md)。
