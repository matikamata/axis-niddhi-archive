# src/transformers/link_resolver.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Resolve links internos: http://localhost/... → ../../pages/PDPN/index.html
# slug_map gerado internamente — zero dependência de Script 15.

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger("S13.LinkResolver")

# Padrão: captura qualquer URL localhost do brasileirinho
_LINK_PATTERN = re.compile(
    r'href=["\']https?://localhost(?:/beng_\w+|/brasileirinho)?/([^"\'>\s]+)["\']',
    re.IGNORECASE,
)


class LinkResolver:
    """
    Converte links internos absolutos em caminhos relativos IPFS-safe.

    O slug_map é construído pela CSL — sem dependência de arquivos externos.
    Formato: { slug_root: pdpn }  (para busca por slug)
             { pdpn: slug_root }  (para geração de URLs)
    """

    def __init__(self, slug_map: Dict[str, str]):
        """
        Args:
            slug_map: Dict { pdpn → slug_root } gerado a partir da CSL.
        """
        self._pdpn_to_slug: Dict[str, str] = slug_map
        # Inverso: slug → pdpn (para resolução de links)
        self._slug_to_pdpn: Dict[str, str] = {v: k for k, v in slug_map.items()}
        logger.info(f"🔗 LinkResolver: {len(self._slug_to_pdpn)} slugs indexados.")

    def resolve_links(self, html_content: str, current_pdpn: str) -> str:
        """
        Substitui hrefs localhost por caminhos relativos.

        Profundidade de output: pages/PDPN/index.html → relative_root = ../../
        """
        if not html_content or "localhost" not in html_content:
            return html_content

        def _replacer(match: re.Match) -> str:
            original = match.group(0)
            path_suffix = match.group(1).strip("/")

            # Extrair slug da URL: ultimo segmento não-vazio
            parts = [p for p in path_suffix.split("/") if p]
            if not parts:
                return original

            target_slug = parts[-1]

            # Tentar resolver pelo slug
            target_pdpn = self._slug_to_pdpn.get(target_slug)
            if target_pdpn:
                return f'href="../../pages/{target_pdpn}/index.html"'

            # Tentar por pdpn diretamente (se a URL contém o pdpn)
            for part in parts:
                if part in self._pdpn_to_slug:
                    return f'href="../../pages/{part}/index.html"'

            # Não resolvido: preservar original (link externo ou categoria)
            logger.debug(f"Link não resolvido: '{target_slug}' em {current_pdpn}")
            return original

        return _LINK_PATTERN.sub(_replacer, html_content)

    def get_url(self, pdpn: str, relative_root: str = "../../") -> str:
        """Retorna URL relativa de um post pelo seu PDPN."""
        return f"{relative_root}pages/{pdpn}/index.html"
