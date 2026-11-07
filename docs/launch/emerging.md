# Launch texts: Africa and emerging markets

The angle for these audiences is the one that matters where mobile data is expensive and connectivity is patchy: **gknowledge works offline, needs no paid API key, and runs on an ordinary Linux laptop.** Lead with that, not with Karpathy or MCP.

Channel research, status and verified rules are in [`DISTRIBUTING.md` §8.4](../../DISTRIBUTING.md). Translated READMEs exist in French, Brazilian Portuguese and Spanish; issues #32–#40 ask native speakers for Swahili, Hausa, Yoruba, Amharic, Arabic, Hindi, Indonesian, Bengali and Vietnamese.

## PyCoder's Weekly (form filled, needs your click)

Form: <https://pycoders.com/submissions> → "Submit Your Link".

- **URL:** https://github.com/openapi/gknowledge
- **Author:** Francesco Bianco
- **Title:** gknowledge: Offline LLM Wiki Desktop App in Python and GTK 4
- **Description:** gknowledge is a native GNOME desktop app, written in Python with PyGObject, GTK 4 and Libadwaita, that implements Karpathy's "LLM Wiki" idea: you drop in documents and it builds a linked Markdown wiki with provenance, then answers questions with citations. It works offline with no API key, and can optionally use Ollama or any OpenAI-compatible endpoint. It also ships an MCP server so coding agents can search the same wiki. MIT licensed.
- Page 2: name required; email and Twitter optional.

## TabNews (Brazil, PT-BR)

Sign up with email at <https://www.tabnews.com.br>. A post about your own project is allowed if it adds value to the reader; put `Pitch` in the title.

**Título:** Pitch: fiz um app de desktop que transforma seus PDFs numa wiki com citações, e funciona sem internet

> Há alguns meses o Andrej Karpathy descreveu a ideia de um "LLM Wiki": em vez de reler todos os documentos a cada pergunta (o RAG tradicional), o modelo lê as fontes uma vez e constrói uma wiki interligada que vai mantendo atualizada.
>
> Eu queria isso como um app nativo no Linux, e queria que funcionasse sem depender de API paga. O resultado é o **gknowledge**, um app GNOME em Python (GTK 4 + Libadwaita):
>
> - Você arrasta PDFs, Markdown e textos, e ele gera páginas em Markdown com links e a fonte de cada informação.
> - Você faz perguntas e recebe respostas com citações.
> - **Funciona offline, sem chave de API**: um motor heurístico local faz a importação e as respostas. Se quiser respostas melhores, conecta um Ollama local ou qualquer endpoint compatível com OpenAI.
> - A pasta é um vault normal do Obsidian.
>
> Instalação no Ubuntu/Debian:
>
> ```
> curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
> ```
>
> Código (MIT) e README em português: https://github.com/openapi/gknowledge/blob/main/README.pt-BR.md
>
> Está no começo (v0.2). Queria saber de vocês: que tipo de documento vocês colocariam nele, e o que falta para trocar o Obsidian + plugins por isso? Issues marcadas como *good first issue* estão abertas para quem quiser contribuir.

## r/developersIndia (monthly Showcase thread only)

Self-promotion is allowed only in the monthly Showcase thread (second Sunday; next: **8 November 2026**). Comment there:

> **gknowledge** – an offline, no-API-key desktop app that turns your PDFs and notes into a linked wiki with citations (Python, GTK 4)
>
> Inspired by Karpathy's "LLM Wiki" idea: the model reads your sources once and maintains a wiki, instead of re-reading everything on every question. It runs fully offline with a local heuristic engine, so you don't need a paid API; plug in Ollama if you want better answers. The output is a plain Obsidian vault.
>
> One-line install on Ubuntu/Debian, MIT licensed: https://github.com/openapi/gknowledge
>
> There are beginner-friendly issues (UI tasks in GTK, README translations into Hindi and Bengali) if anyone wants a first open-source contribution. Feedback on ingestion quality welcome.

## Hashnode (India, Nigeria)

