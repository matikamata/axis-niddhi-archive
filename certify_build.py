#!/usr/bin/env python3
"""
💎 BRASILEIRINHO ENGINE — certify_build.py
==========================================
ISO Guardian Certification — Reproducible Build Verifier
Versão: 1.0.0
Data:   2026-03-01

Função:
  1. Lê build_meta.json para capturar BUILD_ID da última run
  2. Computa SHA256 canônico da árvore de output (tree_sha256)
  3. Coleta estatísticas do output
  4. Gera CERTIFICATE.json

Critério de sucesso:
  Duas execuções consecutivas sem mudança de conteúdo →
    BUILD_ID idêntico
    tree_sha256 idêntico

Exclusões do hash (mesmas do _inject_build_id_into_sw):
  - sw.js, build_meta.json, index.json  (conteúdo não determinístico)
  - *.py, *.log, *.tmp                  (artefatos de execução)
  - logs/, cache/, __pycache__/         (pastas de estado interno)
  - CERTIFICATE.json                    (auto-referencial)
"""

import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ── Paths (espelha build.py) ─────────────────────────────────────────────────
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE.parent / "scripts"))

try:
    from config import DIR_13_SSG as OUTPUT_DIR_CFG
    OUTPUT_DIR = Path(OUTPUT_DIR_CFG)
except ImportError:
    OUTPUT_DIR = _HERE  # build.py e certify_build.py vivem no mesmo dir

CSL_DIR    = OUTPUT_DIR.parent / "09-csl"
META_DIR   = OUTPUT_DIR.parent / "metadata"
AUDIO_DIR  = OUTPUT_DIR / "assets" / "audio" / "en-US"
CERT_FILE  = OUTPUT_DIR / "CERTIFICATE.json"
BUILD_META = OUTPUT_DIR / "build_meta.json"

