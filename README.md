# humanizer-zh-chatgpt

把 [`op7418/Humanizer-zh`](https://github.com/op7418/Humanizer-zh) 持续、确定性地转换成 ChatGPT 兼容 Skill。

这个仓库把“上游内容”和“ChatGPT 适配层”分开：上游 `Humanizer-zh` 始终作为只读来源；本仓库不维护一份人工 fork 的规则正文，而是通过脚本重新生成 ChatGPT 版本。这样上游更新时，不需要反复手工合并适配修改。

## Skill 分工

| Skill | 适用范围 | 常见任务 |
| --- | --- | --- |
| `humanizer-en`（本机英文适配版，来源 `blader/humanizer`） | English-language writing only | 英文文章、邮件、评论和说明的润色与审阅 |
| `humanizer-zh` | Chinese-language writing only | 中文文章、评论、技术说明和文档的润色与审阅 |

两个 Skill 的触发描述明确按写作语言划分，避免自动路由时相互竞争。中英混合文本根据主要写作语言和用户明确指定选择。

## 自动化流程

```text
op7418/Humanizer-zh
        │
        │ 每月 1 日检查 / 手动触发
        ▼
scripts/sync_upstream.py
        │
        ├─ 保存 upstream-snapshot/
        ├─ 保存 upstream-tests/
        ├─ 确定性转换 generated/humanizer-zh/
        └─ 更新 UPSTREAM.lock
        │
        ▼
validate + unit tests
        │
        ▼
自动创建同步 PR
        │
        │ 人工审核上游规则变化
        ▼
merge main
        │
        ▼
GitHub Release → skill.zip
```

同步任务**不会直接覆盖 `main`**。发现上游新 commit 后只创建或更新 `automation/sync-humanizer-zh` PR。你确认规则变化没有问题并合并后，Release workflow 才生成新的 `skill.zip`。

默认在每月 1 日 00:00 UTC 自动检查一次 `op7418/Humanizer-zh`。上游 SHA 没有变化时不产生 PR；如需立即检查，可在 GitHub Actions 中手动运行 `Sync upstream Humanizer-zh`（`workflow_dispatch`）。

## 转换原则

转换不调用 LLM，也不重新润色上游内容。`scripts/convert_skill.py` 只执行可重复的机械操作：

- 从上游 YAML frontmatter 读取并核对 `name`；上游 `description` 不参与最终路由；
- 生成 ChatGPT Skill 的 frontmatter，只保留 `name` 和 adapter 固定的中文专用 `description`；
- 保留上游核心编辑约束、文体、流程和文件保护规则；
- 从固定标题 `## 模式的使用方式` 起，把详细 31 项规则拆入 `references/patterns.md`；
- 生成中文专用的 `agents/openai.yaml`；
- 复制上游 LICENSE；
- 写入 `UPSTREAM.json`，记录确切 commit SHA。

`validate_conversion.py` 会重新对照上游快照，确认核心正文和详细规则 payload 没有丢失或被重写，并确认 adapter 的中文专用 description 和界面元数据保持固定。未来即使上游更改自己的 description，也不会覆盖这层触发边界。

## 目录

```text
.
├── .github/workflows/
│   ├── ci.yml
│   ├── sync-upstream.yml
│   └── release.yml
├── generated/humanizer-zh/   # 可上传 Skill 的展开目录
├── scripts/
│   ├── convert_skill.py
│   ├── package_release.py
│   ├── sync_upstream.py
│   └── validate_conversion.py
├── tests/                    # 适配层自身测试
├── upstream-snapshot/        # 本次已审核的上游文本快照
├── upstream-tests/           # 上游 tests 的同步副本（不在高权限同步 Job 中执行）
├── UPSTREAM.lock             # 当前已同步 SHA
└── adapter-config.json
```

## 为什么不直接执行上游 tests

同步 workflow 拥有创建 PR 所需的写权限。出于供应链安全考虑，它会复制上游 `tests/` 供审阅，但不会在高权限 Job 中直接执行来自外部仓库的 Python。适配层自己的测试负责检查转换器和包结构；上游测试内容仍会随同步 PR 一起显示 diff，方便人工审阅。

## 本地重新同步

```bash
python scripts/sync_upstream.py
python scripts/validate_conversion.py \
  --source-dir upstream-snapshot \
  --output-dir generated/humanizer-zh
python -m unittest discover -s tests -v
python scripts/package_release.py
```

最终文件位于：

```text
dist/skill.zip
```

## 在 ChatGPT 中更新

GitHub 侧的检测、转换、验证和打包可以自动完成；ChatGPT Skills 界面中已安装的个人 Skill 仍建议用最新 Release 的 `skill.zip` 手动更新。也就是说，正常维护时你只需要：

1. 收到同步 PR；
2. 查看上游规则 diff；
3. 合并；
4. 从 Release 取得新的 `skill.zip` 并上传到 ChatGPT。

## 许可

适配脚本采用 MIT License。生成的 Skill 保留 `Humanizer-zh` 上游 MIT License，并在 `UPSTREAM.json` 中记录来源 commit。
