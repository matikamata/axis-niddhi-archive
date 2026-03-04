# src/loaders/csl_loader.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Escaneia 09-csl/ e retorna List[Post]. CSL é READ-ONLY — nunca escreve aqui.

import logging
from pathlib import Path
from typing import List

from .identity_loader import load_identity
from models import Post

logger = logging.getLogger("S13.CSL")


def load_csl_repository(csl_root: Path) -> List[Post]:
    """
    Varre 09-csl/ e carrega todos os posts válidos.

    Regras:
    - Ignora symlinks (segurança)
    - Ignora pastas sem identity.json
    - Loga posts inválidos mas continua (nunca aborta)
    - Ordena por findex para determinismo

    Retorna: List[Post] ordenada por findex.
    """
    valid: List[Post] = []
    skipped = 0

    if not csl_root.exists():
        logger.critical(f"CSL não encontrada: {csl_root}")
        return []

    logger.info(f"📂 Scanning CSL: {csl_root}")

    for item in sorted(csl_root.iterdir()):
        if not item.is_dir():
            continue
        if item.is_symlink():
            logger.warning(f"⛔ Symlink ignorado: {item.name}")
            skipped += 1
            continue

        identity_path = item / "meta" / "identity.json"
        if not identity_path.exists():
            continue  # pasta de sistema ou incompleta — silencioso

        post = load_identity(identity_path, item)
        if post:
            valid.append(post)
        else:
            skipped += 1

    # Ordenar por findex (string com zero-padding → ordenação correta)
    valid.sort(key=lambda p: p.findex)

    logger.info(f"✅ {len(valid)} posts carregados.")
    if skipped:
        logger.warning(f"⚠️  {skipped} entradas inválidas ignoradas.")

    return valid
