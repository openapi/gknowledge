# Outreach to authors who cover our peers

Ready-to-send messages for writers who already covered Karpathy-style LLM wiki apps. Send them from your own account; keep each one personal and short. Track replies in the channel log of [`DISTRIBUTING.md`](../../DISTRIBUTING.md) §8.

## Theo James (Medium, editor of *Better Workflow*)

Article: [8 Apps That Give You a Karpathy-Style LLM Knowledge Base in 2026](https://medium.com/@theo-james/karpathy-style-llm-knowledge-base-apps-ba4735322be9) (16 June 2026). It ranks NotebookLM, Recall, Obsidian + plugins, Khoj, AnythingLLM, Quivr, Heptabase and Constella (sponsored). His recurring criticism of every tool is that "the automated *LLM compiles a wiki from raw sources* part of the Karpathy pattern is still mostly on you". That is exactly what gknowledge does, so lead with it.

He lists no email or social profile; the only channel is a Medium response on the article (needs a Medium account). Two options:

### Option A: response on the article

> Great breakdown, and your test ("does knowledge build on itself, or does it start over?") is the right one. You note that with Khoj, AnythingLLM and the Obsidian plugins the "LLM compiles a wiki from raw sources" step is still on you.
>
> That step is the whole point of gknowledge, an MIT-licensed desktop app we built: drop in PDFs or Markdown and it writes and maintains a linked Markdown wiki (`index.md`, `log.md`, wikilinks, sources recorded on every page), with a review queue for what the model is unsure about. It runs offline with a built-in engine, or with Ollama / any OpenAI-compatible endpoint, and the folder opens in Obsidian. It is a native GNOME app, so Linux only for now.
>
> If you update the list, I'd be glad if you tried it: https://github.com/openapi/gknowledge

### Option B: pitch a piece to *Better Workflow*

If the publication accepts writers, submit the dev.to article ([I turned Karpathy's LLM Wiki into a native GNOME app](https://dev.to/francescobianco/i-turned-karpathys-llm-wiki-into-a-native-gnome-app-and-it-works-offline-130c)) as a Medium import with the canonical link pointing to dev.to.

## Dr. Prahlad G. Menon (The Menon Lab)

Posts: [Tolaria: Karpathy's LLM Wiki Concept Is Now a Real Desktop App](https://themenonlab.blog/blog/tolaria-karpathy-llm-wiki-desktop-app) and [Google Just Standardized Karpathy's LLM Wiki Pattern](https://themenonlab.blog/blog/google-okf-open-knowledge-format-karpathy-llm-wiki-standard). He follows the category and his contact page explicitly invites open-source collaboration.

Contact (from [themenonlab.blog/contact](https://themenonlab.blog/contact)): email prahlad.menon@quant.md, X [@themedcave](https://x.com/themedcave), Reddit u/the_ai_scientist. Email is the channel he recommends.

**Subject:** An offline, native-Linux take on Karpathy's LLM Wiki (follow-up to your Tolaria post)

> Hi Prahlad,
>
> I read your posts on Tolaria and on Google's Open Knowledge Format; they are among the clearest write-ups of where the LLM Wiki pattern is going.
>
> I'm Francesco, and I maintain gknowledge (https://github.com/openapi/gknowledge), an MIT-licensed desktop app that implements the pattern end to end: you drop in documents and it writes and maintains a linked Markdown wiki, with `index.md` and `log.md`, `[[wikilinks]]`, the sources of every page recorded, and a review queue for uncertain changes.
>
> Two things set it apart from Tolaria and nashsu/llm_wiki, which are both Tauri apps:
>
> - It works with no model at all. A built-in engine ingests and answers offline; Ollama, any OpenAI-compatible endpoint, or a ChatGPT plan make it better when you want them.
> - It is a native GTK 4 / Libadwaita app for Linux, and it ships an MCP server so Claude Code or Codex can read and grow the same wiki.
>
> If it's interesting for a follow-up post or a mention, I'd be happy to answer questions or give you a walkthrough. Either way, thanks for covering the space.
>
> Francesco Bianco

## Not reachable (checked 2026-10-14)

- **ClaudeKit** (claudekit.io): hand-curated Korean site for Claude Code tools (about 70 entries, lists nashsu/llm_wiki). No submission form, repository or contact found on the site, in `llms.txt` or in `robots.txt`.
