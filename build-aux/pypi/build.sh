#!/usr/bin/env bash
# Build the gknowledge-mcp wheel and sdist for PyPI.
#
#   build-aux/pypi/build.sh [outdir]     (default: dist/pypi)
#
# Only the headless core and the MCP server are packaged: the GTK interface
# (app.py, __main__.py, ui/) stays out, so the package installs anywhere.
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
out=$(realpath -m "${1:-$root/dist/pypi}")
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

cp "$root/build-aux/pypi/pyproject.toml" "$root/build-aux/pypi/README.md" "$root/LICENSE" "$stage/"
mkdir "$stage/gknowledge"
cp "$root/gknowledge/__init__.py" "$root/gknowledge/mcp.py" "$stage/gknowledge/"
cp -r "$root/gknowledge/core" "$root/gknowledge/providers" "$stage/gknowledge/"
find "$stage" -name __pycache__ -type d -prune -exec rm -rf {} +

python3 -m build --outdir "$out" "$stage"
