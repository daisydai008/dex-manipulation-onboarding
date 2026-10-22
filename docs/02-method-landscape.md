# 02 从资源和失败信号选择方法

方法选择应先说明现有资源、失败发生在哪里，以及首个实验能排除什么解释。本章与 [README](../README.md) 负责选方向；[01](01-problem-structure.md) 定义任务边界，[03](03-retargeting-to-policy.md) 检查可执行性，[04](04-onpolicy-diffusion-interface.md) 约束概率接口，[05](05-ppo-enhancement.md) 负责诊断和隔离实验。以下选型均为【机制相关】【需新证据】的建议，不构成方法排名或灵巧手收益承诺。

## 任务契约

【机制相关】首个实验应固定任务契约，而不是只给一个 benchmark 名称。按 [01](01-problem-structure.md#任务谱系) 写明 in-hand、grasp acquisition、arm-hand、双手或 long-horizon 的目标，定义 success、掉落、超时和恢复行为，记录初始接触状态、测试物体与部署初始分布；未明确这些条件时，不比较论文回报数字。

【机制相关】【需新证据】观测与动作契约应横贯所有方法族。分别记录 actor/critic 的 privileged state、视觉、proprioception、tactile、history/recurrence、采样时间与 delay，未知项记“未报告”；动作要明确 target/delta/velocity/torque、control rate、action chunk 与执行 mapping。若部署不可获得训练输入，应先解决感知或接口不一致，不能由 actor 容量更大推断问题消失；证据边界见 [01 观测](01-problem-structure.md#观测与部分可观测性)。

## 资源盘点

【机制相关】资源盘点的产出是可用清单与缺口清单。检查 simulator/reward/reset 是否可复现，成功 robot demonstrations 是否含同步观测和真实动作，reference 是否有可重建的 joint/object state，base controller 是否可独立闭环；数据是否成功不能由 retargeting 几何误差判断，依据与检查项见 [03](03-retargeting-to-policy.md#链条与数据契约)。

【需新证据】训练资源与部署约束应分别记录。列出可用 environment interactions、wall-clock、显存、推理 latency 和允许的控制周期；人类视频只有运动线索、不等于 robot action labels，simulator 吞吐也不等于真机采样能力。先保留这些限制，再选择采集、imitation、RL 或组合路线，不从方法名称补全缺失资源。

## 瓶颈诊断：由可观察信号驱动

【机制相关】【需新证据】update 异常先排查概率与估计接口。若 KL/clip fraction 在更新后突变，检查同一 action 的 old/new log-prob、advantage、normalization 与 done/truncation；这些一致后才分别改变 LR、epoch 或 clip，不能先归因于探索不够。[implementation-matters-2020](bibliography.md#implementation-matters-2020) 支持实现归因的重要性，具体排查顺序是 [05 selector](05-ppo-enhancement.md#从失败信号选择接口) 的候选设计。

【机制相关】【需新证据】几何贴合但物体滑落，优先定位接触与控制问题。按 phase 记录 reference error、object motion、接触失败、base-only 成功与 residual 饱和，检查 reference/base/feasible reset，而不是立即替换 actor；若早期失败导致后续 phase 几乎无采样，再单独评估 phase resets/curriculum，并始终用固定部署初始状态报告 end-to-end success，见 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

【需新证据】动作表示不足只能在数据与更新口径一致后提出。观察相同条件下的成功动作是否存在多种模式、imitation 的闭环恢复是否失败，以及 Gaussian baseline 的问题是否仍存在；多模态数据本身不能证明 diffusion 会提高 task success。若主要耗时在 simulator 而非 actor/update，先测吞吐分段而不是换生成模型；实验拆分见 [05](05-ppo-enhancement.md)。

## 候选选择：五个方法族

五族是可组合的标签，不是从低级到高级的阶段。每张短卡按同一字段约束选择，论文证据与拟议收益分开；涉及目标灵巧任务的收益均【需新证据】。

### 仿真 RL 与 sim-to-real 工程

- 解决的瓶颈：【机制相关】已有任务和奖励，但缺少闭环接触策略或部署分布覆盖。
- 前置条件：可复现 simulator、reward/reset、Gaussian PPO baseline 与明确的训练/部署观测差异。
- 收益预期：【需新证据】建立从交互学习的控制基线，测试扰动下的 task success，不预设 sample efficiency。
- 代价：接触仿真、奖励定义、randomization 校准、交互预算与部署验证。
- 证据范围：[openai-inhand-2020](bibliography.md#openai-inhand-2020)、[dextreme-2022](bibliography.md#dextreme-2022) 的 abstract 支持各自系统的 sim-to-real；[massively-parallel-2021](bibliography.md#massively-parallel-2021) 的并行证据来自 locomotion，不能直接转为手部加速比。
- 不适用情形：reset 物理不可行、部署观测不可得，或仍未定义成功指标；这些问题不是扩大训练规模能确认解决的。
- 最小对照：【机制相关】【需新证据】先固定任务测 Gaussian PPO；只改变一个 randomization family 或并行规模，分别按 interactions 与 wall-clock 报告结果。

### 遥操作与数据采集

- 解决的瓶颈：【机制相关】缺少成功 robot demonstrations，或已有运动记录没有同步、可执行 action。
- 前置条件：机器人动作接口、传感同步、操作者控制与安全流程；能区分 reference target 和 executed action。
- 收益预期：【需新证据】获得可筛选的成功接触片段和闭环 imitation 数据，不把数据量当作 policy 收益。
- 代价：采集设备、标定、操作者时间、失败标注与 embodiment 对齐。
- 证据范围：[dexpilot-2020](bibliography.md#dexpilot-2020)、[anyteleop-2023](bibliography.md#anyteleop-2023)、[dexcap-2024](bibliography.md#dexcap-2024) 的 abstract 覆盖各自映射与数据管线，不提供统一成功率排名。
- 不适用情形：已有覆盖充分且动作一致的数据，当前失败主要来自 reward、update 或不可行 reset；应先诊断现有数据为何不能闭环。
- 最小对照：【机制相关】【需新证据】固定任务和 imitation 模型，只比较数据筛选/采集方案，报告成功片段覆盖、同步误差与闭环 task success；可执行性检查见 [03](03-retargeting-to-policy.md#遥操作与数据管线)。

### 人类视频与模仿

- 解决的瓶颈：【机制相关】有可利用的人类运动或任务结构，但缺少同 embodiment 的动作监督。
- 前置条件：可获取的场景/运动线索、跨 embodiment 对齐，以及后续 robot 执行验证；有 robot demonstrations 时应另行记录其使用量。
- 收益预期：【需新证据】提供 reference 或高层任务引导，而不是把人类视频直接等同 expert robot action。
- 代价：姿态/物体估计、时间对齐、遮挡处理及接触可行性校验。
- 证据范围：[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 的 abstract 支持机器人手 imitation，[mimicplay-2023](bibliography.md#mimicplay-2023) 支持 human play 与少量 robot demonstrations 的组合；两者不证明任意 retargeted trajectory 都能用于 BC。
- 不适用情形：任务需要精确接触动作而记录无法恢复物体/接触状态，或无法验证生成 reference 的动力学可行性。
- 最小对照：【机制相关】【需新证据】固定 robot 数据与下游模型，比较有/无视频引导；分别记录 reference 可行率与闭环成功率，避免把几何匹配当作控制完成。

### Diffusion policy

- 解决的瓶颈：【机制相关】成功 demonstrations 中有条件多模态动作，现有 imitation 表示或 action horizon 可能不足。
- 前置条件：成功 robot observation-action 数据、明确的 prediction/execution horizon、可部署输入与 latency 预算。
- 收益预期：【需新证据】比较 conditional generation 是否改善闭环成功与恢复；不由表达能力直接推出 on-policy RL 收益。
- 代价：denoising 推理、数据覆盖、chunk/controller 对齐，以及训练与部署观测一致性检查。
- 证据范围：[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 的 abstract 支持 visuomotor imitation，[dp3-2024](bibliography.md#dp3-2024) 支持 3D representation；它们不是 auxiliary density 或灵巧手 online fine-tuning 的证据。
- 不适用情形：没有有效动作监督、reference 还不能执行，或控制周期不支持候选 sampler 的实测 latency。
- 最小对照：【机制相关】【需新证据】相同数据、observation、action horizon 与测试 reset 下比较 Gaussian imitation 与 diffusion imitation，先完成闭环再决定是否加 reward fine-tuning。

### Diffusion 与 RL

- 解决的瓶颈：【机制相关】imitation 已能闭环但 task reward 尚有改进需求，或一致条件下 Gaussian actor 的表示限制仍有可观察证据。
- 前置条件：可交互环境、可归因的 baseline、明确的 probability object 与 rollout schema；offline 与 on-policy 资源不能混用。
- 收益预期：【需新证据】检验 actor 与相应更新方案是否改善目标任务，不预设接触探索或稳定性优势。
- 代价：sampling、likelihood、denoising trajectory/auxiliary action 存储、update compute 与数据来源控制。
- 证据范围：[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 与 [idql-2023](bibliography.md#idql-2023) 的 abstract 支持 offline 路线；[dppo-2024](bibliography.md#dppo-2024) v3 §4–5 支持 denoising-step PPO 与 fine-tuning，不能替未指定 sampler 证明可逆性或 exact density。
- 不适用情形：old log-prob 无法在原采样变量上重算、数据版本失配，或观测/reference/reset 问题尚未排除。
- 最小对照：【机制相关】【需新证据】先固定任务、数据与 Gaussian baseline，再替换 actor 和必要的记录/更新接口；若同时改变 actor、update schema、pretraining，只能归因于组合，不能单独归因于 actor，见 [04](04-onpolicy-diffusion-interface.md)。

## 三条起步路线

【机制相关】【需新证据】有 simulator、无示范时，先建立 Gaussian PPO baseline。固定 reward/reset/observation/action semantics，输出学习曲线、成功/掉落、KL/clip fraction 与分段耗时；只有 baseline 接口一致且仍有具体失败假设时才选择五族中的下一项，不把 diffusion 作为默认起点，依据 [ppo-2017](bibliography.md#ppo-2017) 与 [05](05-ppo-enhancement.md#固定-ppo-更新与估计口径)。

【机制相关】【需新证据】有成功 robot demonstrations 时，先验证 imitation 闭环，再决定 reward fine-tuning。先统一数据与部署动作、评估固定 reset 的 success 和偏离示范后的恢复；若 imitation 已满足任务，不因存在 RL 方法而追加复杂度。需要 fine-tuning 时再按 [dppo-2024](bibliography.md#dppo-2024) 的证据边界评估，不把其结果外推为灵巧手保证。

【机制相关】【需新证据】有 reference/base controller 时，先验证物理可行性与 base-only，再测 Gaussian residual，最后考虑换 actor。按 [03](03-retargeting-to-policy.md) 区分 BC、tracking 与 reset 用途，固定 controller/reference 的版本与 residual scale；若 base-only 已失稳或 reference 不可行，先修复这些接口，而不是用更复杂 actor 掩盖原因。该顺序借鉴 [residual-rl-2018](bibliography.md#residual-rl-2018) 的控制分工，目标任务收益尚待验证。

## 首个实验与停止条件

【需新证据】首个实验只回答一个可证伪的问题。写明失败信号、候选解释、唯一改动接口、共同数据/环境配置、seed 列表、interactions 与 wall-clock 上限、部署 latency 限制及事先定义的成功判据；输出 baseline 与对照的 per-seed 结果、失败类型和预算消耗，不用单次最高 return 选方法。具体记录与任务用途见 [04](04-onpolicy-diffusion-interface.md#按诊断目的的任务验证) 和 [05](05-ppo-enhancement.md#评估顺序与停止条件)。

【机制相关】【需新证据】停止条件应区分接口错误与实验负结果。遇到 log-prob 不一致、不可行 reset、部署输入不可得或 latency 超预算，停止追加训练并修复接口；若预算耗尽且预定义 task metric 未改善，保留负结果，不追加其他模块后声称原假设成立。若只改善训练 reward 而不改善固定测试分布的 success，应重查 reward 与任务目标的对应关系。
