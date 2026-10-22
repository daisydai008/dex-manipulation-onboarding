# 04 GenPO 与 dexterous manipulation 的接口

GenPO 的关键接口是 auxiliary action 的 exact likelihood，而不是直接获得机器人执行动作的 marginal density。本章机制事实只依据 [genpo-2025](bibliography.md#genpo-2025) v4 与 [dppo-2024](bibliography.md#dppo-2024) v3；【论文直接验证】限定于指定版本的构造或实验，【机制相关】表示可推导的接口关系，【需新证据】表示尚无对应组合实验。

## 概率对象与 rollout 约定

【论文直接验证】GenPO 在扩展动作空间定义可逆采样变换。按 [genpo-2025](bibliography.md#genpo-2025) v4 §4.2、Eq. (7)–(8)，独立采样 `x₀,y₀ ~ N(0,I)`，通过交替更新与 mixing 得到 auxiliary/dummy action `ã=(x,y)`；两个分量各与环境 action 同维，执行动作取 `a=(x+y)/2`。独立双噪声是 density construction 的条件，不能改写为共享同一噪声的二重表示。

【论文直接验证】change of variables 计算的是 `πθ(ã|s)`。按 [genpo-2025](bibliography.md#genpo-2025) v4 §4.1 Eq. (5) 与 §4.2，记 `z=(x₀,y₀)`、`ã=Fθ(z;s)`，则 `log πθ(ã|s)=log p(z)−log|det D_z Fθ(z;s)|`，其中通过逆映射求 `z=Fθ⁻¹(ã;s)`；exact 指该可逆概率模型的密度，不是无数值误差、精确动力学或机器人传感器无噪声。

【论文直接验证】PPO ratio 必须在同一个已采样的 auxiliary action 上比较新旧策略。[genpo-2025](bibliography.md#genpo-2025) v4 §4.3 Eq. (11) 使用 `rθ=exp(log πθ(ã|s)−log πold(ã|s))`，Algorithm 1 第 4–8 步明确 sample dummy actions、以均值与环境交互，并保存 transitions、dummy actions、probability 和 advantage；不能只存均值 `a` 后反推唯一 `(x,y)`。

【论文直接验证】entropy 与 KL 的估计对象同样是 auxiliary policy。[genpo-2025](bibliography.md#genpo-2025) v4 §4.3 Eq. (9)–(10) 分别定义当前策略的 log-likelihood expectation 与旧策略样本上的 log-prob difference；它们是可采样估计而不是 closed-form execution-action entropy。Eq. (12) 的 compression term 惩罚 `(x−y)²`，用于减少 expanded space 中对同一执行动作的冗余探索，不应解释为真实接触约束。

## 固定 mapping 与 residual

【机制相关】【推测】固定且与待更新 policy 参数无关的 action mapping 可以折入环境，不要求该 mapping 可逆。若 `u=g(s,ã)` 是 rollout 与 update 期间相同的固定映射，则扩展环境可定义 `P̃(s'|s,ã)=P(s'|s,g(s,ã))`、`R̃(s,ã)=R(s,g(s,ã))`；在 auxiliary policy 上按原始 `ã` 计算 ratio 仍有正确的采样概率对象。此推导以 [genpo-2025](bibliography.md#genpo-2025) v4 §4.2 的 reformulated MDP 为基础，不是论文做过 residual 实验的声明。

【机制相关】【推测】固定 base controller、固定 residual scale、固定 clipping 或安全映射不会因非可逆而自动使 PPO 失效。例如 `u=clip(b(s)+c·(x+y)/2)` 可作为上述 `g`，条件是 `b`、`c` 与约束在当前数据收集及 update 中不随待更新参数变化，并保存原始 `ã`、old log-prob 与 conditioning observation；该解释结合 [residual-rl-2018](bibliography.md#residual-rl-2018) 的 signal superposition 和 GenPO 的扩展 MDP，属于适配推导。

【机制相关】【推测】被否定的是把 auxiliary likelihood 当作执行动作密度的解释，而不是 residual composition 本身。平均、clipping 和 contact-dependent controller 都可能把多个 auxiliary action 映到同一个执行动作，因此 `πθ(ã|s)` 不能直接冒充 `pθ(u|s)`，auxiliary entropy 也不能直接称为 actuator exploration entropy；推断来源是 [genpo-2025](bibliography.md#genpo-2025) v4 §4.2 的 many-to-one 平均映射。

【需新证据】【推测】如果 base controller 或 action mapping 与 actor 同时学习，就必须重新分析参数相关的 transition 与记录约定。带内部状态的 filter/controller 还需把其状态纳入环境描述；固定映射推导不覆盖更改 reference、controller 或 safety filter 后继续复用旧 rollout 的情形。面向 REGRIND 的 residual GenPO 因而只是适配假设，不能从 [genpo-2025](bibliography.md#genpo-2025) 或 [residual-rl-2018](bibliography.md#residual-rl-2018) 推出训练收益。

## GenPO 与 DPPO 对照

【论文直接验证】DPPO 已提供 on-policy diffusion policy optimization，因此不把 GenPO 写成首个能做 on-policy diffusion RL 的方法。[dppo-2024](bibliography.md#dppo-2024) v3 §4.1–4.2 明确构造 diffusion MDP 并应用 PPO；[genpo-2025](bibliography.md#genpo-2025) v4 abstract 的优先性措辞不作为本导读结论，GenPO 的差异应定位到其具体 auxiliary invertibility、entropy/KL 接口。

【论文直接验证】likelihood 对象不同，但都绕开最终执行动作 marginal density。[genpo-2025](bibliography.md#genpo-2025) v4 §4.2–4.3、Eq. (7)–(11) 对完整 `ã=(x,y)` 求密度；[dppo-2024](bibliography.md#dppo-2024) v3 §4.1、Eq. (4.1)–(4.4) 对扩展 state `(s,a^{k+1})` 下的 denoising action `a^k` 求 Gaussian transition likelihood，§4.2 Eq. (4.5)–(4.8) 用该对象形成 PPO 更新与 denoising-discounted advantage。DPPO §4.3 还区分 sampling-noise 与 likelihood-noise 的最小值设置，复现时不能省略这些实际修正。

【论文直接验证】初始化来源应按评估重心而非能力上限区分。[genpo-2025](bibliography.md#genpo-2025) v4 §5.1 与 Algorithm 1 描述 benchmark 中从环境采样训练，未报告 demonstration pretraining；[dppo-2024](bibliography.md#dppo-2024) v3 §5 主要先以 demonstrations 预训练再 fine-tune，但同时指出 Appendix C 有 from-scratch 结果。因此不能说 DPPO 必须有示范，或 GenPO 已支持任意 pretrained Diffusion Policy checkpoint 的直接接入。

【论文直接验证】action horizon 与 denoising horizon 是两个维度。[genpo-2025](bibliography.md#genpo-2025) v4 Algorithm 1 每次生成一个环境动作，Appendix B Table 10 没有 action-chunk 配置；[dppo-2024](bibliography.md#dppo-2024) v3 §3 定义预测长度 `T_p` 与执行长度 `T_a≤T_p`，§4.3 讨论 UNet 下更长预测、较短执行。GenPO 的 flow steps 与 DPPO 的 denoising steps 都不能当作 robot action chunk length。

【论文直接验证】探索机制必须区分生成噪声、正则项和经验解释。[genpo-2025](bibliography.md#genpo-2025) v4 §4.2–4.3 使用独立双噪声、mixing、entropy 和 compression，§5.2 在 Ant 做相关消融；[dppo-2024](bibliography.md#dppo-2024) v3 §4.3 用 stochastic denoising/DDIM、noise floor，§6 在 Avoid 任务研究靠近 pretraining manifold 的 structured exploration，且承认从零训练时未观察到相对 Gaussian 的显著探索优势。这些结果不能直接推导出接触模式探索优势。

【论文直接验证】两篇论文没有提供可直接排名的统一 compute benchmark。[genpo-2025](bibliography.md#genpo-2025) v4 §6 指出计算/内存与 Jacobian determinant 开销，Appendix D.5 的 Ant 实验报告 inference 比 Gaussian 慢、比所比 diffusion baseline 快，并给出 2.577 ms 的特定测量；[dppo-2024](bibliography.md#dppo-2024) v3 §4.3 讨论末几步 fine-tuning 和 DDIM 减少时间/内存。硬件、batch、任务、denoising steps 与实现不同，不能据此宣称 GenPO 比 DPPO 更快。

【论文直接验证】DPPO 的时间开销应以分任务、分架构记录为准，而非把概述数字当作上限。[dppo-2024](bibliography.md#dppo-2024) v3 §5 概述相对其他 policy parameterization 可慢约 2×，但 Appendix D Table A3 的 Lift 单轮 wall-clock 是 Gaussian-MLP 27.7 s、DPPO-MLP 35.6 s、DPPO-UNet 83.6 s，UNet 相对 Gaussian 已超过该倍率；Appendix D 明确存在架构和任务差异，本导读据具体配置保留该差异，不据概述外推。

## 仿真训练接入点

【论文直接验证】GenPO 的直接 dexterous 证据限于 Shadow Hand cube reorientation。[genpo-2025](bibliography.md#genpo-2025) v4 §5.1、Appendix A 列出的 8 个 benchmark 为 `Isaac-Ant-v0`、`Isaac-Humanoid-v0`、`Isaac-Lift-Cube-Franka-v0`、`Isaac-Repose-Cube-Shadow-Direct-v0`、`Isaac-Velocity-Flat-Anymal-D-v0`、`Isaac-Velocity-Rough-Unitree-Go2-v0`、`Isaac-Velocity-Rough-H1-v0` 与 `Isaac-Quadcopter-Direct-v0`。它们不是 8 项灵巧操作任务，Table 1 的 episodic return 也不是跨任务统一成功率。

【机制相关】【推测】IsaacLab Shadow Hand 是自然试验场，因为同一任务中可以先固定环境、奖励与 action semantics 再替换 Gaussian/GenPO actor。[genpo-2025](bibliography.md#genpo-2025) v4 Appendix A 给出的 157 维 state、20 维 action 允许检查 doubled auxiliary dimension；【需新证据】若更换 observation、初始 grasp、物体形状或 retargeting reference，就已改变实验问题，需重新建立 baseline，不能沿用论文 return 当作预期效果。

【需新证据】【推测】REGRIND 中可候选的接入点包括 reference-conditioned GenPO residual 和 demonstration-pretrained DPPO，但二者都只是适配假设。前者需按固定 mapping 约定保存 auxiliary action，后者需先把轨迹转为匹配 chunk/observation 的训练数据；分别依据 [genpo-2025](bibliography.md#genpo-2025) v4 §4 与 [dppo-2024](bibliography.md#dppo-2024) v3 §3–4 的接口相关性，不承诺 tracking、接触稳定性或样本效率提升。

【需新证据】【推测】观测接口必须独立于 actor 替换进行审计。GenPO v4 Appendix A 未报告完整 privileged-state split、history/recurrence、感知延迟或 tactile input；Appendix C 的 diffusion timestep embedding 不是时间观测记忆。DPPO v3 §3、§5 支持 POMDP 表述与 pixel input，但同样不构成 tactile dexterous 验证；应先固定可部署 observation，再评估 history、noise 与 delay，依据见 [genpo-2025](bibliography.md#genpo-2025) 与 [dppo-2024](bibliography.md#dppo-2024)。

## 真机部署与在线 fine-tuning

【论文直接验证】zero-shot sim-to-real 与真机在线学习必须分开记录。[dppo-2024](bibliography.md#dppo-2024) v3 §5.4 的 One-leg hardware evaluation 是无 real-data fine-tuning/co-training 的 zero-shot 部署；[genpo-2025](bibliography.md#genpo-2025) v4 §5、Appendix A 的实验均为仿真，真实机器人在线 fine-tuning 未报告，不能把其讨论中的 deployment potential 写成真机成果。

【需新证据】【推测】真机在线 fine-tuning 需要新的交互预算、reset 方式和安全评估，而非把仿真吞吐数字缩放即可。应测真实闭环 latency、残差幅度、接触冲击、掉落/急停与人工恢复成本，并固定或记录所有执行 mapping；[zhu-2018](bibliography.md#zhu-2018) 提供早期真机 RL 参照，但不能证明 diffusion on-policy 的在线成本可接受。

【需新证据】【推测】进入真机前的验收节点应是概率记录正确、受控仿真扰动通过、执行接口一致，再开展限幅部署评估。该顺序由 [genpo-2025](bibliography.md#genpo-2025) 的 auxiliary 概率约定与 [dppo-2024](bibliography.md#dppo-2024) 的 sim-to-real 证据边界推导，不是安全认证，也不替代硬件负责人制定的安全流程。
