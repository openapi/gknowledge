# Contributing to gknowledge

Thanks for helping. The project is young, so small, focused contributions are the most useful.

## Quick start

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1   # Debian/Ubuntu
make test    # headless core tests, no GTK or network needed
make run     # run from the source tree
make start   # dev loop on a demo project, restarts on every save
```

Flatpak users get the GTK and libadwaita of the GNOME runtime, not yours. Before submitting UI work, run the same dev loop inside that runtime (the version is read from the Flatpak manifest):

```bash
flatpak install --user flathub org.gnome.Platform//51   # once
make start-flatpak
```

New to developing inside the GNOME SDK? Justin's series [Building GNOME Apps with Rust](https://fromthearchitect.dev/series/building-gnome-apps-with-rust/) walks through it, starting from the setup in [Part 1: Getting Started](https://fromthearchitect.dev/posts/gnome-rust-part-1-getting-started/) and then GObject, Blueprint, state and signals; the toolchain differs, the runtime workflow is the same.

## Ground rules

- **Core stays headless.** `gknowledge/core/` must not import GTK. UI code lives in `gknowledge/ui/`.
- **Offline first.** Every feature must work with the offline provider; remote providers are optional.
- **User data is sacred.** Never rewrite user-authored notes or frontmatter; generated content is marked and reviewable.
- **No silent network use.** Anything leaving the machine needs explicit user consent.
- **Follow the GNOME HIG** and keep Flatpak sandboxing in mind (use portals, not broad filesystem access).
- **Tests** for core changes, in `tests/`.
- **AI-assisted contributions** are welcome, but say so in the PR description and make sure you understand the code you submit. Flathub and GNOME Circle have policies on AI-generated code.
- **No CLA.** Contributions are under the project's MIT license.

## Where to start

See [`TODO.md`](TODO.md) and issues labelled `good first issue`. Larger direction is in [`ROADMAP.md`](ROADMAP.md).

## Conduct

Be respectful. Harassment and personal attacks are not tolerated; maintainers may remove comments or contributors that violate this. We follow the spirit of the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
