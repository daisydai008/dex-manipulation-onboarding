# REGRIND 与生成式策略的对接思路

本章讨论生成式策略可以怎样用于 retargeting 训练，以及每种尝试需要比较什么。总体选型见 [导读](../README.md)，论文版本与实验范围见 [注释书目](bibliography.md)。

## 背景

REGRIND 的项目背景是 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练：先把人类运动转换成机器人参考轨迹，再通过交互学习修正执行中的偏差。这一描述沿用 [03 的项目背景](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)，当前源码与部署状态需另行核查。

参考轨迹贴合人类动作后，还需通过接触稳定性实验验证机器人执行能力。生成式策略可以用于学习控制修正量、生成连续多步动作，也可以作为训练扰动的候选模型；以下分别说明已有论文验证了什么，以及 REGRIND 仍需进行什么试验。本章只讨论方法接口，不含硬件选型、排期与分工，那些在 REGRIND 侧文档。

## 可插入生成式 actor 的三个接口

### 位置级 reference 之后的 residual

Residual RL 用已有 controller 处理可建模的控制部分，再让 RL 学习修正量。[Residual RL](bibliography.md#residual-rl-2018) 在真机 block assembly 中验证了这种控制叠加；[MoDex](bibliography.md#modex-2026) 则提供 diffusion policy 经 DPPO fine-tuning 后 zero-shot 部署到 Allegro 的参照；其任务范围为顺序抓取，residual 控制与真机在线训练需另行验证。

一种可行做法是保留 reference 与 base controller，让生成式 actor 只输出 residual。试验应先记录 base-only 和 Gaussian residual 的结果，再比较生成式 residual，保持 reference、residual scale、执行限制和测试初始状态一致；同时记录任务成功率、修正幅度与饱和率，区分 reference 不可执行与 residual 控制不足。

### 多步 action chunk 生成

Action chunk 是一次预测的一段连续动作，执行其中若干步后再根据新观测预测。[DPPO](bibliography.md#dppo-2024) v3 §3、§4.3 讨论 action horizon 与 denoising-step fine-tuning，[DexUMI](bibliography.md#dexumi-2025) 则以 diffusion policy 预测多步机器人动作并进行真机灵巧手实验；前者提供更新方法，后者提供动作序列部署的参照。

一种可行做法是从单步修正扩展为一段 reference-conditioned residual。试验应先固定单步方案，再改变预测长度与实际执行长度，记录接触恢复、任务成功率和推理延迟；延长每次执行的动作段时，还需检查策略能否及时响应滑落或接触变化，并将 action chunk 中的控制步数与环境交互次数分别统计。

### 部署噪声模型标定的扰动生成

部署论文提供了研究数据变化与机器人形态变化的参照；生成式噪声模型需要单独标定和验证。[DexVLA](bibliography.md#dexvla-2025) 研究跨形态的 diffusion action expert，[DexWild](bibliography.md#dexwild-2025) 研究人手与机器人数据联合训练及环境泛化。

此接口可先用同步记录标定部署观测误差，再比较经验噪声采样与生成式扰动模型。这属于训练数据或环境侧的改动，控制 actor 保持不变；试验应固定 policy、reference 和测试分布，检查扰动的时间相关性、取值范围与闭环成功率。生成样本的适用范围由实测误差数据决定。

## 接口的概率与记录约定

执行命令与 policy 采样变量需要分别保存。PPO ratio 使用原始采样变量，Residual 相加、幅度缩放与 clipping 后的 command 单独保存用于执行核对；固定 controller 时的条件见 [04 固定执行 mapping](04-onpolicy-diffusion-interface.md#固定执行-mapping)，DPPO 与可逆模型各自需要的记录见 [04 Rollout 记录](04-onpolicy-diffusion-interface.md#rollout-记录)。

Reference 的数据检查应先于 actor 比较。坐标系、joint order、时间戳、物体状态和实际执行动作的记录见 [03 数据记录与执行检查](03-retargeting-to-policy.md#数据记录与执行检查)，接触与 controller 可执行性检查见 [03 接触可行性与动力学鸿沟](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。
