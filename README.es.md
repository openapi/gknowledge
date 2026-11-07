<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.it.md">Italiano</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <b>Español</b></p>

<p align="center">
  <b>El LLM Wiki de Karpathy como app nativa de GNOME.</b><br>
  Arrastra tus documentos y obtén una wiki enlazada que un modelo mantiene al día.<br>
  Sin conexión por defecto, sin clave de API, Markdown simple en disco, compatible con Obsidian.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=for-the-badge&color=E95420"></a>
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge en acción: importa artículos de IA, obtén una wiki enlazada, haz preguntas con citas" width="880">
</p>

## Instalación

En Ubuntu 24.04+ y Debian 13+ basta una línea: añade el repositorio APT firmado de gknowledge, y las actualizaciones llegan con `apt upgrade` (en otras distribuciones se instala en `~/.local`):

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

O añade tú el repositorio APT:

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

En cualquier distribución, con Flatpak (el runtime de GNOME viene de Flathub):

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## Pensada para funcionar sin internet

Una vez instalada, gknowledge no necesita internet, ni cuenta, ni una clave de API de pago.

- **Motor sin conexión integrado**: importar documentos, construir la wiki y responder con citas funcionan sin ningún modelo.
- **Poco consumo de datos**: por defecto nada se envía a la nube. Si quieres un modelo, [Ollama](https://ollama.com) se ejecuta en local y se descarga una sola vez.
- **Hardware modesto**: una app GTK nativa en Python, sin Electron ni navegador integrado, que funciona en un portátil Linux corriente.
- **Tus datos son tuyos**: Markdown y un índice SQLite en una carpeta que tú controlas.

## Por qué gknowledge

Si has usado [LLM Wiki](https://github.com/nashsu/llm_wiki), [Tolaria](https://github.com/refactoringhq/tolaria), [Reor](https://github.com/reorproject/reor) o [Khoj](https://github.com/khoj-ai/khoj), ya conoces el ciclo: **importas las fuentes, el modelo construye y mantiene una wiki, y luego le preguntas a la wiki.** gknowledge lo hace como una auténtica aplicación GNOME.

- **Nativa**, GTK 4 y Libadwaita: sin Electron, Tauri ni navegador integrado.
- **Con fuentes y revisión**: cada página registra sus fuentes, cada respuesta las cita y una cola de revisión te deja el control.
- **Abierta**: licencia MIT, la carpeta se abre en Obsidian.

## Úsala desde Claude Code, Codex o Cursor

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/mi-proyecto
```

El agente puede buscar en la wiki, leer páginas, hacer preguntas con citas y añadir nuevas fuentes.

## Elige el cerebro

| Proveedor | Necesita | Notas |
|---|---|---|
| **Sin conexión** (por defecto) | nada | Extracción heurística, totalmente privada |
| **Ollama / LM Studio** | un servidor local | Cualquier endpoint compatible con OpenAI |
| **Plan de ChatGPT** | cuenta Plus o Pro | En Preferencias, *Sign in with ChatGPT*: el uso va a tu plan, sin clave de API |
| **Nube** | una clave de API | OpenAI, OpenRouter y similares |

## Contribuye

Las contribuciones son bienvenidas: mira las [*good first issues*](https://github.com/openapi/gknowledge/labels/good%20first%20issue). Las traducciones a otros idiomas son especialmente bienvenidas.

El resto de la documentación está en el [README en inglés](README.md). Si gknowledge te resulta útil, una ⭐ ayuda a que otras personas lo encuentren.
