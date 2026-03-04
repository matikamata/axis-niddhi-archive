# src/renderers/post_renderer.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Renderiza posts com build incremental por hash. Templates injetados — sem paths hardcoded.
# PATCH S14: inject_marginalia (M1.1) — glossary injection restaurada.

import hashlib
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Comment
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
from models import Post, Section
from transformers.link_resolver import LinkResolver
from transformers.asset_mapper import process_assets

logger = logging.getLogger("S13.PostRenderer")

_SKIP_TAGS = {"script", "style", "code", "pre", "textarea"}

# Tags cujos nós de texto NÃO devem ser anotados.
# Estrutura, links, código e elementos já anotados são intocáveis.
_SKIP_TAGS = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "code", "pre", "script", "style", "textarea",
})


# ── Helpers ────────────────────────────────────────────────────────────────────

def infer_level(section_code: str) -> str:
    """Nível cognitivo heurístico baseado na seção."""
    intro    = {"TL", "BD", "LD", "KD"}
    advanced = {"AB", "PS", "QD", "BA"}
    if section_code in intro:     return "intro"
    if section_code in advanced:  return "advanced"
    return "intermediate"


def get_safe_harbor(section_code: str) -> Optional[Dict[str, str]]:
    """Para seções avançadas, sugere seção introdutória."""
    if section_code in {"TL", "BD", "LD"}:
        return None
    return {
        "code":  "TL",
        "title": "Three Levels of Practice",
        "url":   "../../index.html#section-TL",
    }


def _estimate_reading_time(html: str) -> int:
    """Estima minutos de leitura (200 palavras/min)."""
    text = re.sub(r"<[^>]+>", "", html)
    words = len(text.split())
    return max(1, round(words / 200))


def _normalize_html(html: str) -> str:
    """Normaliza diacríticos Pāli para NFC."""
    return unicodedata.normalize("NFC", html) if html else ""


def load_glossary(glossary_json: Path) -> Dict[str, Any]:
    """
    Carrega glossary_config.json.
    Retorna dict vazio se ausente — nunca aborta.
    """
    if not glossary_json.exists():
        return {}
    try:
        data = json.loads(glossary_json.read_text(encoding="utf-8"))
        # Formato: { "entries": [ {"src": "...", "tgt": "..."}, ... ] }
        entries = data.get("entries", [])
        return {e["src"].lower(): e["tgt"] for e in entries if "src" in e and "tgt" in e}
    except Exception as e:
        logger.warning(f"⚠️  Glossário não carregado: {e}")
        return {}


def inject_marginalia(html: str, glossary: dict) -> str:
    """
    Envolve a primeira ocorrência de cada termo do glossário em:
        <em class="term-highlight" data-term="..." title="...">

    DOM-based (BeautifulSoup) — nunca trata HTML como string pura.
    NFC normalize garante match correto de diacríticos Pāli.
    Retorna html intacto se glossário vazio.
    """
    if not glossary:
        return html

    html = unicodedata.normalize("NFC", html)

    soup = BeautifulSoup(html, "html.parser")

    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in sorted(glossary.keys(), key=len, reverse=True)) + r")\b",
        flags=re.IGNORECASE,
    )

    def _replacer(match: re.Match) -> str:
        term = match.group(0)
        # Localizar chave case-insensitive
        key = next((k for k in glossary if k.lower() == term.lower()), None)
        if not key:
            return term
        entry = glossary[key]
        # entry pode ser str (glossary_config.json) ou dict com "definition"
        if isinstance(entry, dict):
            raw_def = entry.get("definition", "")
        else:
            raw_def = str(entry)
        clean_def = re.sub(r"<[^>]+>", "", raw_def).replace('"', "&quot;")
        return f'<em class="term-highlight" data-term="{key}" title="{clean_def}">{term}</em>'

    for text_node in soup.find_all(string=True):
        if isinstance(text_node, Comment):
            continue
        if text_node.parent.name in _SKIP_TAGS:
            continue
        original = str(text_node)
        new_html = pattern.sub(_replacer, original)
        if new_html != original:
            text_node.replace_with(BeautifulSoup(new_html, "html.parser"))

    return str(soup)


# ── Renderizador principal ──────────────────────────────────────────────────────

