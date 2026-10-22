# 注释书目

本文件是 37 篇入选作品的唯一逐篇注释位置；其他文档只通过稳定 paper ID 指向这里。除 [genpo-2025](#genpo-2025) 与 [dppo-2024](#dppo-2024) 的机制说明来自指定全文版本外，其余条目的证据上限是所记录版本的 abstract 与公开元数据，超出该范围的分析明确标为【推测】。

## openai-inhand-2020
- paper-id：openai-inhand-2020
- title：Learning Dexterous In-Hand Manipulation
- authors-year：Andrychowicz 等，2018
- arxiv：1808.00177v5
- tier：core
- evidence：v5 abstract
- 解决什么问题：研究仅在仿真训练的策略能否在物理 Shadow Hand 上完成视觉闭环的物体重定向。
- 方法与信号是什么：使用 RL、视觉物体状态与广泛的物理及外观 randomization，不依赖人类示范。
- 验证到哪里及缺口：已覆盖证据：abstract 报告策略从仿真迁移到真机，并出现 finger gaiting 等行为。 不支持的结论：动作语义、延迟和具体观测历史未报告。
- 对两类读者有什么用：【推测】同事 A 可把它作为生成式策略之外的 sim-to-real 对照，retargeting 读者可把它作为直接从任务奖励学习接触策略的基线。
- 主源：[arXiv v5](https://arxiv.org/abs/1808.00177v5)

## openai-rubiks-2019
- paper-id：openai-rubiks-2019
- title：Solving Rubik's Cube with a Robot Hand
- authors-year：Akkaya 等，2019
- arxiv：1910.07113v1
- tier：core
- evidence：v1 abstract
- 解决什么问题：研究仿真策略在复杂长序列灵巧操作中的真机迁移与适应。
- 方法与信号是什么：提出 Automatic Domain Randomization（ADR），同时训练控制策略和视觉状态估计器，并使用带 memory 的策略。
- 验证到哪里及缺口：已覆盖证据：abstract 报告物理机器人解 Rubik's Cube，并观察到 test-time emergent meta-learning。 不支持的结论：动作接口和训练代价未报告。
- 对两类读者有什么用：【推测】同事 A 可用它检查 diffusion on-policy 方法是否保留 adaptation，retargeting 读者可用 ADR 作为课程与 sim-to-real 层的候选。
- 主源：[arXiv v1](https://arxiv.org/abs/1910.07113v1)

## dextreme-2022
- paper-id：dextreme-2022
- title：DeXtreme: Transfer of Agile In-hand Manipulation from Simulation to Reality
- authors-year：Handa 等，2022
- arxiv：2210.13702v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：研究多指灵巧操作策略和物体 pose estimator 如何跨越仿真到现实的差异。
- 方法与信号是什么：在 Isaac Gym 中训练适应广泛条件的 Allegro Hand 策略，并配合实时视觉 pose estimation。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 vision policy 在同一重定向任务上优于既有视觉策略，且接近 privileged-state 策略。 不支持的结论：历史、延迟和控制频率未报告。
- 对两类读者有什么用：【推测】同事 A 可用它界定视觉闭环测试，retargeting 读者可用它分离 state estimation 与 policy adaptation。
- 主源：[arXiv v2](https://arxiv.org/abs/2210.13702v2)

## visual-dexterity-2022
- paper-id：visual-dexterity-2022
- title：Visual Dexterity: In-Hand Reorientation of Novel and Complex Object Shapes
- authors-year：Chen 等，2022；Science Robotics 2023
- arxiv：2211.11744v3
- tier：core
- evidence：v3 abstract
- 解决什么问题：研究单个 commodity depth camera 能否支持新颖复杂形状的实时任意旋转重定向。
- 方法与信号是什么：在仿真中用 RL 训练视觉控制器，再在未见物体上进行真机评估。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 median reorientation time 接近 7 秒，并给出 duck 物体的掉落率和角度成功统计。 不支持的结论：动作语义和训练细节未报告。
- 对两类读者有什么用：【推测】同事 A 可把新物体视觉条件作为接口压力测试，retargeting 读者可把物体泛化与接触稳定性作为分离指标。
- 主源：[arXiv v3](https://arxiv.org/abs/2211.11744v3)

## sequential-dexterity-2023
- paper-id：sequential-dexterity-2023
- title：Sequential Dexterity: Chaining Dexterous Policies for Long-Horizon Manipulation
- authors-year：Chen 等，2023
- arxiv：2309.00987v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：研究差异显著的 dexterous sub-policy 如何组成 long-horizon 任务并从失败中恢复。
- 方法与信号是什么：以 transition feasibility function 逐步 fine-tune 子策略，并进行 autonomous switching、recovery 与跳过冗余阶段。
- 验证到哪里及缺口：已覆盖证据：abstract 报告少量训练物体上的仿真训练、新形状泛化和真机 zero-shot transfer。 不支持的结论：切换观测与延迟未报告。
- 对两类读者有什么用：【推测】同事 A 可区分单策略生成与 policy chaining，retargeting 读者可把 reference 分段和 transition feasibility 视为独立问题。
- 主源：[arXiv v2](https://arxiv.org/abs/2309.00987v2)

## dapg-2018
- paper-id：dapg-2018
- title：Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations
- authors-year：Rajeswaran 等，2017；RSS 2018
- arxiv：1709.10087v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：研究 model-free DRL 如何扩展到 24-DoF 灵巧手并降低实体系统所需样本量。
- 方法与信号是什么：从少量人类 demonstrations 引导策略学习，再由 RL 优化任务行为。
- 验证到哪里及缺口：已覆盖证据：abstract 报告仿真从零学习及 demonstrations 显著降低 sample complexity，并提升动作自然性和 robustness。 不支持的结论：具体 demo 注入公式不在本条证据范围。
- 对两类读者有什么用：【推测】同事 A 可把 demo 初始化与 diffusion pretraining 对照，retargeting 读者可把 retargeted motion 作为 demonstration 信号候选。
- 主源：[arXiv v2](https://arxiv.org/abs/1709.10087v2)

## bi-dexhands-2023
- paper-id：bi-dexhands-2023
- title：Towards Human-Level Bimanual Dexterous Manipulation with Reinforcement Learning
- authors-year：Chen 等，2022
- arxiv：2206.08686v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：提供双手灵巧操作 benchmark，并比较 single-agent、multi-agent、offline、multi-task 与 meta RL。
- 方法与信号是什么：在 Isaac Gym 中构建数十项双手任务和数千目标物体，利用 GPU 并行评估多类 RL 设定。
- 验证到哪里及缺口：已覆盖证据：abstract 报告单卡 30,000+ FPS、PPO 类方法可解简单任务，multi-agent RL 有助于部分协同任务，而 multi-task/few-shot 多数失败。 不支持的结论：真机证据未报告。
- 对两类读者有什么用：【推测】同事 A 可用它检验生成策略在双手高维空间的可扩展性，retargeting 读者可用它区分单策略并行与真正 multi-agent 分解。
- 主源：[arXiv v2](https://arxiv.org/abs/2206.08686v2)

## isaac-lab-2023
- paper-id：isaac-lab-2023
- title：Orbit: A Unified Simulation Framework for Interactive Robot Learning Environments
- authors-year：Mittal 等，2023；IEEE RA-L
- arxiv：2301.04195v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：提供统一、模块化且 GPU 加速的机器人学习环境构建框架。
- 方法与信号是什么：基于 NVIDIA Isaac Sim 组织 rigid/deformable simulation、传感器、motion generator、RL 与 demonstration collection。
- 验证到哪里及缺口：已覆盖证据：abstract 列出 16 个机器人平台、4 种 sensor modality、10 个 motion generator 和 20+ benchmark task。 不支持的结论：特定灵巧手任务的可比协议未报告。
- 对两类读者有什么用：【推测】同事 A 可把它作为大规模 on-policy 实验平台背景，retargeting 读者可据其模块边界规划 reference、observation 与 action 接口。
- 主源：[arXiv v2](https://arxiv.org/abs/2301.04195v2)

## dexpilot-2020
- paper-id：dexpilot-2020
- title：DexPilot: Vision Based Teleoperation of Dexterous Robotic Hand-Arm System
- authors-year：Handa 等，2019
- arxiv：1910.03135v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：降低高自由度手臂-手 teleoperation 的成本，同时保留完整控制能力。
- 方法与信号是什么：仅观察裸手来控制 23-DoA 系统，并采集高维 multimodal state-action data。
- 验证到哪里及缺口：已覆盖证据：abstract 报告两位操作者、多任务上的 speed 与 reliability 测量。 不支持的结论：下游 autonomous policy 的效果未报告。
- 对两类读者有什么用：【推测】同事 A 可把数据作为 diffusion pretraining 来源，retargeting 读者可比较在线 teleoperation 与离线 mocap retargeting 的误差结构。
- 主源：[arXiv v2](https://arxiv.org/abs/1910.03135v2)

## anyteleop-2023
- paper-id：anyteleop-2023
- title：AnyTeleop: A General Vision-Based Dexterous Robot Arm-Hand Teleoperation System
- authors-year：Qin 等，2023
- arxiv：2307.04577v3
- tier：core
- evidence：v3 abstract
- 解决什么问题：让 vision-based teleoperation 跨多种 arm、hand、reality 与 camera configuration 复用。
- 方法与信号是什么：以统一系统适配多种 simulator 和 real hardware，并输出可用于 imitation learning 的操作数据。
- 验证到哪里及缺口：已覆盖证据：abstract 报告真机成功率优于特定硬件系统，仿真数据带来更好的 imitation learning。 不支持的结论：各形态动作空间的严格一致性未报告。
- 对两类读者有什么用：【推测】同事 A 可用它研究跨 embodiment 的 pretraining 数据，retargeting 读者可用它检查 morphologic mapping 是否成为独立数据层。
- 主源：[arXiv v3](https://arxiv.org/abs/2307.04577v3)

## dexcap-2024
- paper-id：dexcap-2024
- title：DexCap: Scalable and Portable Mocap Data Collection System for Dexterous Manipulation
- authors-year：Wang 等，2024
- arxiv：2403.07788v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：提高人手 mocap 数据采集的便携性，并把人类运动转为有效机器人策略。
- 方法与信号是什么：DexCap 联合 SLAM、电磁追踪和 3D observation；DexIL 使用 inverse kinematics、point-cloud imitation 与可选 human-in-the-loop correction。
- 验证到哪里及缺口：已覆盖证据：abstract 报告六项 dexterous task 和 in-the-wild mocap 学习。 不支持的结论：动力学可执行性约束与在线延迟未报告。
- 对两类读者有什么用：【推测】同事 A 可把其数据用于 diffusion policy 预训练，retargeting 读者可把 IK 输出与 policy-ready trajectory 之间的差距作为研究对象。
- 主源：[arXiv v2](https://arxiv.org/abs/2403.07788v2)

## diffusion-policy-2023
- paper-id：diffusion-policy-2023
- title：Diffusion Policy: Visuomotor Policy Learning via Action Diffusion
- authors-year：Chi 等，2023；RSS 2023
- arxiv：2303.04137v5
- tier：core
- evidence：v5 abstract
- 解决什么问题：用条件 denoising diffusion process 表示 multimodal、高维 visuomotor action distribution。
- 方法与信号是什么：学习 action-distribution score，并结合 receding horizon control、visual conditioning 与 time-series diffusion transformer。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 4 个 manipulation benchmark 的 12 项任务及相对既有方法平均提升 46.9%。 不支持的结论：online RL 与灵巧手专项证据未报告。
- 对两类读者有什么用：【推测】同事 A 可把它作为 DPPO/GenPO 的生成策略背景，retargeting 读者可把 action chunking 作为从轨迹到闭环策略的一种表示。
- 主源：[arXiv v5](https://arxiv.org/abs/2303.04137v5)

## dppo-2024
- paper-id：dppo-2024
- title：Diffusion Policy Policy Optimization
- authors-year：Ren 等，2024
- arxiv：2409.00588v3
- tier：core
- evidence：v3 Section 3；Section 4.1、Eq. (4.1)–(4.4)；Section 4.2、Eq. (4.5)–(4.8)；Section 4.3；Section 5–6 与 Appendix D（Table A1–A5）
- 解决什么问题：让预训练 Diffusion Policy 能以 policy gradient/PPO 进行 online fine-tuning，而不要求显式计算最终 action chunk 的边缘密度。
- 方法与信号是什么：把每个 Gaussian denoising transition 视为扩展 MDP 的 policy action，ratio 对象是逐步 denoising likelihood；通常从 demonstrations 预训练，支持 action chunk、部分 denoising-step fine-tuning 与 stochastic DDIM exploration。
- 验证到哪里及缺口：已覆盖证据：Section 5 覆盖 locomotion、Franka Kitchen、Robomimic、Furniture-Bench 与 zero-shot sim-to-real；Appendix D Table A3 的 Lift 单轮训练为 Gaussian-MLP 27.7 s、DPPO-MLP 35.6 s、DPPO-UNet 83.6 s。 不支持的结论：未验证 dexterous hand；不能将 Section 5 的约 2× 概述当作全局开销上限。
- 对两类读者有什么用：【论文直接验证】同事 A 应把它作为 GenPO 的核心 on-policy comparator；【机制相关】retargeting 读者可用 demonstration pretraining 加 online fine-tuning 的链条，但灵巧手接触迁移仍需新证据。
- 主源：[arXiv HTML v3 §3](https://arxiv.org/html/2409.00588v3#S3)、[§4](https://arxiv.org/html/2409.00588v3#S4)、[§5](https://arxiv.org/html/2409.00588v3#S5)、[§6](https://arxiv.org/html/2409.00588v3#S6)、[Appendix D](https://arxiv.org/html/2409.00588v3#A4)

## genpo-2025
- paper-id：genpo-2025
- title：GenPO: Generative Diffusion Models Meet On-Policy Reinforcement Learning
- authors-year：Ding 等，2025
- arxiv：2505.18763v4
- tier：core
- evidence：v4 Section 4.1、Eq. (5)；Section 4.2、Eq. (7)–(8)；Section 4.3、Eq. (9)–(12) 与 Algorithm 1；Section 5.1–5.2 与 Section 6；Appendix A、B（Table 10）、C、D.5
- 解决什么问题：为大规模并行 on-policy RL 构造可计算 exact log-likelihood 的生成式 flow policy。
- 方法与信号是什么：在 doubled dummy/auxiliary action `ã=(x,y)` 上构造可逆 diffusion mapping，执行 `a=(x+y)/2`，并以 `πθ(ã|s)` 计算 PPO ratio、entropy 与 KL；Algorithm 1 明确保存 dummy action 和 probability。
- 验证到哪里及缺口：已覆盖证据：Section 5.1 与 Appendix A 在 8 个 IsaacLab benchmark 上验证，含 `Isaac-Repose-Cube-Shadow-Direct-v0`；Section 6 与 Appendix D.5 报告计算/内存开销。 不支持的结论：未报告真机在线 fine-tuning 或 retargeting/residual 组合，auxiliary likelihood 不等于执行动作密度。
- 对两类读者有什么用：【论文直接验证】同事 A 可据此复现 auxiliary-action likelihood 接口；【机制相关】retargeting 读者可研究其作为 residual/reference-conditioned on-policy actor 的可能性，但该组合与真机收益均【需新证据】。
- 主源：[arXiv HTML v4 §4](https://arxiv.org/html/2505.18763v4#S4)、[§5](https://arxiv.org/html/2505.18763v4#S5)、[§6](https://arxiv.org/html/2505.18763v4#S6)、[Appendix A](https://arxiv.org/html/2505.18763v4#A1)、[Appendix B](https://arxiv.org/html/2505.18763v4#A2)、[Appendix C](https://arxiv.org/html/2505.18763v4#A3)、[Appendix D.5](https://arxiv.org/html/2505.18763v4#A4.SS5)

## ppo-2017
- paper-id：ppo-2017
- title：Proximal Policy Optimization Algorithms
- authors-year：Schulman 等，2017
- arxiv：1707.06347v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：在保持 policy-gradient 实现简洁的同时，允许同一批 on-policy 数据进行多 epoch minibatch 更新。
- 方法与信号是什么：交替进行环境采样和 surrogate objective 优化，以 proximal 更新约束 policy change。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 simulated locomotion 与 Atari benchmark，并比较 sample complexity、simplicity 与 wall-time。 不支持的结论：灵巧操作未报告。
- 对两类读者有什么用：【推测】两类读者都应把它作为 ratio、clip 与 update cadence 的共同基线，而不是把实现增强误归因于 policy class。
- 主源：[arXiv v2](https://arxiv.org/abs/1707.06347v2)

## implementation-matters-2020
- paper-id：implementation-matters-2020
- title：Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO
- authors-year：Engstrom 等，2020
- arxiv：2005.12729v1
- tier：core
- evidence：v1 abstract
- 解决什么问题：识别 PPO/TRPO 的性能提升有多少来自论文主算法之外的 code-level optimization。
- 方法与信号是什么：对实现中的 algorithm augmentation 进行 case study 和 attribution。
- 验证到哪里及缺口：已覆盖证据：abstract 报告这些优化解释 PPO 相对 TRPO 的多数累计回报提升，并会改变算法行为。 不支持的结论：dexterous setting 未报告。
- 对两类读者有什么用：【推测】两类读者可据此要求所有 GenPO/retargeting 对照共享 observation normalization、optimizer 与 rollout 口径。
- 主源：[arXiv v1](https://arxiv.org/abs/2005.12729v1)

## massively-parallel-2021
- paper-id：massively-parallel-2021
- title：Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning
- authors-year：Rudin 等，2021
- arxiv：2109.11978v3
- tier：core
- evidence：v3 abstract
- 解决什么问题：研究单 workstation GPU 上大规模并行如何缩短实体机器人 policy generation 时间。
- 方法与信号是什么：分析 massively parallel regime 的算法组件，并加入适合数千仿真机器人的 game-inspired curriculum。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 ANYmal 平地训练少于 4 分钟、崎岖地形约 20 分钟并迁移真机。 不支持的结论：灵巧操作接触分布未报告。
- 对两类读者有什么用：【推测】同事 A 可评估 diffusion update 能否吸收并行吞吐，retargeting 读者可借鉴 curriculum 但不能直接外推 locomotion 结果。
- 主源：[arXiv v3](https://arxiv.org/abs/2109.11978v3)

## residual-rl-2018
- paper-id：residual-rl-2018
- title：Residual Reinforcement Learning for Robot Control
- authors-year：Johannink 等，2018
- arxiv：1812.03201v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：把可由 conventional feedback control 处理的结构与难以建模的接触、摩擦 residual 分开学习。
- 方法与信号是什么：最终 control policy 是 base controller signal 与 RL residual signal 的叠加。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 real-world block assembly。 不支持的结论：对 diffusion likelihood、动作约束和 retargeted reference 未报告。
- 对两类读者有什么用：【推测】同事 A 需区分 auxiliary-action likelihood 与执行端 residual mapping，retargeting 读者可把位置级 controller 作为 base、RL 作为 residual 的起点。
- 主源：[arXiv v2](https://arxiv.org/abs/1812.03201v2)

## sapg-2024
- paper-id：sapg-2024
- title：SAPG: Split and Aggregate Policy Gradients
- authors-year：Singla 等，2024
- arxiv：2407.20230v1
- tier：core
- evidence：v1 abstract
- 解决什么问题：缓解 PPO 在并行环境数量增大后性能饱和、不能继续利用新增数据的问题。
- 方法与信号是什么：把并行环境拆为 chunks，再通过 importance sampling 聚合 policy-gradient 更新。
- 验证到哪里及缺口：已覆盖证据：abstract 报告多项 challenging environment 上优于 vanilla PPO 和强基线。 不支持的结论：灵巧手、生成策略及具体计算开销未报告。
- 对两类读者有什么用：【推测】同事 A 可把它作为 GenPO 并行扩展的 update-layer 对照，retargeting 读者可在固定策略结构后单独测数据聚合收益。
- 主源：[arXiv v1](https://arxiv.org/abs/2407.20230v1)

## demostart-2024
- paper-id：demostart-2024
- title：DemoStart: Demonstration-led auto-curriculum applied to sim-to-real with multi-fingered robots
- authors-year：Bauza 等，2024
- arxiv：2409.06613v2
- tier：core
- evidence：v2 abstract
- 解决什么问题：从少量仿真 demonstrations 和 sparse reward 学习三指手臂-手复杂操作，并实现 zero-shot sim-to-real。
- 方法与信号是什么：demonstration-led auto-curriculum 配合 domain randomization，部署策略输入为多相机 raw pixels 与 proprioception。
- 验证到哪里及缺口：已覆盖证据：abstract 报告相对真机 demonstrations 学习方法使用少 100 倍 demonstrations。 不支持的结论：课程构造细节和动作语义未报告。
- 对两类读者有什么用：【推测】同事 A 可把它作为 demo curriculum 而非 policy-class 改造，retargeting 读者可把 reference 起始状态转为 curriculum 候选。
- 主源：[arXiv v2](https://arxiv.org/abs/2409.06613v2)

## leap-hand-2023
- paper-id：leap-hand-2023
- title：LEAP Hand: Low-Cost, Efficient, and Anthropomorphic Hand for Robot Learning
- authors-year：Shaw 等，2023
- arxiv：2309.06440v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：提供面向 robot learning 的低成本、耐用 anthropomorphic hand。
- 方法与信号是什么：采用新的 kinematic structure，并发布 assembly instruction、Sim2Real pipeline 与 API。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 4 小时组装、2000 美元成本及多类真机任务。 不支持的结论：标准 benchmark 的 observation/action protocol 未报告。
- 对两类读者有什么用：【推测】它可用于评估方法对低成本硬件的迁移，但不能把硬件结果直接与 Shadow/Allegro benchmark 排名。
- 主源：[arXiv v1](https://arxiv.org/abs/2309.06440v1)

## zhu-2018
- paper-id：zhu-2018
- title：Dexterous Manipulation with Deep Reinforcement Learning: Efficient, General, and Low-Cost
- authors-year：Zhu 等，2018
- arxiv：1810.06045v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：检验多指接触任务能否在低成本真机上直接用 model-free deep RL 从零学习。
- 方法与信号是什么：直接从 sensor reading 到 action，并测试少量 demonstrations 对学习速度的影响。
- 验证到哪里及缺口：已覆盖证据：abstract 报告多数任务从零约 4–7 小时、加 demonstrations 后约 2–3 小时。 不支持的结论：任务协议和现代 PPO 对照未报告。
- 对两类读者有什么用：【推测】它提供真机在线 RL 的历史参照，但其时间数字不能直接外推到 diffusion policy 或 REGRIND。
- 主源：[arXiv v1](https://arxiv.org/abs/1810.06045v1)

## trifinger-2021
- paper-id：trifinger-2021
- title：Transferring Dexterous Manipulation from GPU Simulation to a Remote Real-World TriFinger
- authors-year：Allshire 等，2021
- arxiv：2108.09779v2
- tier：extended
- evidence：v2 abstract
- 解决什么问题：把 arbitrary 6-DoF cube pose manipulation 从 Isaac Gym 迁移到 remote TriFinger。
- 方法与信号是什么：在 policy observation 与 reward 中使用 object pose keypoint representation，并结合 domain randomization。
- 验证到哪里及缺口：已覆盖证据：abstract 报告远程真机 83% success rate。 不支持的结论：与 anthropomorphic in-hand reorientation 的动作和接触结构不同。
- 对两类读者有什么用：【推测】它提示 representation 与 reward 可共同影响迁移，应与 policy algorithm 的贡献隔离。
- 主源：[arXiv v2](https://arxiv.org/abs/2108.09779v2)

## rotate-touch-2023
- paper-id：rotate-touch-2023
- title：Rotating without Seeing: Towards In-hand Dexterity through Touch
- authors-year：Yin 等，2023
- arxiv：2303.10880v4
- tier：extended
- evidence：v4 abstract
- 解决什么问题：研究不依赖视觉时，touch-only observation 能否支持新物体 in-hand rotation。
- 方法与信号是什么：在手掌、finger links 和 fingertips 上布置 dense binary force sensors，并在仿真中用 RL 训练。
- 验证到哪里及缺口：已覆盖证据：abstract 报告真机直接部署并旋转训练未见物体。 不支持的结论：延迟、history 与精确成功率未报告。
- 对两类读者有什么用：【推测】它要求 diffusion 与 retargeting 方法把 tactile modality 作为横切 observation 变量，而不是独立方法族。
- 主源：[arXiv v4](https://arxiv.org/abs/2303.10880v4)

## openteach-2024
- paper-id：openteach-2024
- title：OPEN TEACH: A Versatile Teleoperation System for Robotic Manipulation
- authors-year：Iyer 等，2024
- arxiv：2403.07870v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：提供开源、低成本且覆盖多类机器人形态的 teleoperation 数据采集系统。
- 方法与信号是什么：基于 Meta Quest 3，以自然手势控制多指手和双臂，最高报告 90 Hz 操作。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 38 项 teleoperation task、与 AnyTeleop 的 user study，以及 10 项下游 policy-learning task。 不支持的结论：统一动作语义未报告。
- 对两类读者有什么用：【推测】它可作为数据吞吐与操作者负担参照，但不能代替接触可执行性评估。
- 主源：[arXiv v1](https://arxiv.org/abs/2403.07870v1)

## bunny-visionpro-2024
- paper-id：bunny-visionpro-2024
- title：Bunny-VisionPro: Real-Time Bimanual Dexterous Teleoperation for Imitation Learning
- authors-year：Ding 等，2024
- arxiv：2407.03162v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：提高双手 dexterous teleoperation 的协调、安全与 downstream imitation quality。
- 方法与信号是什么：使用 VR headset、低成本 haptic feedback、collision avoidance 与 singularity avoidance。
- 验证到哪里及缺口：已覆盖证据：abstract 报告标准任务上成功率和完成时间优于既有系统，并覆盖 multi-stage long-horizon imitation。 不支持的结论：具体数值和 latency 未报告。
- 对两类读者有什么用：【推测】它可为双手数据管线提供安全约束来源，但与单手 retargeting 结果不可直接合并。
- 主源：[arXiv v1](https://arxiv.org/abs/2407.03162v1)

## robotic-telekinesis-2022
- paper-id：robotic-telekinesis-2022
- title：Robotic Telekinesis: Learning a Robotic Hand Imitator by Watching Humans on Youtube
- authors-year：Sivakumar 等，2022
- arxiv：2202.10448v2
- tier：extended
- evidence：v2 abstract
- 解决什么问题：从单个未标定 RGB camera 把人手运动实时 retarget 到不同形态的 robot hand-arm。
- 方法与信号是什么：利用互联网人手视频学习 human-hand representation，并约束输出 trajectory 平滑且无 self-collision。
- 验证到哪里及缺口：已覆盖证据：abstract 报告未训练操作者可完成多项 teleoperation task。 不支持的结论：object contact feasibility 和 autonomous policy learning 未报告。
- 对两类读者有什么用：【推测】它清楚展示 kinematic/semantic retargeting，但也暴露无碰撞不等于动力学可执行。
- 主源：[arXiv v2](https://arxiv.org/abs/2202.10448v2)

## mimicplay-2023
- paper-id：mimicplay-2023
- title：MimicPlay: Long-Horizon Imitation Learning by Watching Human Play
- authors-year：Wang 等，2023
- arxiv：2302.12422v2
- tier：extended
- evidence：v2 abstract
- 解决什么问题：降低 long-horizon real-world imitation learning 对机器人 demonstrations 的需求。
- 方法与信号是什么：从 human play video 学 latent plan，再以少量 teleoperated demonstration 学 low-level visuomotor control。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 14 项真机 long-horizon task 上的 success、generalization 和 robustness 提升。 不支持的结论：灵巧手专项与 on-policy RL 未报告。
- 对两类读者有什么用：【推测】它提供 human video 作为高层 plan 的组合方式，但不能直接证明 retargeted joint trajectory 可执行。
- 主源：[arXiv v2](https://arxiv.org/abs/2302.12422v2)

## dexmimicgen-2024
- paper-id：dexmimicgen-2024
- title：DexMimicGen: Automated Data Generation for Bimanual Dexterous Manipulation via Imitation Learning
- authors-year：Jiang 等，2024
- arxiv：2410.24185v2
- tier：extended
- evidence：v2 abstract
- 解决什么问题：降低双臂多指 imitation learning 的人工数据采集成本。
- 方法与信号是什么：从少量 human demonstration 在仿真中自动合成 trajectory，并提供 real-to-sim-to-real pipeline。
- 验证到哪里及缺口：已覆盖证据：abstract 报告由 60 条 source demo 生成 21K demos，并部署 humanoid can sorting。 不支持的结论：生成轨迹的接触失配率未报告。
- 对两类读者有什么用：【推测】它可作为 retargeted motion 扩增路线，也可给 diffusion pretraining 提供规模化数据，但需单独审计合成偏差。
- 主源：[arXiv v2](https://arxiv.org/abs/2410.24185v2)

## dp3-2024
- paper-id：dp3-2024
- title：3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations
- authors-year：Ze 等，2024
- arxiv：2403.03954v7
- tier：extended
- evidence：v7 abstract
- 解决什么问题：以紧凑 3D representation 提升 diffusion visuomotor imitation 的数据效率与泛化。
- 方法与信号是什么：从 sparse point cloud 提取 3D feature，作为 conditional diffusion policy 的 observation。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 72 项仿真任务和 4 项真机任务，并给出相对提升及真机成功率。 不支持的结论：online RL 与灵巧手范围未单列。
- 对两类读者有什么用：【推测】它提醒两类读者将 policy class 与 3D observation representation 的收益分开测量。
- 主源：[arXiv v7](https://arxiv.org/abs/2403.03954v7)

## dexdiffuser-2023
- paper-id：dexdiffuser-2023
- title：DexDiffuser: Generating Dexterous Grasps with Diffusion Models
- authors-year：Weng 等，2023
- arxiv：2402.02989v3
- tier：extended
- evidence：v3 abstract
- 解决什么问题：从 partial object point cloud 生成、评估并优化 dexterous grasp。
- 方法与信号是什么：DexSampler 进行 conditional diffusion sampling，DexEvaluator 评分，并用 EGD/ESR refinement。
- 验证到哪里及缺口：已覆盖证据：abstract 报告相对 FFHNet 的仿真与真机 grasp success 提升。 不支持的结论：抓取后 closed-loop manipulation 未报告。
- 对两类读者有什么用：【推测】它覆盖 grasp acquisition，而 GenPO/retargeting 主线主要覆盖后续控制，二者不应按同一任务成功率比较。
- 主源：[arXiv v3](https://arxiv.org/abs/2402.02989v3)

## diffusion-ql-2022
- paper-id：diffusion-ql-2022
- title：Diffusion Policies as an Expressive Policy Class for Offline Reinforcement Learning
- authors-year：Wang 等，2022
- arxiv：2208.06193v3
- tier：extended
- evidence：v3 abstract
- 解决什么问题：在 offline RL 中同时限制 out-of-distribution action 并保留 multimodal policy expressiveness。
- 方法与信号是什么：conditional diffusion loss 联合 behavior cloning 与 action-value maximization。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 2D bandit 与多数 D4RL task 的性能。 不支持的结论：on-policy ratio、并行仿真和 dexterous hand 未报告。
- 对两类读者有什么用：【推测】它是 off-policy/offline comparator，不能据其 Q-guided 结果推断 PPO fine-tuning 收益。
- 主源：[arXiv v3](https://arxiv.org/abs/2208.06193v3)

## idql-2023
- paper-id：idql-2023
- title：IDQL: Implicit Q-Learning as an Actor-Critic Method with Diffusion Policies
- authors-year：Hansen-Estruch 等，2023
- arxiv：2304.10573v2
- tier：extended
- evidence：v2 abstract
- 解决什么问题：为 IQL 隐含的复杂 multimodal actor 提供可抽样的 diffusion policy extraction。
- 方法与信号是什么：从 diffusion behavior policy 采样，再按 critic 权重 importance sample 目标 policy。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 offline RL 基线性能和 hyperparameter robustness。 不支持的结论：online interaction 与机器人专项未报告。
- 对两类读者有什么用：【推测】它提供 critic-guided sampling 对照，但不回答 exact on-policy likelihood 问题。
- 主源：[arXiv v2](https://arxiv.org/abs/2304.10573v2)

## on-policy-actor-critic-2020
- paper-id：on-policy-actor-critic-2020
- title：What Matters In On-Policy Reinforcement Learning? A Large-Scale Empirical Study
- authors-year：Andrychowicz 等，2020
- arxiv：2006.05990v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：系统识别 on-policy continuous-control 实现中大量高低层 design choice 的影响。
- 方法与信号是什么：在统一框架中实现 50+ choices，并训练 250,000+ agents 进行经验比较。
- 验证到哪里及缺口：已覆盖证据：abstract 覆盖五个 continuous-control environment。 不支持的结论：灵巧接触、diffusion actor 与 REGRIND 未报告。
- 对两类读者有什么用：【推测】它要求先固定 update/estimation 细节，再比较 GenPO、residual 或 curriculum 方案。
- 主源：[arXiv v1](https://arxiv.org/abs/2006.05990v1)

## domain-randomization-2017
- paper-id：domain-randomization-2017
- title：Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World
- authors-year：Tobin 等，2017
- arxiv：1703.06907v1
- tier：extended
- evidence：v1 abstract
- 解决什么问题：用模拟图像训练可迁移至真实图像的视觉模型。
- 方法与信号是什么：随机化 simulator rendering，使真实图像落入训练变化范围。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 object localization、1.5 cm accuracy、遮挡鲁棒性与 clutter grasping。 不支持的结论：动力学 randomization 和灵巧手未报告。
- 对两类读者有什么用：【推测】它是视觉 domain randomization 的来源，不应被误写为已经验证 contact dynamics randomization。
- 主源：[arXiv v1](https://arxiv.org/abs/1703.06907v1)

## mappo-2021
- paper-id：mappo-2021
- title：The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games
- authors-year：Yu 等，2021
- arxiv：2103.01955v4
- tier：extended
- evidence：v4 abstract
- 解决什么问题：重新评估 PPO 在 cooperative multi-agent setting 中的 sample efficiency 与最终表现。
- 方法与信号是什么：在四类 multi-agent testbed 上比较 PPO-based 与 off-policy method，并消融实现和 hyperparameter 因素。
- 验证到哪里及缺口：已覆盖证据：abstract 报告 competitive/superior final return 与 sample efficiency。 不支持的结论：机器人手指作为 agent 的设定未验证。
- 对两类读者有什么用：【推测】只有把双手或手指明确建模为 cooperative agents 时才是条件性参照，单 actor REGRIND 不应直接采用。
- 主源：[arXiv v4](https://arxiv.org/abs/2103.01955v4)

## deepmimic-2018
- paper-id：deepmimic-2018
- title：DeepMimic: Example-Guided Deep Reinforcement Learning of Physics-Based Character Skills
- authors-year：Peng 等，2018
- arxiv：1804.02717v3
- tier：extended
- evidence：v3 abstract
- 解决什么问题：把 retargeted motion clip 转为可响应扰动、形态变化和任务目标的 physics-based policy。
- 方法与信号是什么：联合 motion-imitation objective 与 task objective，并整合多个 clip 训练 multi-skill agent。
- 验证到哪里及缺口：已覆盖证据：abstract 覆盖 human、Atlas、dinosaur、dragon 角色和多种动态技能。 不支持的结论：灵巧手接触与 robot manipulation 未报告。
- 对两类读者有什么用：【推测】它支持 tracking reference 与 task reward 的概念链条，但把其 RSI 思想迁移到手部接触仍需新证据。
- 主源：[arXiv v3](https://arxiv.org/abs/1804.02717v3)
