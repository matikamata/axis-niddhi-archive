# src/transformers/language_router.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Determina disponibilidade de idiomas. Single-HTML strategy (IPFS-safe).

from typing import Dict, Optional
from models import Post


def get_language_alternates(post: Post) -> Dict[str, Optional[str]]:
    """
    Retorna disponibilidade de idiomas para o template.

    Strategy: Single HTML com ambos os conteúdos, toggle via CSS radio inputs.
    Compatível com file://, localhost, IPFS — sem JS obrigatório.
    """
    return {
        "en": "available",
        "pt": "available" if post.has_pt else None,
    }
