# Dexterous manipulation 文献导读

本仓库为 diffusion × on-policy RL 与 retargeting × residual RL 两类研究者提供共享的文献入口。范围是灵巧操作的问题结构、数据到闭环策略的转换、GenPO/DPPO 的概率接口，以及可隔离评估的 PPO 增强方向；不包含训练代码，也不承诺任何方案对 REGRIND 有收益。

## 使用与证据约定

文献库收录 37 篇作品，其中 20 篇 core、17 篇 extended；不要求全部先读。逐篇四问注释集中于 [bibliography](docs/bibliography.md)，主题章节只负责跨文献综合，稳定 paper ID 不随标题或年份勘误变化。

适配分析使用三级标签，不能把机制可组合性当作已验证收益。【论文直接验证】限定于论文实际任务与指标；【机制相关】表示接口在概念上相关，不表示组合已有实验；【需新证据】表示目标任务、硬件或组合尚待验证。除 GenPO v4 与 DPPO v3 的指定全文之外，其他论文只使用 abstract 和公开元数据；越出该证据范围的陈述另标【推测】。“未报告”始终表示本导读查阅的证据范围未报告，而不是断言整篇论文没有该信息。

## 同事 A 路径

这条路径以 diffusion × on-policy RL 为主线，用 6 篇论文完成任务、数据与概率接口的最小对齐。

1. [openai-inhand-2020](docs/bibliography.md#openai-inhand-2020)：要解决的问题是 in-hand reorientation 与真机迁移需要什么；对应 [问题结构](docs/01-problem-structure.md#任务谱系)。
2. [dextreme-2022](docs/bibliography.md#dextreme-2022)：要解决的问题是 vision policy 与 privileged state 的证据如何区分；对应 [观测维度](docs/01-problem-structure.md#观测与部分可观测性)。
3. [diffusion-policy-2023](docs/bibliography.md#diffusion-policy-2023)：要解决的问题是为什么从单动作分布转向 conditional action generation；对应 [diffusion policy 方法族](docs/02-method-landscape.md#diffusion-policy)。
4. [dppo-2024](docs/bibliography.md#dppo-2024)：要解决的问题是如何不求最终动作边缘密度而进行 on-policy update；对应 [GenPO 与 DPPO 对照](docs/04-genpo-interface.md#genpo-与-dppo-对照)。
5. [genpo-2025](docs/bibliography.md#genpo-2025)：要解决的问题是 exact likelihood 属于哪个随机变量；对应 [auxiliary action 接口](docs/04-genpo-interface.md#概率对象与-rollout-约定)。
6. [implementation-matters-2020](docs/bibliography.md#implementation-matters-2020)：要解决的问题是如何将 policy class 收益与实现收益分开；对应 [update/estimation 层](docs/05-ppo-enhancement.md#updateestimation-层)。

## Retargeting 路径

这条路径以 motion 到 executable policy 为主线，用 7 篇论文区分数据、reference、residual 与课程接口。

1. [dexcap-2024](docs/bibliography.md#dexcap-2024)：要解决的问题是 mocap、IK 与 policy-ready 数据之间缺什么；对应 [数据管线](docs/03-retargeting-to-policy.md#遥操作与数据管线)。
2. [dapg-2018](docs/bibliography.md#dapg-2018)：要解决的问题是 demonstrations 如何帮助 RL，而不是替代环境交互；对应 [BC 用途](docs/03-retargeting-to-policy.md#用途一bc-数据)。
3. [deepmimic-2018](docs/bibliography.md#deepmimic-2018)：要解决的问题是 tracking reference 如何与 task objective 共存；对应 [tracking 与 RSI](docs/03-retargeting-to-policy.md#用途二tracking-reference-与-rsi)。
4. [residual-rl-2018](docs/bibliography.md#residual-rl-2018)：要解决的问题是 base control 与 residual 的职责如何划分；对应 [动力学鸿沟](docs/03-retargeting-to-policy.md#接触可行性与动力学鸿沟)。
5. [demostart-2024](docs/bibliography.md#demostart-2024)：要解决的问题是示范是否可只用于 reset/curriculum；对应 [reward/reset 用途](docs/03-retargeting-to-policy.md#用途三reward-与-reset-信号)。
6. [sapg-2024](docs/bibliography.md#sapg-2024)：要解决的问题是增加并行环境为何不等于更有效学习；对应 [demonstration/residual 集成层](docs/05-ppo-enhancement.md#demonstrationresidual-集成层)。
7. [ppo-2017](docs/bibliography.md#ppo-2017)：要解决的问题是增强方案最终改变哪部分 surrogate update；对应 [评估顺序](docs/05-ppo-enhancement.md#评估顺序与停止条件)。

## 文件导航

- [01 问题结构](docs/01-problem-structure.md)：任务谱系、观测、硬件与 benchmark 的比较边界。
- [02 方法全景](docs/02-method-landscape.md)：五个交叉方法族及其组合关系。
- [03 Retargeting 到 policy](docs/03-retargeting-to-policy.md)：轨迹三种用途、接触可行性与数据管线。
- [04 GenPO 接口](docs/04-genpo-interface.md)：auxiliary likelihood、DPPO 对照、仿真与真机适配边界。
- [05 PPO 增强](docs/05-ppo-enhancement.md)：三层候选、所需信号、修改接口与隔离评估。
- [注释书目](docs/bibliography.md)：每篇的身份、版本、证据与四问。
- [检查器](scripts/check_links.py)：本地结构、条目、相对链接、风格与联网元数据验证；协作边界见 [任务记录](TASK-RECORD.md)。

## 检查与接受边界

检查器仅依赖 Python 标准库，不写 cache、日志或 fixture。`--lint` 不联网；完整模式核验每条记录版本的 arXiv API title/ID、bibliography 外链与内部 anchor，单请求 15 秒、至多重试 2 次、同 host 间隔至少 1 秒、总联网预算 15 分钟；退出码为 0 全部通过、2 内容失败、3 网络未完成，内容失败优先。

```bash
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py --lint
python3 scripts/check_links.py
```

自动检查通过不等于内容接受。GenPO/DPPO 机制与选型论断仍需人工对照指定版本，最终接受由 Kimi 的独立核验和只读 review 决定。
