# src/loaders/identity_loader.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Lê e valida identity.json Schema V3.1. Retorna None se inválido — nunca aborta.

import json
import logging
import unicodedata
from pathlib import Path
from typing import Optional, Dict

from models import Post, ArtifactMetadata

logger = logging.getLogger("S13.Loader")

REQUIRED_FIELDS = ["pdpn", "findex", "section_code", "slug_root"]


def _validate_file(path: Path) -> bool:
    """Arquivo existe, é arquivo real (não symlink)."""
    return path.exists() and path.is_file() and not path.is_symlink()


def load_identity(json_path: Path, post_dir: Path) -> Optional[Post]:
    """
    Parseia identity.json e constrói um Post imutável.

    Compatível com Schema V3.1 (aninhado em 'identity': {...}) e
    schemas antigos (campos na raiz).

    Retorna None se validação falhar — nunca lança exceção para o caller.
    """
    try:
        if json_path.is_symlink():
            logger.error(f"⛔ REJEITADO: symlink em {json_path}")
            return None

        data = json.loads(json_path.read_text(encoding="utf-8"))

        # ── Schema V3.1: campos aninhados em 'identity' ────────────────────
        identity_block = data.get("identity", {})

        # Fallback para schemas antigos (campos na raiz, sem bloco identity)
        # NFC normalize — garante forma canônica de diacríticos Pāli nos metadados
        _nfc = lambda s: unicodedata.normalize("NFC", s) if isinstance(s, str) else s

        pdpn        = _nfc(identity_block.get("pdpn")        or data.get("pdpn"))
        findex      = identity_block.get("findex")      or data.get("findex", "0000")
        section_code= identity_block.get("section_code")or data.get("section_code")
        slug_root   = _nfc(identity_block.get("slug_root")
                       or data.get("slug_en")
                       or data.get("slug", ""))

        # Inferir section_code do pdpn se ausente
        if not section_code and pdpn and "." in pdpn:
            section_code = pdpn.split(".")[1]

        # Validação mínima
        for fname, val in [("pdpn", pdpn), ("section_code", section_code)]:
            if not val:
                logger.warning(f"⚠️  PULADO: campo '{fname}' ausente em {json_path}")
                return None

        # ── Títulos ─────────────────────────────────────────────────────────
        titles_block = data.get("titles", {})
        titles = {
            "en": _nfc(titles_block.get("en") or data.get("title_en") or slug_root),
            "pt": _nfc(titles_block.get("pt") or data.get("title_pt") or ""),
        }

        # ── Artefatos ────────────────────────────────────────────────────────
        artifacts_data = data.get("artifacts", {})
        artifacts: Dict[str, ArtifactMetadata] = {}

        # EN-US: obrigatório
        en_path = post_dir / "source" / "en-US" / "content.html"
        if _validate_file(en_path):
            en_meta = artifacts_data.get("en-US", {})
            artifacts["en-US"] = ArtifactMetadata(
                status=en_meta.get("status", "canonical"),
                integrity_sha256=en_meta.get("integrity_sha256"),
                file_path=en_path,
            )
        else:
            logger.error(f"❌ INVÁLIDO: content.html EN ausente para {pdpn}")
            return None

        # PT-BR: opcional
        pt_path = post_dir / "source" / "pt-BR" / "content.html"
        if _validate_file(pt_path):
            pt_meta = artifacts_data.get("pt-BR", {})
            artifacts["pt-BR"] = ArtifactMetadata(
                status=pt_meta.get("status", "derived"),
                integrity_sha256=pt_meta.get("integrity_sha256"),
                file_path=pt_path,
            )

        return Post(
            pdpn=pdpn,
            section_code=section_code,
            findex=str(findex).zfill(4),
            slug_root=slug_root,
            titles=titles,
            artifacts=artifacts,
            source_dir=post_dir,
        )

    except json.JSONDecodeError:
        logger.error(f"💥 JSON corrompido: {json_path}")
        return None
    except Exception as e:
        logger.exception(f"💥 Erro inesperado em {json_path}: {e}")
        return None
