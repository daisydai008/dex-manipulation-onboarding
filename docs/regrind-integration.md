# REGRIND 与生成式策略的对接思路

本章讨论生成式策略可以怎样用于 retargeting 训练，以及每种尝试需要比较什么。总体选型见 [导读](../README.md)，论文版本与实验范围见 [注释书目](bibliography.md)。

## 背景

REGRIND 的项目背景是 Drake 位置级 retargeting、residual RL 与 Isaac 并行训练：先把人类运动转换成机器人参考轨迹，再通过交互学习修正执行中的偏差。这一描述沿用 [03 的项目背景](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)，不是对当前源码或部署状态的审计。

参考轨迹贴合人类动作，不等于机器人能稳定完成接触任务。生成式策略可以用于学习控制修正量、生成连续多步动作，也可以作为训练扰动的候选模型；以下分别说明已有论文验证了什么，以及 REGRIND 仍需进行什么试验。本章只讨论方法接口，不含硬件选型、排期与分工，那些在 REGRIND 侧文档。

## 可插入生成式 actor 的三个接口

### 位置级 reference 之后的 residual

Residual RL 用已有 controller 处理可建模的控制部分，再让 RL 学习修正量。[Residual RL](bibliography.md#residual-rl-2018) 在真机 block assembly 中验证了这种控制叠加；[MoDex](bibliography.md#modex-2026) 则提供 diffusion policy 经 DPPO fine-tuning 后 zero-shot 部署到 Allegro 的参照，但它的顺序抓取实验在本书目中未记录为 residual 控制，也不是在真机上在线训练。

【推测】【需新证据】REGRIND 的适配假设是保留 reference 与 base controller，让生成式 actor 只输出 residual。试验应先记录 base-only 和 Gaussian residual 的结果，再比较生成式 residual，保持 reference、residual scale、执行限制和测试初始状态一致；同时记录任务成功率、修正幅度与饱和率，区分 reference 不可执行与 residual 控制不足。

### 多步 action chunk 生成

Action chunk 是一次预测的一段连续动作，执行其中若干步后再根据新观测预测。[DPPO](bibliography.md#dppo-2024) v3 §3、§4.3 讨论 action horizon 与 denoising-step fine-tuning，[DexUMI](bibliography.md#dexumi-2025) 则以 diffusion policy 预测多步机器人动作并进行真机灵巧手实验；前者提供更新方法，后者提供动作序列部署的参照。

【推测】【需新证据】REGRIND 可以尝试生成一段 reference-conditioned residual，而不只生成当前控制步的修正量。试验应先固定单步方案，再改变预测长度与实际执行长度，记录接触恢复、任务成功率和推理延迟；若每次执行的动作段更长，还需检查策略是否仍能及时响应滑落或接触变化，不能把 action chunk 数量直接当作环境交互次数。

### 部署噪声模型标定的扰动生成

部署论文提供了研究数据变化与机器人形态变化的参照，但不等于验证了生成式噪声模型。[DexVLA](bibliography.md#dexvla-2025) 研究跨形态的 diffusion action expert，[DexWild](bibliography.md#dexwild-2025) 研究人手与机器人数据联合训练及环境泛化；本书目所记录的两篇证据都不能支持“用 diffusion 生成部署扰动已经有效”的结论。

【推测】【需新证据】此接口的适配假设是先用同步记录标定部署观测误差，再比较经验噪声采样与生成式扰动模型。这属于训练数据或环境侧的改动，不是替换控制 actor；试验应固定 policy、reference 和测试分布，检查扰动的时间相关性、取值范围与闭环成功率。没有实测误差数据时，不把生成样本当作真实部署噪声。

## 接口的概率与记录约定

执行命令与 policy 采样变量需要分别保存。Residual 相加、幅度缩放与 clipping 后的 command 不能替代 PPO ratio 使用的原始变量；固定 controller 时的条件见 [04 固定执行 mapping](04-onpolicy-diffusion-interface.md#固定执行-mapping)，DPPO 与可逆模型各自需要的记录见 [04 Rollout 记录](04-onpolicy-diffusion-interface.md#rollout-记录)。

Reference 的数据检查应先于 actor 比较。坐标系、joint order、时间戳、物体状态和实际执行动作的记录见 [03 链条与数据契约](03-retargeting-to-policy.md#链条与数据契约)，接触与 controller 可执行性检查见 [03 接触可行性与动力学鸿沟](03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。

## 检查与接受范围

检查器只用 Python 标准库，不写 cache、日志或 fixture。交付文件清单显式登记在 `scripts/check_links.py` 的 `FILES` 集合，新文件须登记加入，编辑器与运行时辅助文件（如 `.vscode/`、`.pi-subagents/`、`.gitignore`）不属于交付树，运行检查前须从树中删除，本地忽略规则放全局 gitignore 或 `.git/info/exclude`。`--lint` 不联网，按内嵌身份映射锚定原有 36 篇 core/extended 身份，新增条目经登记与 arXiv 核验后接受（当前 43 条、19 core、24 extended）；完整模式核验记录版本的 arXiv API title/ID、书目外链、全部交付 Markdown 中的官方工程文档链接与内部 anchor。网络请求单次 15 秒、至多重试 2 次、同 host 间隔至少 1 秒、总联网预算 15 分钟；退出码为 0 全部通过、2 内容失败、3 网络未完成，内容失败优先，只有 failed=0 且 unverified=0 才通过。

```bash
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py --lint
python3 scripts/check_links.py
```

自动检查通过不等于内容接受。条件推导、DPPO 机制与选型建议仍需人工核对；执行者交回与独立内容核验分开，不以链接可达代替技术判断。
