---
name: safe-update
description: Update OpenClaw safely with auto-detected dual modes. Ordinary installs follow the official recommended update path, while local source forks use a developer tarball workflow with backup and rollback metadata.
version: 1.5.2
updated: 2026-03-08
---

# Safe Update

按当前环境选择合适的 OpenClaw 更新方式，并在更新前生成可回退的备份信息。

Choose the right OpenClaw update path for the current environment and create rollback-friendly backups before any mutation.

---

## 适用场景

当用户提出以下需求时使用：

- 更新 OpenClaw 到最新版本
- 基于本地功能分支继续同步 upstream
- 修复运行时绑定到错误入口的问题
- 需要一条兼顾普通用户和开发者用户的安全更新链路

Use this skill when the user wants to:

- Update OpenClaw to a newer version
- Sync a local feature branch with upstream
- Repair a runtime that is bound to the wrong entrypoint
- Use one update workflow that works for both ordinary users and developers

---

## 核心设计

`safe-update` 现在采用**双模式**。

`safe-update` now uses a **dual-mode** design.

### 1. 官方模式

适用于普通用户，优先贴近 OpenClaw 官方文档推荐路径。

典型特征：

- 当前环境不是本地功能分支开发态
- 没有明显的本地源码定制需求
- 目标是稳定更新到官方版本

执行策略：

- 优先使用 `openclaw update`
- 然后运行 `openclaw doctor`
- 最后 `openclaw gateway restart`

这条路径对应官方文档中的推荐更新思路。

### 1. Official mode

Use this for ordinary users and prefer the OpenClaw documentation's recommended path.

Typical signals:

- The environment does not look like a local feature-branch development setup
- There is no clear need to preserve local source customizations
- The goal is a stable upgrade to the official version

Execution strategy:

- Prefer `openclaw update`
- Then run `openclaw doctor`
- Finally run `openclaw gateway restart`

This path is intentionally aligned with the official documentation.

### 2. 开发者模式

适用于存在本地源码仓库、本地功能分支或定制修改的用户。

典型特征：

- 当前目录是本地源码仓库
- 当前分支不是纯净官方主分支
- 有本地未推送提交、未提交修改，或需要保留 fork 改动
- 需要把运行时安装成真实目录，而不是继续 link 回源码目录

执行策略：

- `git fetch upstream`
- `git checkout <branch>`
- `git merge` 或 `git rebase` 指定 upstream ref
- `npm run build`
- `npm pack`
- `npm uninstall -g openclaw`
- `npm install -g ./openclaw-<version>.tgz`
- `openclaw daemon install --force`
- `openclaw gateway restart`

这条路径不是官方默认主推更新模式，但适合保留本地开发态改动并重绑运行时。

### 2. Developer mode

Use this for users with a local source checkout, feature branches, or custom modifications.

Typical signals:

- The target directory is a local source repository
- The current branch is not a clean upstream main branch
- There are unpushed commits, uncommitted changes, or fork-specific modifications to preserve
- The runtime should become a real installed directory instead of continuing to resolve back into the source tree

Execution strategy:

- `git fetch upstream`
- `git checkout <branch>`
- `git merge` or `git rebase` onto the chosen upstream ref
- `npm run build`
- `npm pack`
- `npm uninstall -g openclaw`
- `npm install -g ./openclaw-<version>.tgz`
- `openclaw daemon install --force`
- `openclaw gateway restart`

This is not the default official update path, but it is useful when local development changes must be preserved and the runtime binding must be repaired.

---

## 自动检测原则

默认使用：

```bash
./update.sh --install-mode auto
```

脚本会结合以下证据判断适合哪种模式：

- `--dir` 指向的是否是有效 OpenClaw 源码仓库
- 仓库 `package.json` 是否就是 `openclaw`
- 仓库 remote 是否指向 OpenClaw 官方仓库或已知 fork
- 当前 git 分支是否为 `main`
- 是否存在未提交修改
- 是否存在相对 `origin/<branch>` 的本地未推送提交
- 是否存在相对 `origin/<branch>` 的上游新提交
- 当前全局安装目录是否仍是 symlink

判定结果：

- 如果存在明确的 OpenClaw 源码维护仓库，默认优先选 `developer`
- 只有更像纯 package 运行时用户时，才选 `official`

