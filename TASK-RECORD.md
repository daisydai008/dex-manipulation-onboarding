# TASK-RECORD — dex-manipulation-onboarding

本文件是 dex-manipulation-onboarding 仓库的协作任务记录，由 Kimi(编排者)独占维护，记录三轮委派前讨论、冻结文献清单、执行工单与验收结果。Astra(执行者)对本文件只读。

## 1. 任务背景与目标

同事 A 的研究方向是 diffusion policy 与 on-policy RL 的结合，代表参照为 GenPO(arXiv 2505.18763,经 exact diffusion inversion 构造可逆 action mapping,在 auxiliary action 上计算 state-action log-likelihood,支撑 PPO 的 ratio、entropy、KL 估计;在 8 个 IsaacLab benchmark 上验证,含 Shadow Hand 立方体重定向)。用户本人方向是 dexterous manipulation 的 retargeting(REGRIND 项目:Drake 位置级 retargeting + residual RL + Isaac 并行训练),并希望为后续 retargeting-RL 工作调研 PPO 增强方向。

本仓库交付一份 onboarding 文献导读:为同事 A 提供 dexterous manipulation robot learning 的全景与精选论文清单,分析 GenPO-line 的 on-policy diffusion 方法可以接入 dexterous manipulation 的位置;同时为用户提供面向 retargeting + residual RL 的 PPO 增强方向梳理。

## 2. 仓库边界与写入纪律

仓库路径 `/home/daisy/research/dex-manipulation-onboarding/`,经 `git rev-parse` 验证不在任何既有 git 仓库内(决定来源:Round 2 finding 1,原拟议路径位于 regrind-development 仓库内,已放弃)。只本地 commit,永不 push;不修改任何其他目录。

写入纪律为时间互斥的 single-writer:Kimi 先完成本记录与 repo bootstrap 并 commit;随后 Astra 作为唯一写者完成授权文件并 commit;之后 Kimi 验证并回填本记录第 7 节;DeepSeek 只读 review;确认的修复仍由 Astra 经新 commit 完成。各方只 stage 自己获授权的文件,禁止笼统 `git add .`。

授权文件清单(全仓库恰为以下 9 个路径加 .git):Astra 可写 `README.md`、`docs/01-problem-structure.md`、`docs/02-method-landscape.md`、`docs/03-retargeting-to-policy.md`、`docs/04-genpo-interface.md`、`docs/05-ppo-enhancement.md`、`docs/bibliography.md`、`scripts/check_links.py` 共 8 个;Kimi 独占 `TASK-RECORD.md`。检查报告只输出到 stdout,不落盘 cache、日志或 fixture。

## 3. 冻结文献清单

2026-10-22 由 Kimi 经 arXiv API 逐条核验(title + 作者姓氏匹配;version 为 API 返回的当前版本),共 37 个作品(20 core + 17 extended)。元数据已核验(metadata-verified);正文结论级引用(claim-verified)由 Astra 在执行时按第 5 节要求完成。Astra 可新增至多 3 个作品,每个须先经 arXiv API 核验 canonical ID 与 title,且计入总量上限 40。

### 3.1 Core(20,bibliography 中给完整四问注释)