# ── Exclusões (idênticas ao _inject_build_id_into_sw) ────────────────────────
EXCLUDE_NAMES = {"sw.js", "build_meta.json", "index.json", "CERTIFICATE.json"}
EXCLUDE_EXTS  = {".py", ".tmp", ".log"}
EXCLUDE_DIRS  = {"logs", "cache", "__pycache__"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_tree_sha256(root: Path) -> str:
    """
    SHA256 canônico da árvore de output.
    Ordem: sorted() alfabético por path relativo.
    Entrada do hash por arquivo: rel_path + conteúdo.
    Exclusões: idênticas ao BUILD_ID.
    """
    hasher = hashlib.sha256()
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if f.name in EXCLUDE_NAMES:
            continue
        if f.suffix in EXCLUDE_EXTS:
            continue
        if any(part in EXCLUDE_DIRS for part in f.parts):
            continue
        try:
            rel = str(f.relative_to(root)).encode()
            hasher.update(rel)
            hasher.update(f.read_bytes())
        except Exception as e:
            print(f"  ⚠️  Não foi possível hashear {f.name}: {e}")
    return hasher.hexdigest()


def count_html_posts(output_dir: Path) -> int:
    pages_dir = output_dir / "pages"
    if not pages_dir.exists():
        return 0
    return sum(1 for d in pages_dir.iterdir() if d.is_dir() and (d / "index.html").exists())


def count_pt_br(output_dir: Path) -> int:
    """Conta posts com conteúdo PT-BR ativo no HTML."""
    pages_dir = output_dir / "pages"
    if not pages_dir.exists():
        return 0
    count = 0
    for d in pages_dir.iterdir():
        f = d / "index.html"
        if f.exists():
            try:
                if 'lang="pt"' in f.read_text(encoding="utf-8", errors="ignore"):
                    count += 1
            except Exception:
                pass
    return count


def count_glossary_terms(output_dir: Path) -> int:
    manifest = output_dir / "pronunciation_manifest.json"
    if not manifest.exists():
        return 0
    try:
        # glossary_terms = todos os termos em pronunciation_manifest
        # proxy: usar search_index não — usar manifest de áudio como lower bound
        # fonte canônica: META_DIR/glossary_config.json
        glossary_path = output_dir.parent / "metadata" / "glossary_config.json"
        if glossary_path.exists():
            data = json.loads(glossary_path.read_text(encoding="utf-8"))
            return len(data.get("entries", data if isinstance(data, dict) else []))
    except Exception:
        pass
    return 0


def main() -> int:
    print("=" * 60)
    print("💎 BRASILEIRINHO ENGINE — ISO Guardian Certification")
    print(f"   Output: {OUTPUT_DIR}")
    print("=" * 60)

    # ── 1. Verificar que output existe ───────────────────────────────────────
    if not OUTPUT_DIR.exists():
        print(f"❌ OUTPUT_DIR não encontrado: {OUTPUT_DIR}")
        print("   Execute python3 build.py primeiro.")
        return 1

    if not BUILD_META.exists():
        print(f"❌ build_meta.json não encontrado.")
        print("   Execute python3 build.py com PATCH S15 primeiro.")
        return 1

    # ── 2. Ler build_meta.json ───────────────────────────────────────────────
    try:
        meta = json.loads(BUILD_META.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Erro ao ler build_meta.json: {e}")
        return 1

    build_id = meta.get("build_id", "unknown")
    engine   = meta.get("engine", "unknown")
    print(f"\n▶ BUILD_ID (build_meta):  {build_id}")
    print(f"  Engine:                 {engine}")

    # ── 3. Computar tree_sha256 ──────────────────────────────────────────────
    print("\n▶ Computando tree_sha256...")
    tree_sha = compute_tree_sha256(OUTPUT_DIR)
    print(f"  tree_sha256: {tree_sha}")

    # ── 4. Estatísticas ──────────────────────────────────────────────────────
    print("\n▶ Coletando estatísticas...")

    posts_total = count_html_posts(OUTPUT_DIR)
    pt_br_count = count_pt_br(OUTPUT_DIR)

    glossary_terms = count_glossary_terms(OUTPUT_DIR)
    if glossary_terms == 0:
        # fallback: ler do search_index
        si = OUTPUT_DIR / "search_index.json"
        if si.exists():
            try:
                posts_total = posts_total or len(json.loads(si.read_text()))
            except Exception:
                pass

    audio_files = len(list(AUDIO_DIR.glob("*.mp3"))) if AUDIO_DIR.exists() else 0

    audio_terms = 0
    manifest_path = OUTPUT_DIR / "pronunciation_manifest.json"
    if manifest_path.exists():
        try:
            audio_terms = len(json.loads(manifest_path.read_text(encoding="utf-8")))
        except Exception:
            pass

    # Total de arquivos e tamanho
    all_files = [f for f in OUTPUT_DIR.rglob("*") if f.is_file()]
    total_files = len(all_files)
    total_size  = sum(f.stat().st_size for f in all_files)

    print(f"  Posts HTML:      {posts_total}")
    print(f"  Posts PT-BR:     {pt_br_count}")
    print(f"  Glossary terms:  {glossary_terms}")
    print(f"  Audio files:     {audio_files}")
    print(f"  Audio terms:     {audio_terms}")
    print(f"  Total files:     {total_files}")
    print(f"  Total size:      {total_size / 1024 / 1024:.1f} MB")

    # ── 5. Verificar contra CERTIFICATE anterior (se existir) ─────────────
    prev_build_id   = None
    prev_tree_sha   = None
    if CERT_FILE.exists():
        try:
            prev = json.loads(CERT_FILE.read_text(encoding="utf-8"))
            prev_build_id = prev.get("build_id")
            prev_tree_sha = prev.get("tree_sha256")
        except Exception:
            pass

    # ── 6. Gerar CERTIFICATE.json ────────────────────────────────────────────
    certificate = {
        "engine":          engine,
        "build_id":        build_id,
        "tree_sha256":     tree_sha,
        "certified_at":    _utc_now(),
        "posts":           posts_total,
        "pt_br":           pt_br_count,
        "glossary_terms":  glossary_terms,
        "audio_files":     audio_files,
        "audio_terms":     audio_terms,
        "total_files":     total_files,
        "total_size_mb":   round(total_size / 1024 / 1024, 2),
    }

    CERT_FILE.write_text(
        json.dumps(certificate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ── 7. Veredicto ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)

    if prev_build_id is None:
        print("📋 CERTIFICATE.json gerado (primeira certificação).")
        print("   Execute novamente para verificar determinismo.")
        verdict = "FIRST_RUN"
    else:
        build_ok = (build_id == prev_build_id)
        tree_ok  = (tree_sha == prev_tree_sha)

        print(f"  BUILD_ID:    {'✅ IDÊNTICO' if build_ok else '❌ DIVERGIU'}")
        print(f"    anterior:  {prev_build_id}")
        print(f"    atual:     {build_id}")
        print(f"  tree_sha256: {'✅ IDÊNTICO' if tree_ok else '❌ DIVERGIU'}")
        print(f"    anterior:  {prev_tree_sha[:32]}...")
        print(f"    atual:     {tree_sha[:32]}...")

        if build_ok and tree_ok:
            verdict = "PASSED"
            print("\n✅ REPRODUCIBLE_BUILD = PASSED")
            print("   ISO Guardian: aprovado.")
        else:
            verdict = "FAILED"
            print("\n❌ REPRODUCIBLE_BUILD = FAILED")
            if not build_ok:
                print("   → BUILD_ID divergiu: arquivo não-determinístico no output.")
            if not tree_ok:
                print("   → tree_sha256 divergiu: conteúdo ou estrutura mudou.")

    certificate["verdict"] = verdict
    CERT_FILE.write_text(
        json.dumps(certificate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n   CERTIFICATE.json → {CERT_FILE}")
    print("=" * 60)

    return 0 if verdict in ("PASSED", "FIRST_RUN") else 1


if __name__ == "__main__":
    sys.exit(main())