也支持人工强制指定：

```bash
./update.sh --install-mode official
./update.sh --install-mode developer
```

Default usage:

```bash
./update.sh --install-mode auto
```

The script chooses a mode using signals such as:

- Whether `--dir` points at a valid OpenClaw source repository
- Whether that repo's `package.json` name is `openclaw`
- Whether repo remotes point to the official OpenClaw repo or a known fork
- Whether the current git branch is `main`
- Whether there are uncommitted changes
- Whether there are unpushed commits relative to `origin/<branch>`
- Whether upstream already has newer commits
- Whether the global install directory is still a symlink

Decision rule:

- If the environment clearly looks like a maintained OpenClaw source repo, choose `developer`
- Only choose `official` when it looks like a package-runtime-only user environment

You can also force a mode manually:

```bash
./update.sh --install-mode official
./update.sh --install-mode developer
```

---

## 更新前备份

更新前必须生成备份，至少覆盖两类内容。

Backups must be created before mutation. At minimum, they should cover two categories.

### 1. 关键配置备份

- `~/.openclaw/openclaw.json`
- 关键 `auth-profiles.json`

### 1. Critical configuration backup

- `~/.openclaw/openclaw.json`
- Important `auth-profiles.json` files

### 2. 回退元数据

备份目录示例：

```text
~/.openclaw/backups/safe-update/<timestamp>/
  metadata.json
  openclaw.json
  auth-profiles-main.json
  auth-profiles-coder.json
  openclaw-status.txt
  gateway-status.txt
  git-status.txt
  git-log.txt
  rollback.sh
```

其中 `metadata.json` 会记录：

- 选中的安装模式
- 更新前 git branch / commit
- 更新前全局版本
- 更新前源码包名称与版本
- 更新前 gateway command
- 当前 projectDir 和 upstreamRef

另外会尽量补充：

- `git-working-tree.diff`
- `git-staged.diff`
- `repo.bundle`
- `npm-global-openclaw.txt`
- `installed-package.json`
- 开发者模式下的 `installed-runtime-before-update.tar.gz`

`rollback.sh` 提供最小可执行的回退提示步骤，避免失败后无从下手。

### 2. Rollback metadata

Example backup directory:

```text
~/.openclaw/backups/safe-update/<timestamp>/
  metadata.json
  openclaw.json
  auth-profiles-main.json
  auth-profiles-coder.json
  openclaw-status.txt
  gateway-status.txt
  git-status.txt
  git-log.txt
  rollback.sh
```

`metadata.json` records:

- The selected install mode
- The pre-update git branch and commit
- The pre-update global version
- The pre-update package name and version
- The pre-update gateway command
- The current projectDir and upstreamRef

The skill also tries to capture:

- `git-working-tree.diff`
- `git-staged.diff`
- `repo.bundle`
- `npm-global-openclaw.txt`
- `installed-package.json`
- `installed-runtime-before-update.tar.gz` in developer mode

`rollback.sh` provides a practical minimum rollback guide so that failures do not leave the user without a path back.

---

## 使用说明

### 推荐默认用法

大多数情况下优先使用自动检测：

```bash
./update.sh --dir /path/to/openclaw --branch main --install-mode auto
```

如果这个目录是你实际维护和发布 OpenClaw 的源码仓库，`auto` 现在会优先按源码同步链路处理，而不是误落到纯 npm 运行时更新。

### 明确知道自己是普通安装用户

如果你只是正常安装 OpenClaw，没有维护本地源码仓库，也不需要同步最新源码，只想更新当前已安装运行时，可以直接使用：

```bash
./update.sh --install-mode official
```

### 明确知道自己是本地源码开发用户

如果你维护本地 fork、功能分支或官方源码主仓，并希望先同步最新源码再发布运行时，使用：

```bash
./update.sh --dir /path/to/openclaw --branch feat/your-branch --mode rebase --upstream-ref upstream/main --install-mode developer
```

### 先做 dry-run

在真实执行前，建议先预演：

```bash
./update.sh --install-mode auto --dry-run
```

## Usage guide

### Recommended default usage

In most cases, prefer auto detection:

```bash
./update.sh --dir /path/to/openclaw --branch main --install-mode auto
```

### If you know you are a normal install user

If you use a standard OpenClaw install and do not maintain a local source branch, use:

