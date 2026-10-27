# 02 从资源和失败信号选择方法

> 本章讨论怎样根据现有资源和训练中的失败现象选择方法。阅读后可以确定先做数据采集、imitation、RL 还是组合实验，并写出首个对照方案。对应 README 的四条研究路线。

方法选择从任务、资源和具体问题开始。本章与 [README](../README.md) 提供选型思路；[01](01-problem-structure.md) 介绍任务设置，[03](03-retargeting-to-policy.md) 讨论运动数据的用途与可执行性，[04](04-onpolicy-diffusion-interface.md) 定义概率与执行接口，[05](05-ppo-enhancement.md) 展开训练诊断。下文先整理已有论文的做法，再提出目标灵巧手任务中的实验建议。

## 任务契约

首个实验需要一份可复现的任务定义。按 [01](01-problem-structure.md#任务谱系) 说明研究对象属于 in-hand、grasp acquisition、arm-hand、双手还是 long-horizon，写明 success、掉落、超时和恢复行为的判据，同时记录初始接触、测试物体与部署初始分布。这些条件共同决定回报数字与成功率的含义，也是跨论文比较的依据。

观测与动作的定义需要贯穿训练和部署。分别列出 actor、critic 使用的 privileged state、视觉、proprioception、tactile、history/recurrence，以及采样时间和 delay；动作则写明 target/delta/velocity/torque、control rate、action chunk 和执行 mapping。待核查项单独列出；涉及训练专有输入时，先确定部署侧的感知来源并验证接口，再评估 actor 容量的影响；相关实例与核查项见 [01 观测](01-problem-structure.md#观测与部分可观测性)。

## 资源盘点

资源盘点应明确哪些条件已经可用，哪些条件还需要准备。确认 simulator、reward 和 reset 可以复现；检查成功 robot demonstrations 是否包含同步观测和动作；判断 reference 能否重建 joint/object state，以及 base controller 能否独立闭环。Retargeting 数据的有效性应通过执行结果确认，几何误差与接触成功分别记录，检查方法见 [03](03-retargeting-to-policy.md#链条与数据契约)。

训练预算与部署约束需要分别测量。训练侧记录可用 environment interactions、wall-clock 和显存，部署侧记录推理 latency 与允许的控制周期。人类视频可以提供运动线索，robot action labels 还需要经过形态映射和执行记录对齐；真机采样能力则取决于实际采集周期和延迟。把这些资源列清楚后，再选择采集、imitation、RL 或组合路线。

## 瓶颈诊断：由可观察信号驱动

更新后 KL 或 clip fraction 突变时，先检查概率与估计记录。核对同一 action 的 old/new log-prob、advantage、normalization 和 done/truncation 处理，再分别调整 LR、epoch 或 clip。[implementation-matters-2020](bibliography.md#implementation-matters-2020) 说明了实现差异对结果归因的重要性；这里的检查顺序是据此提出的诊断方案，具体项目见 [05 selector](05-ppo-enhancement.md#从失败信号选择接口)。

轨迹几何贴合而物体仍滑落时，重点检查接触与控制。按 phase 记录 reference error、object motion、接触失败、base-only 成功率和 residual 饱和情况，核对 reference、base controller 与 reset 的可执行性。若早期失败使后续 phase 很少得到采样，可以单独比较 phase resets 或 curriculum，并始终从固定部署初始状态报告 end-to-end success，详见 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

动作表示是否合适，需要在数据与更新口径一致后判断。可以检查同一条件下的成功动作是否具有多种模式，以及这些模式与 Gaussian baseline 的失败、imitation 的恢复表现有何关联，再用对照实验评估 diffusion 的作用。计算效率则通过 simulator、actor 和 update 的分段耗时判断，实验拆分见 [05](05-ppo-enhancement.md)。

## 候选选择：五个方法族

以下五类方法分别处理交互学习、数据获取、跨形态引导、动作表示和奖励优化，可以根据任务需要组合。各节先说明论文做过的工作，再讨论使用条件、成本与建议的最小实验。

### 仿真 RL 与 sim-to-real 工程

仿真 RL 适合已有任务和奖励、需要通过交互学习接触控制的场景。[openai-inhand-2020](bibliography.md#openai-inhand-2020) 与 [dextreme-2022](bibliography.md#dextreme-2022) 报告了各自系统从仿真到真机的策略迁移；[massively-parallel-2021](bibliography.md#massively-parallel-2021) 则研究 locomotion 中的并行训练，为吞吐与训练时间的测量提供参照。

采用这条路线需要可复现的 simulator、reward/reset 和 Gaussian PPO baseline，并明确训练与部署的观测差异。主要投入包括接触仿真、奖励设计、randomization 校准、环境交互和部署验证。准备阶段先检查 reset 的物理可行性、部署观测来源与成功指标，再评估训练规模和样本效率。

最小实验可以固定任务测量 Gaussian PPO，然后只改变一个 randomization family 或并行规模。分别报告固定 interactions 与固定 wall-clock 下的结果，并记录扰动条件下的 task success，从而区分分布覆盖与计算吞吐的贡献。

### 遥操作与数据采集

遥操作用于获取成功的 robot demonstrations，也可补充现有运动记录中的同步观测和可执行动作。[dexpilot-2020](bibliography.md#dexpilot-2020)、[anyteleop-2023](bibliography.md#anyteleop-2023) 与 [dexcap-2024](bibliography.md#dexcap-2024) 分别介绍了各自的运动映射与数据管线，比较时应结合任务和设备配置阅读。

采集前需要确定机器人动作接口、传感同步、操作者控制和安全流程，并分别保存 reference target 与 executed action。设备、标定、操作者时间、失败标注和 embodiment 对齐构成主要成本。若现有数据已覆盖成功行为且动作定义一致，可以先检查 reward、update 或 reset，再决定追加采集的内容。

最小实验可以固定任务与 imitation 模型，比较数据筛选或采集方案。结果同时记录成功接触片段的覆盖、同步误差和闭环 task success，用于判断新增数据对策略的实际帮助；可执行性检查见 [03](03-retargeting-to-policy.md#遥操作与数据管线)。

### 人类视频与模仿

人类视频提供运动、场景和任务结构，机器人学习还需要跨 embodiment 的映射。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 报告机器人手 imitation，[mimicplay-2023](bibliography.md#mimicplay-2023) 将 human play 与少量 robot demonstrations 结合，分别展示运动映射和高层引导的用途。

这类方法适合有可利用的人类运动、需要 reference 或任务引导的场景。实施时要处理姿态与物体估计、时间对齐、遮挡和接触可行性；使用 robot demonstrations 时另行记录其数量。精确接触任务还需确认物体与接触状态可以恢复，并通过机器人执行验证动作监督或 reference 的质量。

最小实验可以固定 robot 数据与下游模型，比较有/无视频引导。分别记录 reference 可行率与闭环成功率，使几何映射和控制完成各有独立指标。

### Diffusion policy

Diffusion policy 用条件生成模型学习示范中的动作分布，适合研究多模态动作与 action horizon。[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 报告 visuomotor imitation，[dp3-2024](bibliography.md#dp3-2024) 研究 3D representation；这两类工作分别提供动作生成与观测表示的参照。

训练需要成功的 robot observation-action 数据、明确的 prediction/execution horizon，以及部署可用输入。主要成本来自 denoising 推理、数据覆盖、chunk 与 controller 对齐和观测一致性检查。可以先验证动作监督与 reference 的可执行性，再测候选 sampler 的 latency 是否适合控制周期；闭环成功和恢复表现由目标任务实验判断。

最小实验是在相同数据、observation、action horizon 与测试 reset 下，比较 Gaussian imitation 和 diffusion imitation。先建立 imitation 闭环，再根据任务需求决定是否加入 reward fine-tuning；auxiliary density 与 online 更新在下一节单独讨论。

### Diffusion 与 RL

Diffusion 与 RL 的结合可以利用任务奖励继续改进 imitation 策略，也可研究 Gaussian actor 在一致条件下出现的表示限制。[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 与 [idql-2023](bibliography.md#idql-2023) 提供 offline 路线，[dppo-2024](bibliography.md#dppo-2024) v3 §4–5 介绍 denoising-step PPO 与 fine-tuning。可逆性与 exact density 则需要针对所选 sampler 核查。

Offline 方法从静态数据学习，on-policy fine-tuning 需要可交互环境；选择时应分别盘点数据与交互资源。两者都需要清晰的 baseline，on-policy 方法还需确定 probability object 和 rollout schema。额外成本包括 sampling、likelihood 求值、denoising trajectory 或 auxiliary action 存储、update compute，以及数据来源和版本管理。

最小实验可以固定任务、数据和 Gaussian baseline，再更换 actor 及其必需的记录、更新接口。开始比较前确认 old log-prob 能在原采样变量上重算，数据版本匹配，观测、reference 与 reset 已完成检查。若 actor、update schema 和 pretraining 一起改变，结果按组合方案归因，详见 [04](04-onpolicy-diffusion-interface.md)。

## 三条起步路线

有 simulator、示范数据尚待准备时，可以先建立 Gaussian PPO baseline。固定 reward、reset、observation 和 action semantics，输出学习曲线、成功率、掉落率、KL/clip fraction 与分段耗时；记录一致后，再根据具体失败现象选择后续方法。这一顺序以 [ppo-2017](bibliography.md#ppo-2017) 为起点，实施检查见 [05](05-ppo-enhancement.md#固定-ppo-更新与估计口径)。

已有成功 robot demonstrations 时，可以先验证 imitation 闭环，再决定是否进行 reward fine-tuning。统一数据与部署动作后，在固定 reset 下测 success 和偏离示范后的恢复；达到任务判据的 imitation 策略可以直接作为交付方案。有进一步优化需求时，再结合 [dppo-2024](bibliography.md#dppo-2024) 的实验设置设计 fine-tuning 对照。

已有 reference 或 base controller 时，可以依次验证物理可行性、base-only 和 Gaussian residual，再评估生成式 actor。按 [03](03-retargeting-to-policy.md) 区分 BC、tracking 与 reset 用途，固定 controller、reference 的版本及 residual scale。这个顺序借鉴 [residual-rl-2018](bibliography.md#residual-rl-2018) 的控制分工，旨在先确定 reference 与控制接口各自的作用，再测目标任务收益。

## 首个实验与停止条件

首个实验应围绕一个可证伪的问题组织。写明失败信号、候选解释、唯一改动接口、共同数据与环境配置、seed 列表、interactions 与 wall-clock 上限、部署 latency 限制，以及事先定义的成功判据。报告 baseline 与对照的 per-seed 结果、失败类型和预算消耗，按完整结果判断方法；任务用途与记录要求见 [04](04-onpolicy-diffusion-interface.md#按诊断目的的任务验证) 和 [05](05-ppo-enhancement.md#评估顺序与停止条件)。

停止条件应区分接口检查和实验结果。动作 log-prob 重算、reset 可行性、部署输入和 latency 预算中的任一检查失败时，暂停追加训练并修复对应接口。预算耗尽而预定义 task metric 持平或变差时，保留负结果，后续改动作为新假设评估；训练 reward 上升而固定测试 success 持平或下降时，重新检查奖励与任务目标的对应关系。
