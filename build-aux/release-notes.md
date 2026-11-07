## Install

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

Or download `gknowledge_all.deb` below and run `sudo apt install ./gknowledge_all.deb` (Ubuntu 24.04+ / Debian 13+).

On any distribution with Flatpak (Fedora, Arch, openSUSE, …):

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## What's new

See [CHANGELOG.md](https://github.com/openapi/gknowledge/blob/main/CHANGELOG.md).

## Highlights

- Native GTK 4 and Libadwaita app with a Nautilus-style sidebar
- Offline by default: ingest documents into a linked Markdown wiki with provenance, ask questions with citations
- Sign in with ChatGPT to use your own Plus or Pro plan, or connect Ollama or any OpenAI-compatible endpoint
- Review queue for generated content; Obsidian-compatible vault
- MCP server: use the wiki from Claude Code, Codex or Cursor
