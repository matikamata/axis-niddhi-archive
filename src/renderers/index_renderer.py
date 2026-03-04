# src/renderers/index_renderer.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0

import logging
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape
from models import Section

logger = logging.getLogger("S13.IndexRenderer")


def render_indices(nav_tree: List[Section], output_dir: Path, templates_dir: Path) -> None:
    """
    Renderiza o index.html raiz do site.
    templates_dir injetado pelo build.py — sem path relativo hardcoded.
    """
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")

    try:
        output_html = template.render(
            nav_tree=nav_tree,
            relative_root="./",
            title="Brasileirinho - Dhamma Preservation",
        )
        output_path = output_dir / "index.html"
        output_path.write_text(output_html, encoding="utf-8")
        logger.info(f"✅ index.html gerado → {output_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar index.html: {e}")
