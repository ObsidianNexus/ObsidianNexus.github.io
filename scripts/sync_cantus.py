#!/usr/bin/env python3
"""
Cantus Alarum Nigrarum — Sync Notion → GitHub Pages (galería bestiario, solo lectura)

Requiere variables de entorno:
  NOTION_TOKEN          Integration token (secret)
  NOTION_CHARACTERS_DB  Data source / database ID de Personajes Canon
  NOTION_FACTIONS_DB    Data source / database ID de Facciones Canonicas (opcional)
  NOTION_PREHISTORIA_ID Page ID de Pre-Historia (opcional)
  NOTION_POWER_ID       Page ID de Escalas de poder (opcional)
"""

from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Cantus-Alarum-Nigrarum"
NOTION_VERSION = "2022-06-28"


def env(name: str, required: bool = True) -> str | None:
    v = os.environ.get(name, "").strip()
    if required and not v:
        print(f"ERROR: falta variable de entorno {name}", file=sys.stderr)
        sys.exit(1)
    return v or None


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_get(token: str, path: str, params: dict | None = None) -> dict:
    r = requests.get(
        f"https://api.notion.com/v1{path}",
        headers=notion_headers(token),
        params=params or {},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def notion_post(token: str, path: str, body: dict) -> dict:
    r = requests.post(
        f"https://api.notion.com/v1{path}",
        headers=notion_headers(token),
        json=body,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def rich_text_to_plain(rt: list[dict] | None) -> str:
    if not rt:
        return ""
    return "".join(t.get("plain_text", "") for t in rt)


def prop_text(props: dict, name: str) -> str:
    p = props.get(name) or {}
    t = p.get("type")
    if t == "title":
        return rich_text_to_plain(p.get("title"))
    if t == "rich_text":
        return rich_text_to_plain(p.get("rich_text"))
    if t == "select":
        s = p.get("select")
        return (s or {}).get("name") or ""
    if t == "multi_select":
        return ", ".join(x.get("name", "") for x in (p.get("multi_select") or []))
    if t == "files":
        files = p.get("files") or []
        urls = []
        for f in files:
            if f.get("type") == "external":
                urls.append(f["external"]["url"])
            elif f.get("type") == "file":
                urls.append(f["file"]["url"])
        return urls[0] if urls else ""
    return ""


def prop_files(props: dict, name: str) -> list[str]:
    p = props.get(name) or {}
    if p.get("type") != "files":
        return []
    urls = []
    for f in p.get("files") or []:
        if f.get("type") == "external":
            urls.append(f["external"]["url"])
        elif f.get("type") == "file":
            urls.append(f["file"]["url"])
    return urls


def query_database(token: str, database_id: str) -> list[dict]:
    results: list[dict] = []
    cursor = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = notion_post(token, f"/databases/{database_id}/query", body)
        results.extend(data.get("results") or [])
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "item"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def nl2p(text: str) -> str:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    if not parts:
        return "<p class=\"muted\">Sin registro.</p>"
    out = []
    for p in parts:
        lines = "<br>\n".join(esc(line) for line in p.split("\n"))
        out.append(f"<p>{lines}</p>")
    return "\n".join(out)


BASE_CSS_HREF = "../css/bestiary.css"
BASE_CSS_HREF_ROOT = "css/bestiary.css"


def page_shell(title: str, body: str, css_href: str, nav_extra: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} · Cantus Alarum Nigrarum</title>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{css_href}">
</head>
<body>
  <div class="veil"></div>
  <header class="site-header">
    <a class="brand" href="../index.html">Cantus Alarum Nigrarum</a>
    <nav>
      <a href="../index.html">Archivo</a>
      <a href="../personajes/">Personajes</a>
      <a href="../facciones/">Facciones</a>
      <a href="../cosmologia.html">Cosmología</a>
      <a href="../escalas.html">Escalas</a>
      <a href="../../index.html">Nexus</a>
      {nav_extra}
    </nav>
  </header>
  <main>
{body}
  </main>
  <footer>
    <p>Archivo de solo lectura · Fuente canónica: Notion · Sincronizado automáticamente</p>
    <p>Cantus Alarum Nigrarum · Obsidian Nexus · Zeth Morket</p>
  </footer>
</body>
</html>
"""


def page_shell_root(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} · Cantus Alarum Nigrarum</title>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{BASE_CSS_HREF_ROOT}">
</head>
<body>
  <div class="veil"></div>
  <header class="site-header">
    <a class="brand" href="index.html">Cantus Alarum Nigrarum</a>
    <nav>
      <a href="index.html">Archivo</a>
      <a href="personajes/">Personajes</a>
      <a href="facciones/">Facciones</a>
      <a href="cosmologia.html">Cosmología</a>
      <a href="escalas.html">Escalas</a>
      <a href="../index.html">Nexus</a>
    </nav>
  </header>
  <main>
{body}
  </main>
  <footer>
    <p>Archivo de solo lectura · Fuente canónica: Notion · Sincronizado automáticamente</p>
    <p>Cantus Alarum Nigrarum · Obsidian Nexus · Zeth Morket</p>
  </footer>
</body>
</html>
"""


def render_character_card(c: dict) -> str:
    pid = esc(c["id"])
    name = esc(c["nombre"])
    raza = esc(c["raza"] or "Desconocida")
    href = esc(c["file"])
    img = c.get("retrato")
    if img:
        media = f'<div class="card-art" style="background-image:url(\ '{esc(img)}\')"></div>'
    else:
        media = '<div class="card-art empty"><span>Sin retrato</span></div>'
    return f"""
    <a class="bestiary-card" href="{href}">
      {media}
      <div class="card-body">
        <span class="card-id">{pid}</span>
        <h3>{name}</h3>
        <span class="tag">{raza}</span>
      </div>
    </a>"""


def render_character_page(c: dict) -> str:
    img_html = ""
    if c.get("retrato"):
        img_html = f'<div class="portrait"><img src="{esc(c["retrato"])}" alt="{esc(c["nombre"])}"></div>'
    weapon = f'<p class="meta"><strong>Arma:</strong> {esc(c["weapon"])}</p>' if c.get("weapon") else ""
    body = f"""
    <article class="entry">
      <div class="entry-header">
        <span class="card-id">{esc(c["id"])}</span>
        <h1>{esc(c["nombre"])}</h1>
        <span class="tag">{esc(c["raza"] or "Desconocida")}</span>
        {weapon}
      </div>
      {img_html}
      <section class="lore">
        <h2>Registro</h2>
        {nl2p(c.get("historia") or "")}
      </section>
      <p class="back"><a href="index.html">← Volver al bestiario</a></p>
    </article>
"""
    return page_shell(c["nombre"], body, BASE_CSS_HREF)


def render_gallery(characters: list[dict]) -> str:
    cards = "\n".join(render_character_card(c) for c in characters)
    body = f"""
    <section class="page-intro">
      <h1>Bestiario de Personajes</h1>
      <p>Registro canónico de entidades catalogadas. Solo lectura. Fuente: Notion.</p>
      <p class="count">{len(characters)} entradas</p>
    </section>
    <section class="gallery">
{cards}
    </section>
"""
    return page_shell("Personajes", body, BASE_CSS_HREF)


def render_faction_card(f: dict) -> str:
    return f"""
    <a class="bestiary-card faction" href="{esc(f['file'])}">
      <div class="card-art empty sigil"><span>{esc(f['nombre'][:1])}</span></div>
      <div class="card-body">
        <h3>{esc(f['nombre'])}</h3>
        <span class="tag">{esc(f.get('tipo') or 'Facción')}</span>
        <p class="muted">{esc((f.get('objetivo') or '')[:120])}</p>
      </div>
    </a>"""


def render_faction_page(f: dict) -> str:
    body = f"""
    <article class="entry">
      <div class="entry-header">
        <h1>{esc(f['nombre'])}</h1>
        <span class="tag">{esc(f.get('tipo') or 'Facción')}</span>
      </div>
      <section class="meta-grid">
        <p><strong>Estado:</strong> {esc(f.get('estado') or '—')}</p>
        <p><strong>Naturaleza:</strong> {esc(f.get('naturaleza') or '—')}</p>
        <p><strong>Amenaza:</strong> {esc(f.get('amenaza') or '—')}</p>
        <p><strong>Objetivo:</strong> {esc(f.get('objetivo') or '—')}</p>
        <p><strong>Relación con La Purga:</strong> {esc(f.get('relacion') or '—')}</p>
      </section>
      <section class="lore">
        <h2>Registro</h2>
        {nl2p(f.get('contenido') or '')}
      </section>
      <p class="back"><a href="index.html">← Volver a facciones</a></p>
    </article>
"""
    return page_shell(f["nombre"], body, BASE_CSS_HREF)


def render_factions_gallery(factions: list[dict]) -> str:
    cards = "\n".join(render_faction_card(f) for f in factions)
    body = f"""
    <section class="page-intro">
      <h1>Facciones Canónicas</h1>
      <p>Órdenes, legiones y fraternidades que disputan Elysarion.</p>
      <p class="count">{len(factions)} entradas</p>
    </section>
    <section class="gallery">
{cards}
    </section>
"""
    return page_shell("Facciones", body, BASE_CSS_HREF)


def blocks_to_text(token: str, page_id: str) -> str:
    """Extrae texto plano de bloques de una página Notion."""
    texts: list[str] = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = notion_get(token, f"/blocks/{page_id}/children", params)
        for b in data.get("results") or []:
            t = b.get("type")
            payload = b.get(t) or {}
            if "rich_text" in payload:
                line = rich_text_to_plain(payload.get("rich_text"))
                if line:
                    texts.append(line)
            if t == "bulleted_list_item":
                line = rich_text_to_plain(payload.get("rich_text"))
                if line:
                    texts.append(f"• {line}")
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return "\n\n".join(texts)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    token = env("NOTION_TOKEN")
    chars_db = env("NOTION_CHARACTERS_DB")
    factions_db = env("NOTION_FACTIONS_DB", required=False)
    prehistoria_id = env("NOTION_PREHISTORIA_ID", required=False)
    power_id = env("NOTION_POWER_ID", required=False)

    assert token and chars_db

    print("→ Consultando personajes…")
    raw_chars = query_database(token, chars_db)
    characters: list[dict] = []
    for page in raw_chars:
        props = page.get("properties") or {}
        # IDs de propiedad flexibles
        pid = prop_text(props, "ID") or prop_text(props, "userDefined:ID") or page["id"][:8]
        nombre = prop_text(props, "nombre") or prop_text(props, "Name") or prop_text(props, "Nombre") or "Sin nombre"
        raza = prop_text(props, "Raza")
        historia = prop_text(props, "Historia")
        weapon = prop_text(props, "Weapon")
        retratos = prop_files(props, "Retrato")
        file_name = f"{pid}-{slugify(nombre)}.html"
        characters.append({
            "id": pid,
            "nombre": nombre,
            "raza": raza,
            "historia": historia,
            "weapon": weapon,
            "retrato": retratos[0] if retratos else "",
            "file": file_name,
        })

    characters.sort(key=lambda c: c["id"])

    print(f"→ {len(characters)} personajes")
    out_chars = OUT / "personajes"
    write(out_chars / "index.html", render_gallery(characters))
    for c in characters:
        write(out_chars / c["file"], render_character_page(c))

    # Facciones
    factions: list[dict] = []
    if factions_db:
        print("→ Consultando facciones…")
        raw_f = query_database(token, factions_db)
        for page in raw_f:
            props = page.get("properties") or {}
            nombre = (
                prop_text(props, "Nombre Faccion")
                or prop_text(props, "Name")
                or prop_text(props, "Nombre")
                or "Facción"
            )
            # contenido de la página
            contenido = blocks_to_text(token, page["id"])
            file_name = f"{slugify(nombre)}.html"
            factions.append({
                "nombre": nombre,
                "tipo": prop_text(props, "Tipo de faccion"),
                "estado": prop_text(props, "Estado"),
                "naturaleza": prop_text(props, "Naturaleza"),
                "amenaza": prop_text(props, "Amenaza"),
                "objetivo": prop_text(props, "Objetivo"),
                "relacion": prop_text(props, "Relacion con la Purga"),
                "contenido": contenido,
                "file": file_name,
            })
        factions.sort(key=lambda f: f["nombre"])
        out_f = OUT / "facciones"
        write(out_f / "index.html", render_factions_gallery(factions))
        for f in factions:
            write(out_f / f["file"], render_faction_page(f))
        print(f"→ {len(factions)} facciones")

    if prehistoria_id:
        print("→ Pre-Historia…")
        text = blocks_to_text(token, prehistoria_id)
        body = f"""
    <section class="page-intro">
      <h1>Cosmología — Pre-Historia</h1>
      <p>Crónica de los Orígenes · El Sueño del Dios Durmiente</p>
    </section>
    <article class="entry lore-wide">
      {nl2p(text)}
    </article>
"""
        write(OUT / "cosmologia.html", page_shell_root("Cosmología", body))

    if power_id:
        print("→ Escalas de poder…")
        text = blocks_to_text(token, power_id)
        body = f"""
    <section class="page-intro">
      <h1>Escalas de poder, tipos y rangos</h1>
      <p>Sistema de Núcleos del Opositor · Base canónica</p>
    </section>
    <article class="entry lore-wide">
      {nl2p(text)}
    </article>
"""
        write(OUT / "escalas.html", page_shell_root("Escalas de poder", body))

    print("✓ Sync completado")


if __name__ == "__main__":
    main()