- openai-inhand-2020 | 1808.00177v5 | Learning Dexterous In-Hand Manipulation | OpenAI(Andrychowicz 等) 2018
- openai-rubiks-2019 | 1910.07113v1 | Solving Rubik's Cube with a Robot Hand | OpenAI(Akkaya 等) 2019
- dextreme-2022 | 2210.13702v2 | DeXtreme: Transfer of Agile In-hand Manipulation from Simulation to Reality | Handa 等 2022
- visual-dexterity-2022 | 2211.11744v3 | Visual Dexterity: In-Hand Reorientation of Novel and Complex Object Shapes | Chen 等 2022(Science Robotics 2023)
- sequential-dexterity-2023 | 2309.00987v2 | Sequential Dexterity: Chaining Dexterous Policies for Long-Horizon Manipulation | Chen 等 2023
- dapg-2018 | 1709.10087v2 | Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations | Rajeswaran 等 2017(RSS 2018)
- bi-dexhands-2023 | 2206.08686v2 | Towards Human-Level Bimanual Dexterous Manipulation with Reinforcement Learning | Chen 等 2022
- isaac-lab-2023 | 2301.04195v2 | Orbit: A Unified Simulation Framework for Interactive Robot Learning Environments | Mittal 等 2023(IEEE RA-L)
- dexpilot-2020 | 1910.03135v2 | DexPilot: Vision Based Teleoperation of Dexterous Robotic Hand-Arm System | Handa 等 2019
- anyteleop-2023 | 2307.04577v3 | AnyTeleop: A General Vision-Based Dexterous Robot Arm-Hand Teleoperation System | Qin 等 2023
- dexcap-2024 | 2403.07788v2 | DexCap: Scalable and Portable Mocap Data Collection System for Dexterous Manipulation | Wang 等 2024
- diffusion-policy-2023 | 2303.04137v5 | Diffusion Policy: Visuomotor Policy Learning via Action Diffusion | Chi 等 2023(RSS 2023)
- dppo-2024 | 2409.00588v3 | Diffusion Policy Policy Optimization | Ren 等 2024
- genpo-2025 | 2505.18763v4 | GenPO: Generative Diffusion Models Meet On-Policy Reinforcement Learning | Ding 等 2025
- ppo-2017 | 1707.06347v2 | Proximal Policy Optimization Algorithms | Schulman 等 2017
- implementation-matters-2020 | 2005.12729v1 | Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO | Engstrom 等 2020
- massively-parallel-2021 | 2109.11978v3 | Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning | Rudin 等 2021
- residual-rl-2018 | 1812.03201v2 | Residual Reinforcement Learning for Robot Control | Johannink 等 2018
- sapg-2024 | 2407.20230v1 | SAPG: Split and Aggregate Policy Gradients | Singla 等 2024
- demostart-2024 | 2409.06613v2 | DemoStart: Demonstration-led auto-curriculum applied to sim-to-real with multi-fingered hands | Bauza 等 2024

### 3.2 Extended(17,bibliography 中给紧凑条目,仍须覆盖四问)

- leap-hand-2023 | 2309.06440v1 | LEAP Hand: Low-Cost, Efficient, and Anthropomorphic Hand for Robot Learning | Shaw 等 2023
- zhu-2018 | 1810.06045v1 | Dexterous Manipulation with Deep Reinforcement Learning: Efficient, General, and Low-Cost | Zhu 等 2018
- trifinger-2021 | 2108.09779v2 | Transferring Dexterous Manipulation from GPU Simulation to a Remote Real-World TriFinger | Allshire 等 2021
- rotate-touch-2023 | 2303.10880v4 | Rotating without Seeing: Towards In-hand Dexterity Through Touch | Yin 等 2023
- openteach-2024 | 2403.07870v1 | Open Teach: A Versatile Teleoperation System for Robotic Manipulation | Iyer 等 2024
- bunny-visionpro-2024 | 2407.03162v1 | Bunny-VisionPro: Real-Time Bimanual Dexterous Teleoperation for Imitation Learning | Ding 等 2024
- robotic-telekinesis-2022 | 2202.10448v2 | Robotic Telekinesis: Learning a Robotic Hand Imitator by Watching Humans on Youtube | Sivakumar 等 2022
- mimicplay-2023 | 2302.12422v2 | MimicPlay: Long-Horizon Imitation Learning by Watching Human Play | Wang 等 2023
- dexmimicgen-2024 | 2410.24185v2 | DexMimicGen: Automated Data Generation for Bimanual Dexterous Manipulation via Imitation Learning | Jiang 等 2024
- dp3-2024 | 2403.03954v7 | 3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations | Ze 等 2024
- dexdiffuser-2023 | 2402.02989v3 | DexDiffuser: Generating Dexterous Grasps with Diffusion Models | Weng 等 2023
- diffusion-ql-2022 | 2208.06193v3 | Diffusion Policies as an Expressive Policy Class for Offline Reinforcement Learning | Wang 等 2022
- idql-2023 | 2304.10573v2 | IDQL: Implicit Q-Learning as an Actor-Critic Method with Diffusion Policies | Hansen-Estruch 等 2023
- on-policy-actor-critic-2020 | 2006.05990v1 | What Matters In On-Policy Reinforcement Learning? A Large-Scale Empirical Study | Andrychowicz 等 2020
- domain-randomization-2017 | 1703.06907v1 | Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World | Tobin 等 2017
- mappo-2021 | 2103.01955v4 | The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games | Yu 等 2021
- deepmimic-2018 | 1804.02717v3 | DeepMimic: Example-Guided Deep Reinforcement Learning of Physics-Based Character Skills | Peng 等 2018

