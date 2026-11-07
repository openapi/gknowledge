# Getting gknowledge into Debian and Ubuntu

The goal is `sudo apt install gknowledge` on stock Debian and Ubuntu. Ubuntu imports new packages from Debian unstable automatically, so a package accepted in Debian lands in Ubuntu **universe** at the next sync. This is the route other GTK Python apps have taken: Apostrophe, for example, is maintained by the Debian GNOME team and reaches Ubuntu the same way.

The source packaging lives in [`build-aux/debian/`](../../build-aux/debian). It is the `debian/` directory to copy into a packaging repository on Salsa (Debian's GitLab); it is not used by our own `.deb` script.

## Build and check it locally

```sh
git archive --format=tar.gz --prefix=gknowledge-0.3.0/ v0.3.0 > ../gknowledge_0.3.0.orig.tar.gz
tar -C .. -xzf ../gknowledge_0.3.0.orig.tar.gz
cp -r build-aux/debian ../gknowledge-0.3.0/debian
cd ../gknowledge-0.3.0 && dpkg-buildpackage -us -uc
lintian -I --pedantic ../gknowledge_0.3.0-1_*.changes
```

On a host without debhelper, run the same steps in a `debian:sid` container with `build-essential devscripts debhelper dh-python python3 python3-pypdf lintian` installed.

Last checked on 2026-10-13 in `debian:sid`: builds, the core tests run during the build and pass, the package installs and the GTK 4 and Libadwaita modules import. Lintian only reports the placeholder ITP bug number, which is filled in after step 1, and informational notes.

## Steps

1. **File the ITP** (Intent To Package) against the `wnpp` pseudo-package, with the text below. Use `reportbug wnpp` or email `submit@bugs.debian.org`. The bug number replaces `#XXXXXX` in `debian/changelog`.
2. **Ask the Debian GNOME team** whether they will co-maintain it (message below). If they accept, `Maintainer:` becomes `Debian GNOME Maintainers <pkg-gnome-maintainers@lists.alioth.debian.org>` and we go in `Uploaders:`, and the repository moves under `salsa.debian.org/gnome-team/`.
3. **Find a sponsor.** Uploading to Debian needs a Debian Developer. Upload the source package to [mentors.debian.net](https://mentors.debian.net) and file an RFS (Request For Sponsorship) bug against `sponsorship-requests`, or ask the GNOME team directly.
4. **Wait for NEW.** New packages go through the ftp-masters' NEW queue, which typically takes days to weeks.
5. **Ubuntu.** Once in unstable, the package syncs into the current Ubuntu development release automatically. Older Ubuntu releases keep using our `.deb` or the Snap.

Each new upstream release then needs a new `debian/changelog` entry and an upload; `debian/watch` lets `uscan` find new tags.

## ITP text

```
Subject: ITP: gknowledge -- native GNOME app that turns documents into a cited wiki
Package: wnpp
Severity: wishlist
Owner: Francesco Bianco <info.francescobianco@gmail.com>
X-Debbugs-Cc: debian-devel@lists.debian.org, debian-gtk-gnome@lists.debian.org

* Package name    : gknowledge
  Version         : 0.3.0
  Upstream Contact: https://github.com/openapi/gknowledge/issues
* URL             : https://github.com/openapi/gknowledge
* License         : Expat (code), CC0-1.0 (AppStream metadata)
  Programming Lang: Python
  Description     : native GNOME app that turns documents into a cited wiki

gknowledge collects documents, notes and links (Markdown, text, PDF,
HTML, EPUB) and turns them into a linked Markdown wiki in which every
page records its sources. Questions are answered from the wiki with
numbered citations. It works fully offline with a built-in engine and
can optionally use a local model (Ollama, LM Studio), any
OpenAI-compatible endpoint, or the user's own ChatGPT plan. It also
ships an MCP server so coding agents can use the same wiki.

It is a GTK 4 / Libadwaita app with no dependencies outside the archive
(python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, optionally python3-pypdf).
Similar apps in Debian are general note editors such as Apostrophe;
none builds a cited knowledge base from source documents.

I am upstream and will maintain the package, ideally within the Debian
GNOME team. Packaging is ready and lintian-clean apart from this bug
number: https://github.com/openapi/gknowledge/tree/main/build-aux/debian
I need a sponsor.
```

## Message to the Debian GNOME team

To: `debian-gtk-gnome@lists.debian.org`

```
Subject: Team maintenance for gknowledge (GTK 4/Libadwaita, ITP #XXXXXX)

Hello,

I'm the upstream developer of gknowledge, a GTK 4 and Libadwaita app
written in Python that turns documents into a linked Markdown wiki with
sources and cited answers. It works offline and only depends on
python3-gi, gir1.2-gtk-4.0 and gir1.2-adw-1 (python3-pypdf optional).

I've filed ITP #XXXXXX and prepared the packaging (debhelper 14,
dh-python, private module directory, man pages, lintian-clean apart
from the ITP number):
https://github.com/openapi/gknowledge/tree/main/build-aux/debian

Would the team be willing to host it on Salsa under gnome-team, with me
as an uploader, and could someone sponsor the first upload? I'm happy
to follow the team's packaging conventions and to take care of updates.

Thanks,
Francesco Bianco
```
