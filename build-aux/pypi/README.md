# gknowledge-mcp

<!-- mcp-name: io.github.openapi/gknowledge -->

**An MCP server for [gknowledge](https://github.com/openapi/gknowledge) wikis.** Claude Code, Codex, Cursor and any other Model Context Protocol client can search, read and grow a linked Markdown wiki that an LLM keeps up to date, following [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Sources are compiled into the wiki once. Agents then read the wiki instead of re-reading raw documents on every question.

- **Plain files.** Markdown with `[[wikilinks]]` and YAML frontmatter, an `index.md` catalogue and an append-only `log.md`. The folder opens in Obsidian or any editor.
- **Cited and incremental.** Each new source updates only the pages it touches. Every page records its sources, and answers cite pages.
- **Offline by default.** A built-in heuristic engine ingests and answers with no model and no API key. For better synthesis, set `provider`, `base_url` and `model` in the project's `settings/settings.json` (or from the desktop app) to use Ollama or any OpenAI-compatible endpoint.
- **No dependencies.** Standard library only; `pip install "gknowledge-mcp[pdf]"` adds PDF import.

## Install and register

```bash
claude mcp add gknowledge -- uvx gknowledge-mcp --init ~/Knowledge/my-project    # Claude Code
codex mcp add gknowledge -- uvx gknowledge-mcp --init ~/Knowledge/my-project     # Codex CLI
```

For Cursor or other clients:

```json
{ "mcpServers": { "gknowledge": { "command": "uvx", "args": ["gknowledge-mcp", "--init", "/home/you/Knowledge/my-project"] } } }
```

`--init` creates the project folder the first time. Without it, the server only opens an existing project. You can also `pipx install gknowledge-mcp` and use `gknowledge-mcp` as the command.

## Tools

| Tool | What the agent can do |
|---|---|
| `search_wiki` | find pages by keyword |
| `read_page` | read a page with its sources and backlinks |
| `list_pages` | list pages by type |
| `ask` | get a cited answer, optionally saved back into the wiki |
| `add_source` | import and ingest a file |
| `recent_activity` | see what changed recently |

## The desktop app

This package is the headless part of gknowledge. The full app is a native GNOME application (GTK 4 and Libadwaita) with sources, wiki, assistant and a review queue in one window, and it opens the same project folders. Install it from the [signed APT repository or Flatpak](https://openapi.github.io/gknowledge).

MIT licensed. Issues and contributions: [github.com/openapi/gknowledge](https://github.com/openapi/gknowledge).
