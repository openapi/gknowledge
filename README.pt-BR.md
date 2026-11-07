<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.it.md">Italiano</a> · <a href="README.fr.md">Français</a> · <b>Português (BR)</b> · <a href="README.es.md">Español</a></p>

<p align="center">
  <b>O LLM Wiki do Karpathy como app nativo do GNOME.</b><br>
  Arraste seus documentos e ganhe uma wiki interligada que um modelo mantém atualizada.<br>
  Offline por padrão, sem chave de API, Markdown simples no disco, compatível com Obsidian.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=for-the-badge&color=E95420"></a>
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge em ação: importe artigos de IA, ganhe uma wiki interligada, faça perguntas com citações" width="880">
</p>

## Instalação

No Ubuntu 24.04+ e Debian 13+ basta uma linha: ela adiciona o repositório APT assinado do gknowledge, e as atualizações chegam com `apt upgrade` (em outras distribuições a instalação vai para `~/.local`):

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

Ou adicione o repositório APT você mesmo:

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

Em qualquer distribuição, com Flatpak (o runtime do GNOME vem do Flathub):

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## Feito para funcionar sem internet

Depois de instalado, o gknowledge não precisa de internet, de conta nem de chave de API paga.

- **Motor offline embutido**: importar documentos, montar a wiki e responder com citações funcionam sem nenhum modelo.
- **Pouco consumo de dados**: nada vai para a nuvem por padrão. Se quiser um modelo, o [Ollama](https://ollama.com) roda localmente, baixado uma única vez.
- **Hardware modesto**: um app GTK nativo em Python, sem Electron nem navegador embutido, que roda num notebook Linux comum.
- **Seus dados ficam com você**: Markdown e um índice SQLite numa pasta que você controla.

## Por que gknowledge

Se você já usou [LLM Wiki](https://github.com/nashsu/llm_wiki), [Tolaria](https://github.com/refactoringhq/tolaria), [Reor](https://github.com/reorproject/reor) ou [Khoj](https://github.com/khoj-ai/khoj), já conhece o ciclo: **você importa as fontes, o modelo constrói e mantém uma wiki, e depois você pergunta à wiki.** O gknowledge faz isso como um app GNOME de verdade.

- **Nativo**, GTK 4 e Libadwaita: sem Electron, Tauri ou navegador embutido.
- **Com fontes e revisão**: cada página registra suas fontes, cada resposta as cita, e uma fila de revisão deixa você no controle.
- **Aberto**: licença MIT, a pasta abre no Obsidian.

## Use pelo Claude Code, Codex ou Cursor

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/meu-projeto
```

O agente pode buscar na wiki, ler páginas, fazer perguntas com citações e adicionar novas fontes.

## Escolha o cérebro

| Provedor | Precisa de | Observações |
|---|---|---|
| **Offline** (padrão) | nada | Extração heurística, totalmente privada |
| **Ollama / LM Studio** | um servidor local | Qualquer endpoint compatível com OpenAI |
| **Plano do ChatGPT** | conta Plus ou Pro | Em Preferências, *Sign in with ChatGPT*: o uso sai do seu plano, sem chave de API |
| **Nuvem** | uma chave de API | OpenAI, OpenRouter e similares |

## Contribua

Contribuições são bem-vindas: veja as [*good first issues*](https://github.com/openapi/gknowledge/labels/good%20first%20issue). Traduções para outros idiomas são especialmente bem-vindas.

O resto da documentação está no [README em inglês](README.md). Se o gknowledge for útil para você, uma ⭐ ajuda outras pessoas a encontrá-lo.
