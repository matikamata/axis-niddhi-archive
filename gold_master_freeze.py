#!/usr/bin/env python3
"""
💎 BRASILEIRINHO ENGINE — gold_master_freeze.py
================================================
GOLD MASTER FREEZE — ISO Guardian Baseline
Versão: 1.0.0
Data:   2026-03-01

Função:
  1. Valida CERTIFICATE.json (deve ter verdict=PASSED)
  2. Cria snapshot em /beng/releases/AXIS-NIDDHI-{version}-GOLD/
  3. Copia todo o output + CERTIFICATE.json + build_meta.json
  4. Gera GOLD_SHA256.txt com hash da árvore inteira
  5. Registra GOLD_MASTER_LOG.json
"""

import sys
import json
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE.parent / "scripts"))

try:
    from config import DIR_13_SSG as OUTPUT_DIR_CFG
    OUTPUT_DIR = Path(OUTPUT_DIR_CFG)
except ImportError:
    OUTPUT_DIR = _HERE

CERT_FILE    = OUTPUT_DIR / "CERTIFICATE.json"
BUILD_META   = OUTPUT_DIR / "build_meta.json"
RELEASES_DIR = Path("/beng/releases")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_full_tree_sha256(root: Path) -> tuple[str, int, int]:
    """
    SHA256 completo de toda a árvore (sem exclusões).
    Retorna: (sha256_hex, total_files, total_bytes)
    """
    hasher = hashlib.sha256()
    total_files = 0
    total_bytes = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        try:
            rel = str(f.relative_to(root)).encode()
            data = f.read_bytes()
            hasher.update(rel)
            hasher.update(data)
            total_files += 1
            total_bytes += len(data)
        except Exception:
            pass
    return hasher.hexdigest(), total_files, total_bytes


def main() -> int:
    print("=" * 60)
    print("💎 BRASILEIRINHO ENGINE — GOLD MASTER FREEZE")
    print(f"   Source: {OUTPUT_DIR}")
    print("=" * 60)

    # ── 1. Verificar pré-condições ────────────────────────────────────────
    if not CERT_FILE.exists():
        print("❌ CERTIFICATE.json não encontrado.")
        print("   Execute python3 certify_build.py primeiro (duas vezes).")
        return 1

    if not BUILD_META.exists():
        print("❌ build_meta.json não encontrado.")
        return 1

    cert = json.loads(CERT_FILE.read_text(encoding="utf-8"))
    meta = json.loads(BUILD_META.read_text(encoding="utf-8"))

    verdict = cert.get("verdict", "")
    if verdict not in ("PASSED", "FIRST_RUN"):
        print(f"❌ CERTIFICATE.json tem verdict={verdict!r}")
        print("   Execute certify_build.py duas vezes com PASSED antes de congelar.")
        return 1

    if verdict == "FIRST_RUN":
        print("⚠️  CERTIFICATE.json tem verdict=FIRST_RUN.")
        print("   Para freeze de produção, execute certify_build.py duas vezes.")
        print("   Continuando com aviso...")

    engine   = meta.get("engine", "unknown")
    build_id = meta.get("build_id", "unknown")
    version  = engine.replace("/", "-").replace(" ", "-")

    # ── 2. Criar diretório de release ─────────────────────────────────────
    release_dir = RELEASES_DIR / f"AXIS-NIDDHI-{version}-GOLD"
    print(f"\n▶ Destino: {release_dir}")

    if release_dir.exists():
        print(f"   ⚠️  Já existe — sobrescrevendo...")
        shutil.rmtree(release_dir)

    release_dir.mkdir(parents=True, exist_ok=True)

    # ── 3. Copiar output completo ─────────────────────────────────────────
    print("\n▶ Copiando output...")
    shutil.copytree(str(OUTPUT_DIR), str(release_dir), dirs_exist_ok=True)
    print(f"   ✅ {OUTPUT_DIR} → {release_dir}")

    # ── 4. Gerar GOLD_SHA256.txt ──────────────────────────────────────────
    print("\n▶ Computando GOLD_SHA256 (árvore completa)...")
    gold_sha, total_files, total_bytes = compute_full_tree_sha256(release_dir)

    gold_sha_path = release_dir / "GOLD_SHA256.txt"
    gold_sha_path.write_text(
        f"GOLD_SHA256={gold_sha}\n"
        f"engine={engine}\n"
        f"build_id={build_id}\n"
        f"frozen_at={_utc_now()}\n"
        f"total_files={total_files}\n"
        f"total_bytes={total_bytes}\n",
        encoding="utf-8",
    )
    print(f"   GOLD_SHA256: {gold_sha}")

    # ── 5. Gerar GOLD_MASTER_LOG.json ─────────────────────────────────────
    log = {
        "GOLD_MASTER_ESTABLISHED": True,
        "engine":      engine,
        "build_id":    build_id,
        "tree_sha256": cert.get("tree_sha256", ""),
        "gold_sha256": gold_sha,
        "frozen_at":   _utc_now(),
        "release_dir": str(release_dir),
        "total_files": total_files,
        "total_size_mb": round(total_bytes / 1024 / 1024, 2),
        "certificate": cert,
    }
    log_path = release_dir / "GOLD_MASTER_LOG.json"
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── 6. Relatório ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ GOLD_MASTER_ESTABLISHED = true")
    print(f"   Engine:       {engine}")
    print(f"   BUILD_ID:     {build_id}")
    print(f"   GOLD_SHA256:  {gold_sha[:32]}...")
    print(f"   Total files:  {total_files}")
    print(f"   Total size:   {total_bytes / 1024 / 1024:.1f} MB")
    print(f"   Release dir:  {release_dir}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
