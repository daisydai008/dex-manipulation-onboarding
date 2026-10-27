# 02 从资源和失败信号选择方法

> 本章帮助已有 RL 背景的读者把现有资源映射到候选方法，并把失败现象转化为可检验的实验。

选型从两个事实开始：现有数据、环境和控制器决定了哪些方案可执行，训练中的失败现象决定了先检查哪个接口。把这两条线索分开记录，首个实验才有明确的归因对象。

## 任务定义与成功判据

先把 benchmark 名称展开为可复现的任务定义和成功判据。按 [01](01-problem-structure.md#任务谱系) 写明研究对象属于 in-hand、grasp acquisition、arm-hand、双手还是 long-horizon，并定义 success、掉落、超时和恢复行为。初始接触、测试物体与部署初始分布也要一并记录，它们共同规定回报数字与成功率的含义。

观测与动作定义接着固定训练和部署的输入输出。观测侧分别列出 actor、critic 使用的 privileged state、视觉、proprioception、tactile、history/recurrence，以及采样时间和 delay；动作侧写明 target/delta/velocity/torque、control rate、action chunk 与执行 mapping，待核查项单独列出。训练使用了部署侧难以直接取得的输入时，先确定部署感知来源并验证接口，再评估 actor 容量的影响；相关实例与核查项见 [01 观测](01-problem-structure.md#观测与部分可观测性)。

## 现有资源与约束

现有资源与约束决定候选方法需要哪些准备。先确认 simulator、reward 和 reset 可以复现，再检查成功 robot demonstrations 是否包含同步观测和动作，reference 能否重建 joint/object state，以及 base controller 能否独立闭环。Retargeting 数据的有效性通过执行结果确认，几何误差与接触成功分别记录，检查方法见 [03 数据记录与执行检查](03-retargeting-to-policy.md#数据记录与执行检查)。

训练预算与部署约束需要分开测量。训练侧记录可用 environment interactions、wall-clock 和显存，部署侧记录推理 latency 与允许的控制周期。人类视频提供运动线索，robot action labels 还需经过形态映射和执行记录对齐；真机采样能力则由实际采集周期和延迟决定。完成这份清单后，再选择采集、imitation、RL 或组合路线。

## 失败现象与排查顺序

失败现象决定先检查哪个接口，actor 参数化留到接口一致后比较。更新、接触、动作表示与计算效率各自对应不同的记录和排查顺序。

更新后 KL 或 clip fraction 突变时，先核对同一 action 的 old/new log-prob、advantage、normalization 和 done/truncation 处理，再分别调整 LR、epoch 或 clip。[implementation-matters-2020](bibliography.md#implementation-matters-2020) 说明了实现差异对结果归因的重要性；这里的检查顺序是据此提出的排查方案，具体项目见 [05 selector](05-ppo-enhancement.md#从失败信号选择接口)。

轨迹几何贴合而物体仍滑落时，重点转向接触与控制。按 phase 记录 reference error、object motion、接触失败、base-only 成功率和 residual 饱和情况，核对 reference、base controller 与 reset 的可执行性。早期失败使后续 phase 很少得到采样时，可以单独比较 phase resets 或 curriculum，并始终从固定部署初始状态报告 end-to-end success，详见 [03](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

动作表示是否合适，需要在数据与更新口径一致后判断。可以检查同一条件下的成功动作是否具有多种模式，以及这些模式与 Gaussian baseline 的失败、imitation 的恢复表现有何关联，再用对照实验评估 diffusion 的作用。计算效率则通过 simulator、actor 和 update 的分段耗时判断，实验拆分见 [05](05-ppo-enhancement.md)。

## 候选选择：五个方法族

五类方法分别处理交互学习、数据获取、跨形态引导、动作表示和奖励优化。选择时先看现有资源与失败现象，再核对使用成本，最后用最小实验验证收益。它们可以按任务需要组合。

### 仿真 RL 与 sim-to-real 工程

已有任务和奖励、希望通过交互学习接触控制时，仿真 RL 是直接的起点。[openai-inhand-2020](bibliography.md#openai-inhand-2020) 与 [dextreme-2022](bibliography.md#dextreme-2022) 报告了各自系统从仿真到真机的策略迁移；[massively-parallel-2021](bibliography.md#massively-parallel-2021) 研究 locomotion 中的并行训练，为吞吐与训练时间的测量提供参照。

这条路线要求 simulator、reward/reset 可复现，已有 Gaussian PPO baseline，并能明确训练与部署的观测差异。接触仿真、奖励设计、randomization 校准、环境交互和部署验证构成主要投入。准备阶段先检查 reset 的物理可行性、部署观测来源与成功指标，再评估训练规模和样本效率。

### 遥操作与数据采集

遥操作首先解决成功 robot demonstrations 的来源问题，也能补充现有运动记录中的同步观测和可执行动作。[dexpilot-2020](bibliography.md#dexpilot-2020)、[anyteleop-2023](bibliography.md#anyteleop-2023) 与 [dexcap-2024](bibliography.md#dexcap-2024) 分别介绍了各自的运动映射与数据管线，比较时应结合任务和设备配置阅读。

采集方案需要同时覆盖机器人动作接口、传感同步、操作者控制和安全流程，并分别保存 reference target 与 executed action。设备、标定、操作者时间、失败标注和 embodiment 对齐构成主要成本。现有数据若已覆盖成功行为且动作定义一致，可以先检查 reward、update 或 reset，再决定追加采集的内容。

### 人类视频与模仿

人类视频适合提供 reference 或高层任务引导，机器人学习则还需要跨 embodiment 的映射。[robotic-telekinesis-2022](bibliography.md#robotic-telekinesis-2022) 报告机器人手 imitation，[mimicplay-2023](bibliography.md#mimicplay-2023) 将 human play 与少量 robot demonstrations 结合，分别展示运动映射和高层引导的用途。

实施这类方法时，需要处理姿态与物体估计、时间对齐、遮挡和接触可行性；使用 robot demonstrations 时另行记录其数量。精确接触任务还要确认物体与接触状态可以恢复，并通过机器人执行验证动作监督或 reference 的质量。这些条件决定了视频信息能转化为哪一类训练信号。

### Diffusion policy

Diffusion policy 用条件生成模型学习示范中的动作分布，适合研究多模态动作与 action horizon。[diffusion-policy-2023](bibliography.md#diffusion-policy-2023) 报告 visuomotor imitation，[dp3-2024](bibliography.md#dp3-2024) 研究 3D representation；两类工作分别提供动作生成与观测表示的参照。

训练需要成功的 robot observation-action 数据、明确的 prediction/execution horizon，以及部署可用输入。主要成本来自 denoising 推理、数据覆盖、chunk 与 controller 对齐和观测一致性检查。实施时先验证动作监督与 reference 的可执行性，再测候选 sampler 的 latency 是否适合控制周期；闭环成功和恢复表现由目标任务实验判断。

### Diffusion 与 RL

Diffusion 与 RL 的结合覆盖两条路径：利用静态数据改进策略，以及利用任务奖励继续训练 imitation 策略。[diffusion-ql-2022](bibliography.md#diffusion-ql-2022) 与 [idql-2023](bibliography.md#idql-2023) 提供 offline 路线，[dppo-2024](bibliography.md#dppo-2024) v3 §4–5 介绍 denoising-step PPO 与 fine-tuning。研究 Gaussian actor 在一致条件下的表示限制时，还需针对所选 sampler 核查可逆性与 exact density。

Offline 方法从静态数据学习，on-policy fine-tuning 需要可交互环境，因此数据与交互资源应分别列出。两者都需要清晰的 baseline，on-policy 方法还需确定 probability object 和 rollout schema。额外成本包括 sampling、likelihood 求值、denoising trajectory 或 auxiliary action 存储、update compute，以及数据来源和版本管理。

## 三条起步路线

起步顺序由现有资源决定：simulator、成功 demonstrations 与 reference/base controller 分别对应三种起点。

已有 simulator、示范数据尚待准备时，可以先建立 Gaussian PPO baseline。固定 reward、reset、observation 和 action semantics，输出学习曲线、成功率、掉落率、KL/clip fraction 与分段耗时；记录一致后，再根据具体失败现象选择后续方法。这一顺序以 [ppo-2017](bibliography.md#ppo-2017) 为起点，实施检查见 [05](05-ppo-enhancement.md#固定-ppo-更新与估计口径)。

已有成功 robot demonstrations 时，可以先验证 imitation 闭环，再决定是否进行 reward fine-tuning。统一数据与部署动作后，在固定 reset 下测 success 和偏离示范后的恢复；达到任务判据的 imitation 策略可以直接作为交付方案。有进一步优化需求时，再结合 [dppo-2024](bibliography.md#dppo-2024) 的实验设置设计 fine-tuning 对照。

已有 reference 或 base controller 时，可以依次验证物理可行性、base-only 和 Gaussian residual，再评估生成式 actor。按 [03](03-retargeting-to-policy.md) 区分 BC、tracking 与 reset 用途，固定 controller、reference 的版本及 residual scale。这个顺序借鉴 [residual-rl-2018](bibliography.md#residual-rl-2018) 的控制分工，旨在先确定 reference 与控制接口各自的作用，再测目标任务收益。

## 首个实验与停止条件

五个方法族采用同一套对照原则：每次对照只改动一个接口、检验一个变量，其余条件保持一致。若必须同时改动多个接口，就把整个方案作为组合实验，结果只归因于这一组合，不能据此判断其中某个接口的独立作用。实验结果分别按固定环境交互次数和固定实际运行时长两种预算口径报告，每种口径都列出各个随机种子的结果，并记录失败类型和实际消耗。

首个实验开始前，还要写明观察到的失败现象、准备检验的解释、各组共用的环境配置、部署时延上限和预先确定的成功标准。任务用途与记录要求见 [04](04-onpolicy-diffusion-interface.md#按检查目的选择任务) 和 [05](05-ppo-enhancement.md#评估顺序与停止条件)。

各方法族的特定比较项如下：

- 仿真 RL：固定任务和 baseline，只改变一个 randomization family 或并行规模，记录扰动条件下的 task success，并区分分布覆盖与计算吞吐的贡献。
- 遥操作：固定任务与 imitation 模型，比较数据筛选或采集方案，记录成功接触片段覆盖、同步误差与闭环 task success；可执行性检查见 [03](03-retargeting-to-policy.md#遥操作与数据管线)。
- 人类视频：固定 robot 数据与下游模型，比较启用与关闭视频引导的两组设置，分别记录 reference 可行率与闭环成功率。
- Diffusion policy：在相同数据、observation、action horizon 和测试 reset 下比较 Gaussian imitation 与 diffusion imitation，先建立闭环，再根据任务需求决定是否加入 reward fine-tuning；auxiliary density 与 online 更新见 [概率基础附录](appendix-probability.md)。
- Diffusion 与 RL：固定任务、数据与 Gaussian baseline，再更换 actor 及其必需的记录、更新接口；开始前确认 old log-prob 能在原采样变量上重算、数据版本匹配、观测/reference/reset 已完成检查，详见 [概率基础附录](appendix-probability.md)。

停止条件分为接口检查与实验结果两类。动作 log-prob 重算、reset 可行性、部署输入和 latency 预算中的任一检查失败时，暂停追加训练并修复对应接口。预算耗尽而预定义 task metric 持平或变差时，保留负结果，后续改动作为新假设评估；训练 reward 上升而固定测试 success 持平或下降时，重新检查奖励与任务目标的对应关系。
