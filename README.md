# Dexterous manipulation 文献导读

本导读按“已有资源 → 起步路线 → 预期产出”组织研究选择。有 simulator 和 reward、没有示范时，先建立 Gaussian PPO baseline，产出任务指标与失败分布；有成功 robot demonstrations 时，先验证 imitation 闭环，产出数据覆盖与恢复能力记录；有 reference/base controller 时，先检查物理可行性，再比较 base-only 与 Gaussian residual，产出控制分工和 residual 作用范围。这些是【机制相关】【需新证据】的实验建议，不是训练收益承诺，具体选择见 [02 决策支持](docs/02-method-landscape.md)。

## Diffusion 与 on-policy RL 阅读路径

这条路径用 6 篇论文对齐任务、数据、更新与概率对象；各步标注的切入点不代表该论文已解决所有灵巧操作设置。

1. [openai-inhand-2020](docs/bibliography.md#openai-inhand-2020)：明确 in-hand reorientation 与真机迁移的任务边界；对应 [01 任务谱系](docs/01-problem-structure.md#任务谱系)。
2. [dextreme-2022](docs/bibliography.md#dextreme-2022)：区分 vision policy 与 privileged state 的证据；对应 [01 观测维度](docs/01-problem-structure.md#观测与部分可观测性)。
3. [diffusion-policy-2023](docs/bibliography.md#diffusion-policy-2023)：理解 conditional action generation 的数据前提；对应 [02 diffusion policy 短卡](docs/02-method-landscape.md#diffusion-policy)。
4. [ppo-2017](docs/bibliography.md#ppo-2017)：明确新旧策略 ratio 必须比较同一随机变量；对应 [04 概率对象](docs/04-onpolicy-diffusion-interface.md#概率对象)。
5. [dppo-2024](docs/bibliography.md#dppo-2024)：理解 denoising-step PPO 与 demonstration fine-tuning，而不要求最终动作的边缘密度；对应 [04 rollout 记录](docs/04-onpolicy-diffusion-interface.md#rollout-记录)。
6. [implementation-matters-2020](docs/bibliography.md#implementation-matters-2020)：区分 policy class 收益与实现收益；对应 [05 update/estimation 层](docs/05-ppo-enhancement.md#updateestimation-层)。

## Retargeting 与 residual RL 阅读路径

这条路径用 7 篇论文区分数据、reference、residual 与课程接口，目标是把 motion 转为可评估的闭环策略。

1. [dexcap-2024](docs/bibliography.md#dexcap-2024)：检查 mocap、IK 与 policy-ready 数据之间缺什么；对应 [03 数据管线](docs/03-retargeting-to-policy.md#遥操作与数据管线)。
2. [dapg-2018](docs/bibliography.md#dapg-2018)：理解 demonstrations 如何帮助 RL，而不是替代环境交互；对应 [03 BC 用途](docs/03-retargeting-to-policy.md#用途一bc-数据)。
3. [deepmimic-2018](docs/bibliography.md#deepmimic-2018)：区分 tracking reference 与 task objective；对应 [03 tracking 与 RSI](docs/03-retargeting-to-policy.md#用途二tracking-reference-与-rsi)。
4. [residual-rl-2018](docs/bibliography.md#residual-rl-2018)：划分 base control 与 residual 的职责；对应 [03 动力学鸿沟](docs/03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。
5. [demostart-2024](docs/bibliography.md#demostart-2024)：判断示范是否只用于 reset/curriculum；对应 [03 reward/reset 用途](docs/03-retargeting-to-policy.md#用途三reward-与-reset-信号)。
6. [sapg-2024](docs/bibliography.md#sapg-2024)：检查增加并行环境为何不等于更有效学习；对应 [05 数据聚合](docs/05-ppo-enhancement.md#split-and-aggregate-数据聚合)。
7. [ppo-2017](docs/bibliography.md#ppo-2017)：明确增强方案改变哪部分 surrogate update；对应 [05 评估顺序](docs/05-ppo-enhancement.md#评估顺序与停止条件)。

## 使用与证据约定

文献库收录 36 篇作品，其中 19 篇 core、17 篇 extended；不要求全部先读。逐篇四问注释集中于 [bibliography](docs/bibliography.md)，主题章节负责跨文献综合，稳定 paper ID 不随标题或年份勘误变化。本仓库不包含训练代码，REGRIND 插入点均为待验证的适配假设。

适配建议不等于已有实验结果。【论文直接验证】限定于所引论文实际机制、任务与指标；【机制相关】说明接口相关而非组合已验证；【需新证据】标出目标任务、硬件或组合尚待验证。除 DPPO v3 的指定全文外，其他论文仅使用所记录版本的 abstract 与公开元数据，越出该范围另标【推测】；“未报告”仅指本导读查阅的证据范围未报告。

推导与工程事实另列证据类别。【条件推导】只在列明前提下成立，不代表任意 diffusion sampler 满足条件或已取得收益；【官方工程文档】只支持固定版本的 registry/interface 事实，不支持 actor-gain 结论。完整约定见 [书目证据说明](docs/bibliography.md#证据约定)。

## 文件导航

- [01 问题结构](docs/01-problem-structure.md)：确定任务、观测与 benchmark 比较边界。
- [02 方法选择](docs/02-method-landscape.md)：与 README 一起选方向，按资源和可观察失败信号选择五族候选。
- [03 Retargeting 到 policy](docs/03-retargeting-to-policy.md)：检查轨迹用途、接触可行性与执行数据契约。
- [04 On-policy diffusion 接口](docs/04-onpolicy-diffusion-interface.md)：定义概率对象、rollout 记录、执行 mapping 与诊断任务协议。
- [05 PPO 增强](docs/05-ppo-enhancement.md)：从失败信号选择排查项，设计隔离实验。
- [注释书目](docs/bibliography.md)：维护 36 篇作品的身份、版本、证据与四问。
- [检查器](scripts/check_links.py)：检查 8 个交付文件的结构、条目、相对链接、机械风格及外部来源。

## 检查与接受边界

检查器只用 Python 标准库，不写 cache、日志或 fixture。检查器冻结恰好 8 个交付文件，编辑器与运行时辅助文件（如 `.vscode/`、`.pi-subagents/`、`.gitignore`）不属于交付树，运行检查前须从树中删除；需要本地忽略时，把规则放进全局 gitignore 或 `.git/info/exclude`。`--lint` 不联网，按内嵌身份映射要求 36 条、19 core、17 extended、新增 0；完整模式核验记录版本的 arXiv API title/ID、书目外链、全部交付 Markdown 中的官方工程文档链接与内部 anchor。网络请求单次 15 秒、至多重试 2 次、同 host 间隔至少 1 秒、总联网预算 15 分钟；退出码为 0 全部通过、2 内容失败、3 网络未完成，内容失败优先，只有 failed=0 且 unverified=0 才通过。

```bash
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py --lint
python3 scripts/check_links.py
```

自动检查通过不等于内容接受。条件推导、DPPO 机制与选型建议仍需人工核对；执行者交回与独立内容核验分开，不以链接可达代替技术判断。
