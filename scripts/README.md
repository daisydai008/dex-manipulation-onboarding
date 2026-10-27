# 仓库检查与维护

检查器只用 Python 标准库，不写 cache、日志或 fixture。交付文件清单显式登记在 `scripts/check_links.py` 的 `FILES` 集合，新文件须登记加入，编辑器与运行时辅助文件（如 `.vscode/`、`.pi-subagents/`、`.gitignore`）不属于交付树，运行检查前须从树中删除，本地忽略规则放全局 gitignore 或 `.git/info/exclude`。`--lint` 不联网，按内嵌身份映射锚定原有 36 篇 core/extended 身份，新增条目经登记与 arXiv 核验后接受（当前 43 条、19 core、24 extended）；完整模式核验记录版本的 arXiv API title/ID、书目外链、全部交付 Markdown 中的官方工程文档链接与内部 anchor。网络请求单次 15 秒、至多重试 2 次、同 host 间隔至少 1 秒、总联网预算 15 分钟；退出码为 0 全部通过、2 内容失败、3 网络未完成，内容失败优先，只有 failed=0 且 unverified=0 才通过。

```bash
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py --lint
python3 scripts/check_links.py
```

自动检查用于验证结构与链接，内容接受还需人工核对。条件推导、DPPO 机制与选型建议仍需人工核对；执行者交回与独立内容核验分开，不以链接可达代替技术判断。
