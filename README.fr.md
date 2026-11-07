<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.it.md">Italiano</a> · <b>Français</b> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.es.md">Español</a></p>

<p align="center">
  <b>Le LLM Wiki de Karpathy en application GNOME native.</b><br>
  Déposez vos documents, obtenez un wiki lié qu'un modèle tient à jour.<br>
  Hors ligne par défaut, sans clé API, Markdown simple sur disque, compatible Obsidian.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=for-the-badge&color=E95420"></a>
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge en action : importer des articles d'IA, obtenir un wiki lié, poser des questions avec citations" width="880">
</p>

## Installation

Sur Ubuntu 24.04+ et Debian 13+, une seule ligne suffit : elle ajoute le dépôt APT signé de gknowledge, et les mises à jour arrivent avec `apt upgrade` (sur les autres distributions, l'installation se fait dans `~/.local`) :

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

Ou ajoutez le dépôt APT vous-même :

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

Sur n'importe quelle distribution, avec Flatpak (le runtime GNOME vient de Flathub) :

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## Pensé pour fonctionner sans connexion

Une fois installé, gknowledge n'a besoin ni d'internet, ni d'un compte, ni d'une clé API payante.

- **Moteur hors ligne intégré** : l'import des documents, le wiki et les réponses avec citations fonctionnent sans aucun modèle.
- **Peu de données mobiles** : rien n'est envoyé dans le cloud par défaut. Si vous voulez un modèle, [Ollama](https://ollama.com) tourne en local, téléchargé une seule fois.
- **Matériel modeste** : une application GTK native en Python, sans Electron ni navigateur embarqué, qui tourne sur un portable Linux ordinaire.
- **Vos données restent chez vous** : du Markdown et un index SQLite dans un dossier que vous contrôlez.

## Pourquoi gknowledge

Si vous avez utilisé [LLM Wiki](https://github.com/nashsu/llm_wiki), [Tolaria](https://github.com/refactoringhq/tolaria), [Reor](https://github.com/reorproject/reor) ou [Khoj](https://github.com/khoj-ai/khoj), vous connaissez déjà le cycle : **vous importez les sources, le modèle construit et entretient un wiki, puis vous interrogez le wiki.** gknowledge le fait en véritable application GNOME.

- **Native**, GTK 4 et Libadwaita : ni Electron, ni Tauri, ni navigateur embarqué.
- **Avec sources et relecture** : chaque page garde ses sources, chaque réponse les cite, une file de relecture vous laisse le contrôle.
- **Ouvert** : licence MIT, le dossier s'ouvre dans Obsidian.

## Utilisez-le depuis Claude Code, Codex ou Cursor

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/mon-projet
```

L'agent peut chercher dans le wiki, lire les pages, poser des questions avec citations et ajouter de nouvelles sources.

## Choisissez le cerveau

| Fournisseur | Nécessite | Notes |
|---|---|---|
| **Hors ligne** (par défaut) | rien | Extraction heuristique, entièrement privée |
| **Ollama / LM Studio** | un serveur local | Tout endpoint compatible OpenAI |
| **Abonnement ChatGPT** | un compte Plus ou Pro | Dans Préférences, *Sign in with ChatGPT* : l'usage passe sur votre abonnement, sans clé API |
| **Cloud** | une clé API | OpenAI, OpenRouter et similaires |

## Contribuer

Les contributions sont les bienvenues : consultez les [*good first issues*](https://github.com/openapi/gknowledge/labels/good%20first%20issue). Les traductions vers d'autres langues, y compris les langues africaines, sont particulièrement appréciées.

Le reste de la documentation se trouve dans le [README en anglais](README.md). Si gknowledge vous est utile, une ⭐ aide d'autres personnes à le trouver.
