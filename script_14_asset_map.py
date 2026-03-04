#!/usr/bin/env python3
"""
💎 BRASILEIRINHO ENGINE — Script 14 (Asset Map)
================================================
Nome:   Asset Map Generator
Versão: 1.0.0 — AXIS-NIDDHI Edition
Data:   2026-03-01

Função:
  Escaneia todos os HTMLs da CSL (09-csl/) em busca de URLs WP:
    http://localhost/wp-content/uploads/...
    http://127.0.0.1/wp-content/uploads/...
    /wp-content/uploads/...

  Gera asset_map.json:
    { "URL_WP_original": "assets/images/filename.ext" }

  Opcional: copia as imagens do SanDisk ou de um diretório de origem
  para OUTPUT_DIR/assets/images/ se encontradas.

Nunca aborta. Comportamento:
  - URL encontrada no HTML → entrada no asset_map
  - Imagem física encontrada → copiada incrementalmente
  - Imagem não encontrada → entrada no map com flag "missing: true"
  - Script 13 já faz passthrough se URL não estiver no map
"""

import sys
import re
import json
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, Set
from urllib.parse import urlparse, unquote

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE.parent / "scripts"))

try:
    from config import (
        DIR_09_CSL    as CSL_DIR_CFG,
        DIR_13_SSG    as SSG_DIR_CFG,
        DIR_14_ASSETS as ASSETS_DIR_CFG,
        LOG_DIR       as LOG_DIR_CFG,
    )
    CSL_DIR    = Path(CSL_DIR_CFG)
    OUTPUT_DIR = Path(SSG_DIR_CFG)
    ASSETS_DIR = Path(ASSETS_DIR_CFG)
    LOG_DIR    = Path(LOG_DIR_CFG)
    _CFG = True
except ImportError:
    _PIPELINE  = _HERE.parent
    CSL_DIR    = _PIPELINE / "09-csl"
    OUTPUT_DIR = _PIPELINE / "13-ssg"
    ASSETS_DIR = _PIPELINE / "14-assets"
    LOG_DIR    = _PIPELINE / "logs"
    _CFG = False

ASSET_MAP_FILE  = ASSETS_DIR / "asset_map.json"
IMAGES_OUT_DIR  = OUTPUT_DIR / "assets" / "images"

# Diretórios de origem de imagens (busca em ordem)
IMAGE_SOURCE_DIRS = [
    Path("/media/sanghop/SanDisk32GB/AKKHAYA-NIDHI/13-static-site/assets/images"),
    Path("/media/sanghop/SanDisk32GB/AKKHAYA-NIDHI/13-static-site/assets"),
    Path("/media/sanghop/BrasileirinhoHD/Brasileirinho_Engine_v2/pipeline/13-static-site/assets/images"),
    CSL_DIR / "meta" / "images",
]

# Padrões de URL WP a detectar
_WP_PATTERNS = [
    re.compile(r'(?:https?://(?:localhost|127\.0\.0\.1)(?::\d+)?)?(/wp-content/uploads/[^\s"\'<>]+)', re.IGNORECASE),
    re.compile(r'src=["\']([^"\']*wp-content/uploads/[^"\']+)["\']', re.IGNORECASE),
    re.compile(r'href=["\']([^"\']*wp-content/uploads/[^"\']+)["\']', re.IGNORECASE),
]

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "S14_asset_map.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("S14")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def extract_wp_urls(html: str) -> Set[str]:
    """Extrai todas as URLs WP encontradas em um HTML."""
    found = set()
    for pattern in _WP_PATTERNS:
        for m in pattern.finditer(html):
            url = m.group(1)
            # Normalizar: garantir path absoluto WP
            if not url.startswith("/"):
                parsed = urlparse(url)
                url = parsed.path
            found.add(url)
    return found


def url_to_filename(wp_path: str) -> str:
    """
    /wp-content/uploads/2023/04/dhamma-nidhi.jpg
    → dhamma-nidhi.jpg
    """
    return Path(unquote(wp_path)).name


