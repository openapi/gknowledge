<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.it.md">Italiano</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.es.md">Español</a></p>

<p align="center">
  <b>Karpathy 的 LLM Wiki，做成原生 GNOME 应用。</b><br>
  放入你的文档，得到一个由大模型持续维护、相互链接的知识库。<br>
  默认离线运行，纯 Markdown 存储，兼容 Obsidian。
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=for-the-badge&color=E95420"></a>
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge 演示：导入 AI 论文，生成链接知识库，带引用地回答问题" width="880">
</p>

## 安装

Ubuntu 24.04+ / Debian 13+ 一行命令安装，会添加已签名的 gknowledge APT 软件源，之后用 `apt upgrade` 即可更新（其他发行版会安装到 `~/.local`）：

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

或者手动添加 APT 软件源：

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

任意发行版，使用 Flatpak（GNOME 运行时自动从 Flathub 安装）：

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## 为什么选择 gknowledge

如果你用过 [LLM Wiki](https://github.com/nashsu/llm_wiki)、[Tolaria](https://github.com/refactoringhq/tolaria)、[Reor](https://github.com/reorproject/reor) 或 [Khoj](https://github.com/khoj-ai/khoj)，你已经熟悉这个流程：**导入资料，让模型构建并维护 wiki，然后基于 wiki 提问。** gknowledge 把它做成了真正的 GNOME 应用。

- **原生应用**：GTK 4 + Libadwaita，没有 Electron、Tauri 或浏览器内核。
- **无需账号**：内置离线引擎即可导入和问答；接入模型后效果更好。
- **数据归你所有**：Markdown + YAML frontmatter，加上可读的 SQLite 索引，可直接用 Obsidian 打开。
- **有出处、可审阅**：每个页面记录来源，回答带编号引用，审阅队列让你掌控内容。

## Karpathy 的 LLM Wiki 模式

2026 年 4 月，Andrej Karpathy 提出了 [LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：不再每次提问都重新阅读原始文档，而是让大模型构建并持续维护一个不断积累的 wiki。

**我们保留的**：原始资料、生成的 wiki、配置三层结构；ingest（导入）和 query（提问）操作；`index.md` 目录和 `log.md` 日志；`[[wikilinks]]` 和 Obsidian 兼容。

**我们新增的**：原生桌面应用；无需模型也能用的离线引擎；用你自己的 ChatGPT 套餐登录、Ollama 或任何 OpenAI 兼容接口；两步式导入并记录出处；不生成空页面、自动合并重复条目；审阅队列；以及 MCP 服务器。

## 在 Claude Code、Codex 或 Cursor 中使用

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project
```

智能体可以搜索 wiki、阅读页面、带引用提问，并导入新资料。

## 选择你的模型

| 提供方 | 需要 | 说明 |
|---|---|---|
| **离线**（默认） | 无 | 启发式抽取，完全私密 |
| **ChatGPT 套餐** | Plus 或 Pro 账号 | 在设置中点击 *Sign in with ChatGPT*，用量计入你自己的套餐，无需 API key |
| **Ollama / LM Studio** | 本地服务 | 任何 OpenAI 兼容接口 |
| **云端接口** | API key | OpenAI、OpenRouter 等 |

更多内容请看 [English README](README.md)。如果 gknowledge 对你有帮助，欢迎点个 ⭐。