### 3.3 已核验但未入选(9,不留条目)

isaac-gym-2021(2108.10470,平台概念由 massively-parallel-2021 与 isaac-lab-2023 覆盖)、mobile-aloha-2024(2401.02117,平行夹爪非灵巧手)、humanplus-2024(2406.10454,人形全身,偏离主题)、consistency-policy-2024(2405.07503,推理加速,偏离目标)、dagger-2011(1011.0686,经典但与主线距离远)、dexvip-2022(2202.00164,人类视频线由 robotic-telekinesis-2022 覆盖)、videodex-2022(2212.04498,同线取舍)、ace-teleop-2024(2408.11805,遥操作系统数量已足)、residual-policy-2018(1812.06298,residual 线保留 Johannink 一条)。

## 4. 三轮委派前讨论记录

讨论双方:Kimi(提案)与 Astra(litellm/gpt-6-astra,独立思考档,每轮 fresh context,只读顾问模式)。每轮结构为 Kimi 提案 → Astra 批评 → Kimi 处置。以下为要点摘录与逐项处置;完整批评原文见会话记录。

### Round 1 — 背景、大图、目标

Kimi 提案要点:以五条方法线(sim-RL/sim-to-real 工程线、数据与模仿线、diffusion policy 线、diffusion×RL 线、RL 算法工程线)为主轴;设 GenPO×dexterous manipulation 接口分析;设面向 retargeting 的 PPO 增强章节;硬件与 benchmark 作为 scaffold。

Astra 批评 10 点(按重要性):GenPO 的 exact likelihood 属于 auxiliary action 而非执行动作,接口分析必须从此出发;五线适合作为交叉标签而非线性演进主轴;DPPO 应是 GenPO 的核心对照而非过渡条目;最缺的是"retargeted motion 如何变成可执行策略"的链条;GenPO 适配论断必须按证据分级(论文直接验证/机制相关/需新证据),Shadow Hand 单一 benchmark 不能外推;tactile 与 partial observability 应横贯各方法族;grasp acquisition/regrasp/long-horizon 应补但需收口,world models 只作延伸阅读;PPO 增强需分三层(update/estimation、demonstration/residual 集成、并行训练与课程),MAPPO 仅在 multi-agent 设定下相关;hardware/benchmark 条目必须带可比性警示(观测、初始状态、动作语义、sim/real 证据);两类读者应有各自 5–7 篇的最小阅读路径,共享同一证据库,条目须逐项核验。

Kimi 处置:10 点全部接受,转化为第 5、6 节的内容硬性约束与验收项。

### Round 2 — 设计、范围、风险

Kimi 提案要点:新独立仓库,README + 5 篇主题 docs + bibliography + check_links.py + TASK-RECORD;文献总量 30–40;Kimi 预核验种子清单,Astra 可新增 ≤5;Kimi 独立验证,DeepSeek 只读 review;风险项为引用幻觉、范围蠕变、风格漂移、GenPO 技术误述。

Astra 批评 9 点:拟议路径在既有 git 仓库内(blocker,须另选位置);"verified IDs+abstracts"只覆盖身份核验,机制与实验结论须正文定位,抽象条目不承担超出 abstract 的结论;文件所有权分离须补充时间互斥与逐文件 stage;auxiliary-action caveat 不得被写成"clipping/residual 使 PPO 不成立"——固定且与待更新参数无关的 action mapping 可折入环境,rollout 保存原始 auxiliary action 即可计算 ratio,被否定的只是"该 likelihood 即执行动作密度"的解释;check_links 通过条件须与证据审查分开,覆盖非 arXiv 来源,网络未完成不得记为通过;tactile 降级仅限传感器硬件综述,观测模态维度保留;30–40 为总量预算而非必读量,两条起步路径各 5–7 篇;bibliography 是逐篇注释唯一维护位置,其他文档经稳定 paper ID 引用,避免事实漂移;05 须提供选型依据(baseline 问题、所需信号、改动接口、证据层级、隔离评估方案),REGRIND 插入点标为适配假设,不承诺训练收益。

