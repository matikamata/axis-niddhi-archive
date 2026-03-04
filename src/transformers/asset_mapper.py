# src/transformers/asset_mapper.py
# 💎 BRASILEIRINHO ENGINE — Script 13 AXIS-NIDDHI v3.0
# Reescreve URLs de assets localhost → caminhos relativos.
# asset_map é OPCIONAL — opera em modo passthrough se vazio.

import logging
from typing import Dict

logger = logging.getLogger("S13.AssetMapper")


def process_assets(
    html_content: str,
    pdpn: str,
    asset_map: Dict[str, str],
) -> str:
    """
    Substitui URLs de assets localhost por caminhos relativos.

    Args:
        html_content: HTML bruto do post.
        pdpn: ID do post (para logging).
        asset_map: { 'http://localhost/.../img.jpg' → 'assets/hash/img.jpg' }
                   Vazio = modo passthrough (sem substituição, sem erro).

    Returns:
        HTML com URLs reescritas. Se asset_map vazio, retorna original intacto.
    """
    if not html_content:
        return ""

    if not asset_map:
        return html_content  # Passthrough — asset_map opcional

    if "localhost" not in html_content:
        return html_content  # Otimização: skip se não há URLs localhost

    replacements = 0
    for original_url, web_path in asset_map.items():
        if original_url in html_content:
            # Posts estão em pages/PDPN/index.html → ../../ chega na raiz
            relative_path = f"../../{web_path}"
            html_content = html_content.replace(original_url, relative_path)
            replacements += 1

    if replacements:
        logger.debug(f"📦 {pdpn}: {replacements} asset(s) resolvido(s).")

    # Logar assets restantes não resolvidos (sem spam)
    remaining = html_content.count("localhost")
    if remaining:
        logger.debug(f"⚠️  {pdpn}: {remaining} referência(s) localhost restante(s) após mapeamento.")

    return html_content