```bash
./update.sh --install-mode official
```

### If you know you are a local source developer

If you maintain a local fork, feature branch, or custom code, use:

```bash
./update.sh --dir /path/to/openclaw --branch feat/your-branch --mode rebase --upstream-ref upstream/main --install-mode developer
```

### Run a dry-run first

Before a real update, preview the flow:

```bash
./update.sh --install-mode auto --dry-run
```

---

## 使用边界

这版技能的目标是覆盖大部分普通用户和开发者的日常更新场景，但它不是一个全自动运维平台。

The goal of this version is to cover most day-to-day update cases for both ordinary users and developers. It is not a fully automated ops platform.

### 当前已经覆盖的边界

- 普通用户可以通过 `official` 模式走官方推荐更新链路
- 开发者可以通过 `developer` 模式保留本地源码修改并重绑运行时
- `auto` 模式可以覆盖大多数常见环境判断
- 更新前已有可用的备份、元数据和回退提示

### Covered well in the current version

- Ordinary users can follow an official-style update path through `official` mode
- Developers can preserve local source changes and repair runtime binding through `developer` mode
- `auto` mode covers most common environment-detection cases
- Backups, metadata, and rollback hints are already practical enough for real use

### 当前刻意没有做的事情

- 不追求百分之百智能的环境识别
- 不把 rollback 做成完全自动恢复系统
- 不把所有官方安装路径都塞进一个超复杂脚本
- 不做完整镜像级别的系统快照

### Intentionally not done in this version

- It does not try to achieve perfect environment detection
- It does not turn rollback into a fully automatic recovery system
- It does not cram every official install path into one overly complex script
- It does not create full machine-level or image-level snapshots

### 什么时候应该暂停并让用户介入

遇到以下情况时，不要盲目继续：

- `auto` 判定结果和环境事实明显不符
- 仓库存在复杂冲突，无法安全 merge 或 rebase
- 当前安装方式异常，超出脚本既定路径
- 备份阶段已经失败
- 用户明确要求保留某些非常特殊的本地状态

### When to stop and involve the user

Do not continue blindly in these cases:

- The `auto` decision clearly disagrees with reality
- The repository has complex conflicts and cannot be safely merged or rebased
- The current install shape is unusual and outside the script's expected paths
- The backup stage has already failed
- The user explicitly needs very unusual local state preserved

### 什么时候这版就已经够用

如果目标只是以下几类，这版通常已经足够：

- 日常升级 OpenClaw
- 普通环境下跟进官方更新
- 本地功能分支同步 upstream/main
- 更新前保留关键配置和回退抓手

### When this version is already enough

This version is usually sufficient when the goal is one of the following:

- Routine OpenClaw upgrades
- Staying current with official updates in a standard install
- Syncing a local feature branch with `upstream/main`
- Preserving critical config and rollback handles before update

---

## 与官方文档的关系

需要明确区分。

A clear distinction from the official documentation matters.

### 官方主推路径

根据本地官方文档：

- 安装首选 installer script
- 普通全局安装首选 `npm install -g openclaw@latest` 或 `pnpm add -g openclaw@latest`
- 源码更新首选 `openclaw update`
- 开发态安装官方更常见的是 `pnpm link --global` 或 `pnpm openclaw ...`

### Officially preferred paths

According to the local OpenClaw docs:

- The installer script is the preferred install path
- Standard global installs prefer `npm install -g openclaw@latest` or `pnpm add -g openclaw@latest`
- Source updates prefer `openclaw update`
- Development installs more commonly use `pnpm link --global` or `pnpm openclaw ...`

### 本技能的开发者模式

开发者模式采用 `npm pack` tarball 安装，是为了处理这类问题：

- 保留本地 fork 和功能分支改动
- 避免全局运行时继续 symlink 回源码目录
- 重新绑定 gateway 到真实安装目录
- 修复安装目录下扩展依赖不完整的问题

因此：

- `official` 对应官方主推路径
- `developer` 对应本地定制源码环境的强化更新链路

### Developer mode in this skill

Developer mode uses a tarball install via `npm pack` to solve problems such as:

- Preserving local fork and feature-branch changes
- Preventing the runtime from continuing to resolve back into the source repo via symlink behavior
- Rebinding the gateway to a real installed runtime directory
- Repairing missing extension dependencies inside the installed runtime