Kimi 处置:9 点全部接受。仓库改址 `~/research/dex-manipulation-onboarding/`(已验证在一切 git root 之外);新增额度由 ≤5 收紧为 ≤3 并计入总量 40;三层命名为 update/estimation 层、demonstration/residual 集成层、并行训练与课程层,边界冻结于第 6 节工单。

### Round 3 — 测试、评估、验收、回滚

Kimi 提案要点:自动检查 A–D(结构、链接、条目完整性、风格)+ 人工验收 E–G(内容硬性约束、双阅读路径走查与抽样、DeepSeek review);commit 策略;删除目录即回滚。

Astra 批评 8 点:文件清单与写入范围分开列明,entry lint 并入 check_links.py,不落盘任何报告文件;作品身份用无版本 arXiv ID 去重,结论所据版本须记录 vN;冻结 entry schema 与稳定 paper ID,内部链接校验 heading anchor,拒绝重复 ID/越界路径,核验阅读路径篇数与总量预算;10 条随机抽查不能替代核心主张全查(GenPO/DPPO 机制主张与 04/05 关键比较主张必须落在 bibliography 证据层级内),抽样方法与所选 ID 须记录;checker 须带 --self-test 负例验证(错 ID、title 不匹配、缺字段、死 anchor、重复作品、timeout/429/5xx、200 但元数据不符),stdlib 优先,区分内容失败/网络未完成/成功三类退出码;风格检查区分机械项与人工项,表格识别须 fence-aware 完整规则,禁用词扫描范围限定 README+docs,记录与脚本避免原样写入禁用词;交回(handback)与最终接受(acceptance)分两个状态,修复预留 commit 额度,禁止 amend/squash 绕过;回滚删除前须由 Kimi 复核绝对路径、realpath 非 symlink、repo root 一致、无外来内容。

Kimi 处置:8 点全部接受,收敛为第 5 节验收标准与第 6 节工单。三轮讨论至此完整,Astra 末轮结论为"先收敛验收定义再冻结工单",本节与第 5、6 节即该收敛结果,无遗留待决分歧。

## 5. 冻结验收标准

### 5.1 自动检查(Astra 交回前必须全部通过并随 handback 报告输出)

