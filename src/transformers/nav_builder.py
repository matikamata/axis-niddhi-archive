# src/transformers/nav_builder.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Constrói a NavTree completa. Mapa canônico embutido — sem dependência de CSV.

import logging
from pathlib import Path
from typing import List, Dict

from models import Post, Section

logger = logging.getLogger("S13.NavBuilder")

# Mapa canônico — sincronizado com build.py e S09.
# Fonte de verdade: Script 13/build.py (Genesis v2.0).
CANONICAL_SECTION_TITLES: Dict[str, str] = {
    "AB": "Abhidhamma",
    "BA": "Buddha Dhamma – Advanced",
    "BC": "Buddhist Chanting",
    "BD": "Buddha Dhamma",
    "BM": "Bhāvanā (Meditation)",
    "CH": "Buddhism in Charts",
    "DD": "Dhammapada",
    "DP": "Dhamma and Philosophy",
    "DS": "Dhamma and Science",
    "ER": "Elephants in the Room",
    "FT": "FootNotes",
    "HB": "Historical Background",
    "IS": 'Is There a "Self"?',
    "KD": "Key Dhamma Concepts",
    "LD": "Living Dhamma",
    "MR": "Myths or Realities?",
    "MS": "Miscellaneous",
    "NP": "NEW POSTS",
    "PD": "Pure Dhamma",
    "PS": "Paṭicca Samuppāda",
    "QD": "Quantum Mechanics and Dhamma",
    "SI": "Sutta Interpretations",
    "TL": "Three Levels of Practice",
    "TS": "Tables and Summaries",
    "CC": "Core Concepts",
}


def _load_csv_overrides(pipeline_root: Path) -> Dict[str, str]:
    """
    Tenta carregar overrides do MasterPDPN_Sections.csv.
    Formato esperado: "Nome da Seção;PREFIXO"
    Falha silenciosamente — nunca aborta.
    """
    csv_path = pipeline_root / "metadata" / "MasterPDPN_Sections.csv"
    if not csv_path.exists():
        return {}

    overrides: Dict[str, str] = {}
    try:
        import csv
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) >= 2:
                    name = row[0].strip()
                    code = row[1].strip()
                    # Limpar prefixo numérico: "01 - Welcome" → "Welcome"
                    if " - " in name:
                        name = name.split(" - ", 1)[1]
                    if name and code:
                        overrides[code] = name
        if overrides:
            logger.info(f"📖 {len(overrides)} seções carregadas do CSV (override).")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao ler MasterPDPN_Sections.csv: {e} — usando canônico.")

    return overrides


def build_navigation_tree(posts: List[Post], pipeline_root: Path) -> List[Section]:
    """
    Agrupa posts por section_code, ordena por findex.
    Título da seção: CSV (se existir) > mapa canônico embutido > fallback.

    Args:
        posts: Lista completa de posts carregados da CSL.
        pipeline_root: Raiz do pipeline (/beng/pipeline) para localizar CSV.

    Returns:
        List[Section] ordenada por code.
    """
    # Mescla: canônico base + overrides do CSV (CSV tem precedência)
    csv_overrides = _load_csv_overrides(pipeline_root)
    section_map = {**CANONICAL_SECTION_TITLES, **csv_overrides}

    grouped: Dict[str, List[Post]] = {}
    for post in posts:
        code = post.section_code
        grouped.setdefault(code, []).append(post)

    sections: List[Section] = []
    for code in sorted(grouped.keys()):
        post_list = grouped[code]
        title = section_map.get(code, f"Section {code}")
        sections.append(Section(code=code, title=title, posts=post_list))

    logger.info(f"✅ NavTree: {len(sections)} seções, {len(posts)} posts.")
    return sections
