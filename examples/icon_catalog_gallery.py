# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Generate an offline visual gallery for *all* imported licensed UI icons.

Usage:
    python -m examples.icon_catalog_gallery pynix_gui/assets/jetbrains_new_ui

The gallery previews every manifest category and both light/dark SVG variants.
No dependency on an external website or an IDE window.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import argparse

from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog


def render_gallery(catalog: JetBrainsIconCatalog) -> str:
    cards = []
    for name in catalog.names():
        dark = catalog.resolve(name, dark=True, tool_window=name.startswith("toolwindows/"))
        light = catalog.resolve(name, dark=False, tool_window=name.startswith("toolwindows/"))
        if dark is None and light is None:
            continue
        def image(item, variant):
            if item is None:
                return ""
            path = item.svg_path.relative_to(catalog.directory).as_posix()
            return (f'<span class="variant {variant}">'
                    f'<img alt="" loading="lazy" src="{escape(path, quote=True)}"></span>')
        cards.append(
            f'<article class="icon" data-search="{escape(name.lower(), quote=True)}">'
            f'<div class="preview">{image(dark, "dark")}{image(light, "light")}</div>'
            f'<div class="name" title="{escape(name, quote=True)}">{escape(name)}</div>'
            f'</article>'
        )
    count = len(cards)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>PYNIX – Icon Catalog</title>
<style>
:root{font:13px system-ui,sans-serif;background:#222326;color:#dedfe4}
*{box-sizing:border-box}body{margin:0}
header{position:sticky;top:0;background:#2b2d31;border-bottom:1px solid #41434a;
 padding:16px 24px;z-index:2;display:flex;gap:18px;align-items:center}
strong{font-size:17px}small{color:#aeb0bb}
input{margin-left:auto;max-width:480px;width:40%;padding:9px 12px;
 color:inherit;background:#1e1f22;border:1px solid #5a5d67;border-radius:8px}
main{padding:24px;display:grid;gap:10px;
 grid-template-columns:repeat(auto-fill,minmax(175px,1fr))}
.icon{background:#2b2d31;border:1px solid #41434a;border-radius:8px;min-width:0;
 padding:12px 11px;display:flex;flex-direction:column;gap:10px}
.preview{display:flex;gap:6px;align-items:center}
.variant{height:42px;width:60px;border-radius:6px;display:grid;place-items:center}
.variant.dark{background:#1e1f22}.variant.light{background:#f7f7f8}
.variant img{max-width:22px;max-height:22px}
.name{color:#c3c6d0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.icon[hidden]{display:none}
</style></head><body>
<header><strong>PYNIX icon catalog</strong>
<small id="count">__COUNT__ licensed icons</small>
<input id="query" type="search" placeholder="Search name or category…"
 aria-label="Search imported icons"></header>
<main>__CARDS__</main>
<script>
const query=document.getElementById('query');
const cards=[...document.querySelectorAll('article.icon')];
query.addEventListener('input',()=>{
 const term=query.value.trim().toLowerCase();
 let visible=0;
 for(const card of cards){
  const show=card.dataset.search.includes(term);
  card.hidden=!show;if(show)visible++;
 }
 document.getElementById('count').textContent=visible+' licensed icons';
});
</script></body></html>""".replace("__COUNT__", str(count)).replace("__CARDS__", "".join(cards))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="View every imported PYNIX/JetBrains icon")
    parser.add_argument("directory", type=Path, help="Directory with icon manifest.json")
    parser.add_argument("--output", type=Path, help="HTML output inside icon catalog directory")
    args = parser.parse_args(argv)
    catalog = JetBrainsIconCatalog(args.directory)
    output = (args.output or catalog.directory / "gallery.html").resolve()
    if output.parent != catalog.directory:
        parser.error("--output must be inside the catalog directory for relative SVG paths")
    output.write_text(render_gallery(catalog), encoding="utf-8")
    print(f"Wrote {len(catalog)} imported icons to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