Cross-post the [dev.to article](https://dev.to/francescobianco/i-turned-karpathys-llm-wiki-into-a-native-gnome-app-and-it-works-offline-130c) with the canonical URL set to dev.to (Hashnode: article settings → "Are you republishing?"). Add the tags `opensource`, `python`, `linux`, `ai`, `offline-first`, and a first paragraph on the offline, no-API-key angle.

## Viblo (Vietnam)

Viblo bans advertising and posts under 1,000 characters, so publish a tutorial, not an announcement: *"Xây dựng wiki kiến thức từ tài liệu với LLM chạy offline trên Linux"*, showing install → import PDFs → ask a question → open the vault in Obsidian, with screenshots. Write it in Vietnamese, or wait for a contributor from issue #40.

## Techpoint Africa tip

Form: <https://techpoint.africa/submit-a-tip/>. They cover startups, so pitch the story, not the tool:

> **An offline AI knowledge tool for places where data is expensive**
>
> gknowledge is a free, MIT-licensed desktop app that turns a folder of PDFs and notes into a searchable, linked wiki with citations. Unlike ChatGPT-style tools, it works with no internet connection and no paid API: the whole pipeline runs on an ordinary Linux laptop, with an optional local model (Ollama). That makes it usable for students, researchers and NGOs working with patchy connectivity and costly mobile data. The project is looking for contributors to translate it into Swahili, Hausa, Yoruba and Amharic. https://github.com/openapi/gknowledge

## Hacktoberfest Hack Day organizers

Hacktoberfest 2026 no longer counts PRs, but its theme is "open-source AI and open-weight models", and local Hack Days need projects to hack on. Contact the organizers through each event's page and offer gknowledge as a ready-made contribution target. Shortlist (dates from the MLH API, 14 Oct 2026):

| Date | Event | Why |
|---|---|---|
| 24 Oct, 31 Oct | [Nairobi x B54](https://events.mlh.io/events/14766-hacktoberfest-hack-day-nairobi-x-b54), [Kigali x B54](https://events.mlh.io/events/14753-hacktoberfest-hack-day-kigali-x-b54), [Ikeja x B54](https://events.mlh.io/events/14765-hacktoberfest-hack-day-ikeja-x-b54), [Abeokuta x Build54](https://events.mlh.io/events/14839-hacktoberfest-hack-day-abeokuta-x-build54-africa-foundation) | one organizer (Build54 Africa Foundation), four events |
| 30 Oct | [Kampala x AIFest Uganda](https://events.mlh.io/events/15508-hacktoberfest-hack-day-kampala-x-aifest-uganda) | AI-focused |
| 31 Oct | [São Paulo x FLUSP](https://events.mlh.io/events/15509-hacktoberfest-hack-day-sao-paulo-x-flusp) | FLOSS group at USP, Linux contributors |
| 28 Oct | [La Plata x AI4Devs](https://events.mlh.io/events/15346-hacktoberfest-meetup-la-plata-x-ai4devs) | AI developers |
| 31 Oct | [Rajshahi x Google ML, AI, DL & NLP Community](https://events.mlh.io/events/15515-hacktoberfest-hack-day-rajshahi-x-google-ml-ai-dl-nlp-community-bangladesh) | AI community; Bengali translation issue |
| 17 Oct | [Lomé x GDG Lomé](https://events.mlh.io/events/15231-hacktoberfest-hack-day-lome-x-gdg-lome) | French-speaking; French README |
| 23 Oct | [Accra x Code & Cocktails](https://events.mlh.io/events/15224-hacktoberfest-hack-day-accra-x-code-cocktails) | Ghana |
| 30 Oct | [Benin City x GDG UNIBEN](https://events.mlh.io/events/15218-hacktoberfest-hack-day-benin-city-x-gdg-uniben) | Nigeria, GDG |
| 31 Oct | [Lusaka x Tech Kaizen](https://events.mlh.io/events/15341-hacktoberfest-hack-day-lusaka-x-tech-kaizen) | Zambia |

**Message (EN; for Lomé, use the French version):**

> Hi! I maintain gknowledge (https://github.com/openapi/gknowledge), an MIT-licensed desktop app that turns documents into a linked wiki with citations, fully offline and with no paid API, with optional local open-weight models through Ollama. It fits this year's Hacktoberfest theme of open-source AI.
>
> If your Hack Day needs projects to contribute to, we have small, well-scoped beginner issues (Python + GTK UI tasks, document parsers) and README translations into Swahili, Hausa, Yoruba, Amharic and more: https://github.com/openapi/gknowledge/labels/good%20first%20issue
>
> I'm happy to review PRs quickly during the event and to join remotely for a 10-minute intro if useful.

> Bonjour ! Je maintiens gknowledge (https://github.com/openapi/gknowledge), une application de bureau sous licence MIT qui transforme des documents en wiki lié avec citations, entièrement hors ligne et sans API payante, avec des modèles ouverts locaux via Ollama en option. Elle correspond au thème Hacktoberfest de cette année, l'IA open source.
>
> Si votre Hack Day cherche des projets où contribuer, nous avons des *good first issues* courtes et bien délimitées (interface Python + GTK, parseurs de documents) et des traductions du README : https://github.com/openapi/gknowledge/labels/good%20first%20issue
>
> Je peux relire les PR rapidement pendant l'événement et faire une présentation de 10 minutes à distance si c'est utile.