def render_posts(
    posts: List[Post],
    output_dir: Path,
    templates_dir: Path,
    template_hash: str,
    cache_file: Path,
    nav_tree: List[Section],
    slug_resolver: LinkResolver,
    asset_map: Dict[str, str],
    glossary: Dict[str, Any],
) -> Dict[str, int]:
    """
    Renderiza todos os posts com build incremental.

    Incremental logic:
        composite_hash = SHA256(content_sha256 | template_hash)
        Se hash == cache → post está atualizado → SKIP (a menos que output ausente)
        Se hash != cache → rebuild

    Args:
        posts: Lista completa de posts da CSL.
        output_dir: Pasta raiz do output (13-static-site/).
        templates_dir: Pasta de templates Jinja2 (injetada pelo build.py).
        template_hash: Hash combinado de todos os templates.
        cache_file: Path para build_state.json.
        nav_tree: Árvore de navegação completa.
        slug_resolver: LinkResolver com slug_map da CSL.
        asset_map: Mapa de assets (pode ser vazio — opcional).
        glossary: Dicionário de termos (pode ser vazio).

    Returns:
        Dict com contagens: rebuilt, skipped, errors.
    """
    stats = {"rebuilt": 0, "skipped": 0, "errors": 0}

    # 1. Carregar cache
    build_state: Dict[str, str] = {}
    if cache_file.exists():
        try:
            build_state = json.loads(cache_file.read_text())
        except Exception:
            build_state = {}

    # 2. Setup Jinja2
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    try:
        template = env.get_template("post.html")
    except Exception as e:
        logger.critical(f"❌ Template post.html não encontrado: {e}")
        stats["errors"] = len(posts)
        return stats

    # 3. Mapa de seções para navegação contextual
    section_map: Dict[str, List[Post]] = {s.code: s.posts for s in nav_tree}
    section_titles: Dict[str, str] = {s.code: s.title for s in nav_tree}

    # 4. Renderizar
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    for post in posts:
        try:
            # A. Hash incremental
            content_sha = (
                post.artifacts["en-US"].integrity_sha256 or "nohash"
            )
            composite = hashlib.sha256(
                f"{content_sha}|{template_hash}".encode()
            ).hexdigest()

            post_dir = pages_dir / post.pdpn
            output_file = post_dir / "index.html"

            if build_state.get(post.pdpn) == composite and output_file.exists():
                stats["skipped"] += 1
                continue

            # B. Ler conteúdo
            html_en_raw = post.artifacts["en-US"].file_path.read_text(encoding="utf-8")
            html_en_raw = _normalize_html(html_en_raw)

            html_pt_raw = ""
            if post.has_pt:
                html_pt_raw = post.artifacts["pt-BR"].file_path.read_text(encoding="utf-8")
                html_pt_raw = _normalize_html(html_pt_raw)

            # C. Transformar
            html_en = slug_resolver.resolve_links(html_en_raw, post.pdpn)
            html_en = process_assets(html_en, post.pdpn, asset_map)
            if glossary:
                html_en = inject_marginalia(html_en, glossary)

            html_pt = ""
            if html_pt_raw:
                html_pt = slug_resolver.resolve_links(html_pt_raw, post.pdpn)
                html_pt = process_assets(html_pt, post.pdpn, asset_map)
                if glossary:
                    html_pt = inject_marginalia(html_pt, glossary)

            # D. Contexto de navegação
            section_code  = post.section_code
            section_title = section_titles.get(section_code, section_code)
            section_posts = section_map.get(section_code, [])

            try:
                idx = next(i for i, p in enumerate(section_posts) if p.pdpn == post.pdpn)
                prev_post = section_posts[idx - 1] if idx > 0 else None
                next_post = section_posts[idx + 1] if idx < len(section_posts) - 1 else None
                position_index = idx + 1
            except StopIteration:
                prev_post = next_post = None
                position_index = 0

            section_total  = len(section_posts)
            reading_time   = _estimate_reading_time(html_en)
            level          = infer_level(section_code)
            suggestion     = get_safe_harbor(section_code)

            # E. Renderizar template
            post_dir.mkdir(parents=True, exist_ok=True)
            output_html = template.render(
                post=post,
                content_en=html_en,
                content_pt=html_pt,
                nav_tree=nav_tree,
                relative_root="../../",
                current_section_code=section_code,
                current_section_title=section_title,
                prev_post=prev_post,
                next_post=next_post,
                position_index=position_index,
                section_total=section_total,
                meta_reading_time=reading_time,
                meta_level=level,
                suggestion_block=suggestion,
            )

            output_file.write_text(output_html, encoding="utf-8")
            build_state[post.pdpn] = composite
            stats["rebuilt"] += 1

        except Exception as e:
            logger.error(f"❌ Erro em {post.pdpn}: {e}")
            stats["errors"] += 1

    # 5. Salvar cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(build_state, indent=2), encoding="utf-8")

    return stats