def find_image_source(filename: str) -> Path | None:
    """Busca o arquivo físico nos diretórios de origem."""
    for src_dir in IMAGE_SOURCE_DIRS:
        if not src_dir.exists():
            continue
        # Busca direta
        candidate = src_dir / filename
        if candidate.exists():
            return candidate
        # Busca recursiva (imagens podem estar em subpastas)
        matches = list(src_dir.rglob(filename))
        if matches:
            return matches[0]
    return None


def copy_image_incremental(src: Path, dst: Path) -> bool:
    """Copia imagem apenas se necessário (SHA256). Retorna True se copiou."""
    if dst.exists():
        if _file_sha256(src) == _file_sha256(dst):
            return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    logger.info("=" * 60)
    logger.info("💎 BRASILEIRINHO ENGINE — Script 14 (Asset Map)")
    logger.info(f"   CSL:    {CSL_DIR}")
    logger.info(f"   Output: {OUTPUT_DIR}")
    logger.info(f"   Config: {'config.py' if _CFG else 'fallback'}")
    logger.info("=" * 60)

    if not CSL_DIR.exists():
        logger.critical(f"❌ CSL não encontrada: {CSL_DIR}")
        return 1

    # ── 1. Escanear CSL em busca de URLs WP ───────────────────────────────
    logger.info("▶ Fase 1/4: Escaneando CSL para URLs WP...")
    all_wp_urls: Set[str] = set()
    html_files = list(CSL_DIR.rglob("*.html"))
    logger.info(f"   {len(html_files)} arquivos HTML na CSL")

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore")
            urls = extract_wp_urls(content)
            all_wp_urls.update(urls)
        except Exception as e:
            logger.warning(f"⚠️  {html_file.name}: {e}")

    logger.info(f"   {len(all_wp_urls)} URLs WP únicas encontradas")

    if not all_wp_urls:
        logger.info("   Nenhuma URL WP encontrada — asset_map.json será vazio.")
        logger.info("   (Posts podem usar URLs absolutas já resolvidas)")

    # ── 2. Construir asset_map ─────────────────────────────────────────────
    logger.info("▶ Fase 2/4: Construindo asset_map...")
    asset_map: Dict[str, str] = {}
    missing: list = []
    copied = skipped = 0

    IMAGES_OUT_DIR.mkdir(parents=True, exist_ok=True)

    for wp_url in sorted(all_wp_urls):
        filename = url_to_filename(wp_url)
        if not filename:
            continue

        local_path = f"assets/images/{filename}"
        asset_map[wp_url] = local_path

        # Tentar copiar a imagem física
        src = find_image_source(filename)
        if src:
            dst = OUTPUT_DIR / local_path
            try:
                if copy_image_incremental(src, dst):
                    copied += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.warning(f"⚠️  Não foi possível copiar {filename}: {e}")
                missing.append(wp_url)
        else:
            missing.append(wp_url)

    logger.info(f"   asset_map: {len(asset_map)} entradas")
    logger.info(f"   Imagens:   {copied} copiadas | {skipped} sem alteração | {len(missing)} não encontradas")

    # ── 3. Salvar asset_map.json ───────────────────────────────────────────
    logger.info("▶ Fase 3/4: Salvando asset_map.json...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    ASSET_MAP_FILE.write_text(
        json.dumps(asset_map, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    logger.info(f"   ✅ {ASSET_MAP_FILE}")

    # ── 4. Relatório ──────────────────────────────────────────────────────
    logger.info("▶ Fase 4/4: Relatório...")
    if missing:
        logger.warning(f"⚠️  {len(missing)} imagens não encontradas nos diretórios de origem:")
        for url in missing[:10]:
            logger.warning(f"   → {url}")
        if len(missing) > 10:
            logger.warning(f"   ... e mais {len(missing) - 10}")
        logger.warning("   Script 13 aplicará passthrough para essas URLs.")

    logger.info("=" * 60)
    logger.info("✨ Script 14 COMPLETO")
    logger.info(f"   URLs mapeadas:      {len(asset_map)}")
    logger.info(f"   Imagens copiadas:   {copied}")
    logger.info(f"   Imagens ausentes:   {len(missing)}")
    logger.info(f"   asset_map.json:     {ASSET_MAP_FILE}")
    logger.info("=" * 60)
    logger.info("▶ Próximo passo:")
    logger.info("   python3 build.py  ← rebuild com assets resolvidos")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