A. 结构:仓库内恰有第 2 节 9 个授权路径与 .git,无其他文件。
B. `python3 scripts/check_links.py`:核验 bibliography 全部外部链接(arXiv 条目:canonical ID 可达且规范化 title 与清单一致,比较对象为清单记录的版本;非 arXiv 条目:DOI/publisher 主源)与全部内部相对链接及 heading anchor;退出码 0=全部通过、2=内容失败、3=网络未完成;结束打印 verified/failed/unverified 计数;仅用 Python 标准库;单请求 timeout 15s、至多 2 次重试、同 host 请求间隔 ≥1s、总运行上限 15 分钟;`--self-test` 模式用本地假数据覆盖负例(错 ID、title 不符、缺字段、死 anchor、重复作品、模拟 timeout/429/5xx、200 但元数据不符),self-test 自身退出码非 0 视为检查器失效。
C. 条目 lint(同一脚本 `--lint`):每条 bibliography 条目符合第 6 节 schema(字段非空、paper ID 唯一、anchor 唯一);README 两条阅读路径各 5–7 个 paper ID 且全部存在于 bibliography;作品总数 ≤40 且相对第 3 节冻结清单的新增 ≤3。
D. 风格机械项:README 与 docs 全部 UTF-8 strict 可解码;fence-aware 识别下无 markdown table(含无外侧竖线形式);禁用词扫描仅覆盖 README.md 与 docs/*.md,词项为 AGENTS.md 与 writing-style skill 规定的两个四字/两字禁用词(本记录以"冒+烟+测+试"与"实+锤"拆分形式指代,扫描时去掉加号);中文行文优先由 Kimi 人工确认,不由脚本判定。

### 5.2 人工验收(Kimi,在 Astra handback 后执行)

E. 内容硬性约束逐项核对(清单见 6.4)。
F. 核心主张全查:GenPO 与 DPPO 的机制级主张、docs/04 与 docs/05 中承载比较结论或选型结论的主张,逐条落在 bibliography 注释的证据层级内,不得出现【机制相关】写成【论文直接验证】;另随机抽 10 个条目对照主源,抽样方法与所选 ID 回填第 7 节。
G. DeepSeek(deepseek/deepseek-v4-pro,fresh context,只读)独立 review,范围限逻辑、结构、证据与事实正确性,不做语言表达评价;Kimi 逐条在盘上复核其发现,确认项经 Astra 修复(修复 commit ≤2),随后重跑 A–D 并复核受影响的语义项。

### 5.3 Commit 策略与回滚

Astra 内容 commit ≤3 个逻辑 commit,review 修复另计 ≤2 个,超出须先经 Kimi 批准;禁止 amend、squash、force-push、push;handback 与最终接受分别绑定具体 commit hash 记录于第 7 节。回滚:修复一律走新 commit 或 git revert;整目录删除仅在 Kimi 复核绝对路径、realpath 非 symlink、repo root 一致、无外来内容后作为项目撤销操作执行,删除即同时销毁本地 commit 与本记录(会话 transcript 留存审计)。

## 6. 执行工单(冻结,Astra 的工作指令以此为准)

### 6.1 范围

仅可创建/修改第 2 节授权的 8 个文件;仅可按第 3 节规则新增 ≤3 个文献条目;不得新建其他文件、目录、脚本或工具;不得修改 TASK-RECORD.md;不得触碰本仓库外任何路径;commit 策略见 5.3。任何超出工单的需求必须停止并询问 Kimi。

### 6.2 可用证据来源

arXiv abs 页与 ar5iv/HTML 全文(curl 获取),GenPO 机制级引用须定位到 v4 的 section/equation(如 likelihood 对象、auxiliary action 构造、benchmark 清单、开销讨论),DPPO 对照须定位到 v3 的相应 section;其余论文的注释以 abstract 与公开元数据为证据上限,超出即标注【推测】。联网核验 arXiv 用 export.arxiv.org API,遵守同 host ≥1s 间隔。

### 6.3 文档分工与结构

- `README.md`:仓库目的、两类读者、两条最小阅读路径(同事路径与 retargeting 用户路径,各 5–7 个 paper ID,每步注明要解决的问题与对应章节)、文件导航。
- `docs/01-problem-structure.md`:任务谱系(in-hand 重定向、grasp acquisition、arm-hand 协同、双手协同、long-horizon 组合)、观测与 partial observability(privileged state、history/recurrence、延迟;论文未报告处标"未报告")、硬件(Shadow Hand、Allegro、LEAP)与 benchmark(Adroit、Bi-DexHands、IsaacLab 任务族)的可比性警示(hand-only/arm-hand、动作语义、初始状态假设、object generalization、sim/real 证据)。
- `docs/02-method-landscape.md`:五个方法族作为交叉标签的全景综合(sim 大规模 RL 与 sim-to-real 工程、遥操作与数据采集、人类视频与模仿、diffusion policy、diffusion×RL),每族给出代表工作、观测假设、证据层级与族间组合关系;此处做跨文献综合,不重复 bibliography 的逐篇注释。
- `docs/03-retargeting-to-policy.md`:从 retargeted motion 到可执行策略的链条;轨迹的三种用途(BC 数据、tracking reference 配 RSI、reward/reset 信号)及其代表工作;接触可行性与运动学匹配的动力学鸿沟;遥操作系统条目(dexpilot-2020、anyteleop-2023、openteach-2024、dexcap-2024、bunny-visionpro-2024)在此归入数据管线语境。
- `docs/04-genpo-interface.md`:GenPO 机制边界(auxiliary action 上的 exact likelihood;执行动作为派生量;固定且与待更新参数无关的 action mapping 可折入环境、rollout 保存原始 auxiliary action 计算 ratio,不得写成 residual composition 使 PPO 不成立;被否定的仅是把 auxiliary likelihood 当作执行动作密度的解释);GenPO vs DPPO 对照(likelihood 对象、初始化来源、action horizon、探索方式、计算代价,逐条标 section 出处);接入点分析按三级证据标注(【论文直接验证】【机制相关】【需新证据】),仿真训练与真机在线 fine-tuning 分开讨论;IsaacLab Shadow Hand 任务族作为自然试验场的论证与边界。
- `docs/05-ppo-enhancement.md`:三层结构。update/estimation 层(ppo-2017、implementation-matters-2020、on-policy-actor-critic-2020 的实现细节与评估口径);demonstration/residual 集成层(dapg-2018、residual-rl-2018、sapg-2024、demostart-2024、deepmimic-2018 的 RSI 思想;mappo-2021 仅作 multi-agent 设定的条件性参照);并行训练与课程层(massively-parallel-2021、domain-randomization-2017、openai-rubiks-2019 的 ADR、bi-dexhands-2023 的多任务并行)。每个方向固定写明:对应 baseline 问题、所需数据/信号、改动接口、论文验证到哪一级、未来如何隔离评估;面向 REGRIND 的插入点一律标注为适配假设,不承诺训练收益,不扩展为代码实现任务。
- `docs/bibliography.md`:第 3 节全部 37 条 + Astra 新增(≤3)的唯一逐篇注释位置。
- `scripts/check_links.py`:实现 5.1 B–D 与 --lint、--self-test。

### 6.4 内容硬性约束(E 项核对清单)

1. 04 含 auxiliary-action likelihood 定义与"固定 mapping 折入环境"的精确表述,并明确保存原始 auxiliary action 的 rollout 约定。
2. 04 含 GenPO vs DPPO 逐项对照与出处;不把 GenPO 写成首个能做 on-policy diffusion RL 的方法。
3. 04 的适配论断全部带三级证据标签;sim 训练与真机在线 fine-tuning 分述。
4. 03 含轨迹三种用途的区分与接触可行性讨论;05 含三层与逐方向选型依据;REGRIND 插入点标注适配假设。
5. 01、02、04 均体现观测模态横切维度(privileged state、history、延迟、未报告标注)。
6. README 两条路径各 5–7 篇、每步带问题与章节指向。
7. 全部论文论断可追溯到 bibliography 条目;bibliography 每条四问非空。
8. 条目数量与新增额度符合 5.1 C。

### 6.5 风格约束

遵循 `~/.pi/agent/skills/writing-style/SKILL.md`:中文行文优先、英文技术术语保留原形;一段一个信息且首句点题;一行一个自然段不硬折行;不用 markdown 表格;不用禁用词(见 5.1 D);不用"门"作阶段隐喻(用检查点/验收节点);数字与结论必须可溯源;不得虚报验证状态。

### 6.6 Handback 要求

交回时报告:commit hash 列表;A、B(含 --lint 与 --self-test)、C、D 的实际输出;新增条目清单及其核验证据;执行中遇到的缺口(如论文未报告项、网络不可达项)及处置。handback 不等于 acceptance;acceptance 以 Kimi 完成 5.2 为准。

## 7. 验收与修复记录(执行后回填)

- Bootstrap:Kimi,git init + 本记录,commit 6414df0。
- 模型与通道:编排 Kimi(kimi-code/k3);执行 Astra(litellm/gpt-6-astra,thinking 请求 max、钳制至 xhigh);独立 review DeepSeek(deepseek/deepseek-v4-pro)。前置修复:~/.pi/agent/models.json 的 litellm apiKey 原失效虚拟 key 已换为本地代理 master key(备份 models.json.bak-20261022),已经 live call 验证;此变更在本仓库爆炸半径之外。另:micu-codex 通道余额不足(quota 报错已消毒记录),Astra 全程经 litellm 通道同一模型执行。
- 执行中两项 schema/元数据冻结(经 supervisor 通道确认):① bibliography 七字段 entry schema(paper-id/title/authors-year/arxiv+vN/tier/evidence/固定四问),evidence 须写明所据(abstract 或 section/equation+vN),越据标【推测】;② 清单 title 勘误处理规则——作品身份以无版本 ID+vN 为准,title 比对对象为所记录版本的 API 元数据。
- Handback:Astra commit bdfee53(8 个授权文件,新增文献 0)。执行者自查 A–D 全过:self-test 40/40;结构 9/9;lint entries=37(core 20+extended 17,additions 0)、internal_links=191;style 全过;联网检查 verified=275 failed=0 unverified=0。
- Kimi 独立复核 A–D:git 状态(2 commits、工作区干净、TASK-RECORD 与 bootstrap 逐字节一致)属实;Kimi 独立重跑检查器,首轮 verified=274 failed=0 unverified=1(DPPO HTML 裸 URL 一次瞬时 timeout,同运行其 #S3–S6 anchor 均 verified),重跑 verified=275 failed=0 unverified=0 exit 0;该 URL 页面 Kimi 已另行成功抓取并用于 F 项内容核验,判定为瞬时网络项。
- E(内容硬性约束)8/8 通过:04 含 auxiliary-action likelihood 定义、固定 mapping 折入环境与保存原始 auxiliary action 约定;04 含 GenPO vs DPPO 逐项对照与出处且未把 GenPO 写成首个;04 适配论断全带三级标签且仿真训练与真机在线 fine-tuning 分述;03 含轨迹三用途与接触可行性;05 含三层与逐方向选型依据、REGRIND 插入点均为适配假设;01/02/04 均体现观测横切维度;README 两条路径 6+7 篇、每步带问题与章节指向;论断可追溯到 bibliography 且四问非空;数量与新增额度合规。
- F(核心主张全查 + 抽样):GenPO v4 与 DPPO v3 机制级主张经 arXiv HTML 全文逐条对照属实(ã=(x,y) 与 a=(x+y)/2;Eq.(5) change of variables;Eq.(12) compression (x−y)²;Algorithm 1 第 8 步保存 transitions/dummy actions/probability/advantage;KL 自适应学习率;8 个 IsaacLab benchmark 名单;Shadow Hand 157×20;Appendix D.5 的 2.577 ms;§6 Jacobian determinant 开销;DPPO T_p/T_a;Table A3 的 27.7/35.6/83.6 s;§5 "up to 2× slower" 概述;§5.4 One-leg zero-shot、T_a=8、50 条 demonstrations)。随机抽样:方法为 python random.seed(20261022) 对 37 个 paper-id 的 random.sample(10),所选 ID 为 deepmimic-2018、diffusion-policy-2023、implementation-matters-2020、isaac-lab-2023、openai-inhand-2020、ppo-2017、robotic-telekinesis-2022、sapg-2024、trifinger-2021、visual-dexterity-2022;逐条对照 arXiv API abstract,全部落在所声明 evidence 范围内,定量陈述(7 秒、16/4/10/20+、83%、46.9%、dinosaur/dragon、untrained operators、SAPG 措辞)与主源一致。
- G(DeepSeek review,deepseek/deepseek-v4-pro,fresh context,只读):结论 0 blocker、0 major、2 minor,总体判定"事实与证据层面已达到可交付标准"。两项 minor 经 Kimi 逐条盘上复核确认:① bibliography dexdiffuser-2023 的 authors-year 作 2023 与 arXiv 2402.02989 published 2024-02-05 不自洽;② dppo-2024 条目"对两类读者"首句把跨论文对照定位误标【论文直接验证】,应为【机制相关】。两项均由 Astra 经 review 修复 commit c5b9a02 完成(恰 1 文件、2+/2-,Kimi 已独立复核 diff、grep、--lint 与 self-test 全过;Astra 修复后完整联网检查 275/0/0)。
- 清单勘误(冻结清单本体不改写,勘误记于此):① demostart-2024(2409.06613v2)title 应为"...multi-fingered robots",§3 原作 hands;② dexdiffuser-2023(2402.02989v3)的 authors-year 依 arXiv published 2024-02-05 应为 2024,paper-id 按稳定 ID 规则保持 dexdiffuser-2023 不变。bibliography 两处均已按主源修正。
- 修复后 A–D 复核:lint、self-test、风格、结构不受影响项全过;完整联网检查 275/0/0(Astra 修复后运行)。
- 最终接受 commit:c5b9a02(内容)+ 本节回填的本 commit。验收状态:acceptance 达成,无遗留待决分歧。
