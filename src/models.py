# src/models.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Contratos de dados imutáveis. Nunca modificar instâncias após criação.

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List


@dataclass(frozen=True)
class ArtifactMetadata:
    """Metadados de uma versão de idioma (en-US ou pt-BR)."""
    status: str                          # "canonical", "derived", "unknown"
    integrity_sha256: Optional[str]      # Hash do content.html (do identity.json)
    file_path: Path                      # Caminho absoluto para content.html


@dataclass(frozen=True)
class Post:
    """
    Representação interna de um post da CSL.
    Frozen=True: imutável após criação — previne mutação acidental no pipeline.
    """
    pdpn: str                            # Chave primária: TL.BB.003
    section_code: str                   # Agrupamento: TL
    findex: str                          # Ordenação: 0396
    slug_root: str                       # URL: law-of-attraction-habits...
    titles: Dict[str, str]              # {'en': '...', 'pt': '...'}
    artifacts: Dict[str, ArtifactMetadata]  # Keyed por 'en-US', 'pt-BR'
    source_dir: Path                    # Pasta de origem na CSL

    @property
    def has_pt(self) -> bool:
        return "pt-BR" in self.artifacts

    @property
    def title_en(self) -> str:
        return self.titles.get("en", self.slug_root)

    @property
    def title_pt(self) -> str:
        return self.titles.get("pt", self.title_en)

    @property
    def slug(self) -> str:
        return self.slug_root


@dataclass
class Section:
    """Agrupamento de posts por código de seção."""
    code: str
    title: str
    posts: List[Post]

    def __post_init__(self):
        self.posts.sort(key=lambda p: p.findex)