So:

- `official` corresponds to the officially preferred path
- `developer` corresponds to a hardened update path for customized source environments

---

## 关键验证项

每次更新后都必须验证：

1. `openclaw gateway status` 正常
2. `openclaw status` 正常
3. 如果是开发者模式，运行入口应指向全局 npm 安装目录中的真实目录
4. 如果启用了关键扩展，要验证其依赖未丢失
5. 备份目录和回退脚本已生成

## Required validation

After every update, verify:

1. `openclaw gateway status` is healthy
2. `openclaw status` returns normally
3. In developer mode, the runtime entrypoint points at a real directory under the global npm install
4. If critical extensions are enabled, their dependencies still resolve
5. The backup directory and rollback script were created

### Feishu 依赖检查

如果安装目录中存在：

```bash
$(npm root -g)/openclaw/extensions/feishu/package.json
```

则必须验证：

```bash
node -e "require.resolve('@larksuiteoapi/node-sdk', { paths: ['$(npm root -g)/openclaw/extensions/feishu'] })"
```

如果解析失败，需要在扩展目录执行：

```bash
cd "$(npm root -g)/openclaw/extensions/feishu"
npm install
openclaw gateway restart
```

### Feishu dependency check

If this file exists:

```bash
$(npm root -g)/openclaw/extensions/feishu/package.json
```

then verify:

```bash
node -e "require.resolve('@larksuiteoapi/node-sdk', { paths: ['$(npm root -g)/openclaw/extensions/feishu'] })"
```

If resolution fails, run:

```bash
cd "$(npm root -g)/openclaw/extensions/feishu"
npm install
openclaw gateway restart
```

---

## 脚本参数

```bash
./update.sh [OPTIONS]

Options:
  --dir PATH              OpenClaw project directory
  --branch NAME           Git branch to update
  --mode MODE             merge or rebase
  --upstream-ref REF      upstream base ref, default: upstream/main
  --install-mode MODE     auto, official, or developer
  --backup-dir PATH       backup root directory
  --dry-run               Preview only
  --help                  Show help
```

## Script options

```bash
./update.sh [OPTIONS]

Options:
  --dir PATH              OpenClaw project directory
  --branch NAME           Git branch to update
  --mode MODE             merge or rebase
  --upstream-ref REF      upstream base ref, default: upstream/main
  --install-mode MODE     auto, official, or developer
  --backup-dir PATH       backup root directory
  --dry-run               Preview only
  --help                  Show help
```

---

## 故障处理

### 1. merge 或 rebase 冲突

```bash
git status
git add ...
git rebase --continue
```

或中止：

```bash
git rebase --abort
```

### 2. 开发者模式安装后运行入口仍回源码仓库

优先检查：

```bash
ls -ld "$(npm root -g)/openclaw"
python3 - <<'PY'
import os
print(os.path.realpath('$(npm root -g)/openclaw'))
PY
```

如果仍是 symlink 或 realpath 回源码仓库，应重走开发者模式安装链路。

### 3. 更新失败后需要回退

优先查看：

```bash
ls ~/.openclaw/backups/safe-update/
cat ~/.openclaw/backups/safe-update/<timestamp>/metadata.json
bash ~/.openclaw/backups/safe-update/<timestamp>/rollback.sh
```

### 4. Gateway 健康检查

```bash
openclaw gateway status
openclaw status
```

## Troubleshooting

### 1. Merge or rebase conflict

```bash
git status
git add ...
git rebase --continue
```

Or abort:

```bash
git rebase --abort
```

### 2. Developer mode still points back to the source repo after install

Check first:

```bash
ls -ld "$(npm root -g)/openclaw"
python3 - <<'PY'
import os
print(os.path.realpath('$(npm root -g)/openclaw'))
PY
```

If it is still a symlink or resolves back to the source repo, rerun the developer-mode install path.

### 3. Rollback after a failed update

Check these first:

```bash
ls ~/.openclaw/backups/safe-update/
cat ~/.openclaw/backups/safe-update/<timestamp>/metadata.json
bash ~/.openclaw/backups/safe-update/<timestamp>/rollback.sh
```

### 4. Gateway health check

```bash
openclaw gateway status
openclaw status
```
