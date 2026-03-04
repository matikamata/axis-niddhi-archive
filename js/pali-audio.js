/**
 * 💎 BRASILEIRINHO ENGINE — AXIS-NIDDHI v3.0 | PATCH S14 M2.2
 * pali-audio.js — Sistema Pāli: tooltip + áudio on click
 *
 * Axiomas:
 * - Progressive enhancement: site 100% funcional sem este arquivo
 * - Lê pronunciation_manifest.json via fetch (relativo à raiz do site)
 * - Funciona em file://, localhost, IPFS (fetch de JSON local)
 * - Zero dependências externas
 */

(function () {
  "use strict";

  /**
   * Calcula a URL base relativa ao documento atual.
   * - pages/PDPN/index.html → ../../
   * - index.html             → ./
   */
  function _getBaseUrl() {
    var path = window.location.pathname;
    if (path.indexOf("/pages/") !== -1) {
      return "../../";
    }
    return "./";
  }

  function initPaliAudio() {
    var base = _getBaseUrl();
    var manifestUrl = base + "pronunciation_manifest.json";

    fetch(manifestUrl)
      .then(function (r) {
        if (!r.ok) throw new Error("manifest not found");
        return r.json();
      })
      .then(function (manifest) {
        if (!manifest || typeof manifest !== "object") return;

        var terms = document.querySelectorAll(".term-highlight[data-term]");
        if (!terms.length) return;

        terms.forEach(function (el) {
          var term = el.getAttribute("data-term");
          var audioPath = manifest[term];

          if (!audioPath) return;

          // Sinalizar que áudio está disponível
          el.setAttribute("data-audio", base + audioPath);
          el.classList.add("has-audio");
          el.title = (el.title ? el.title + " · " : "") + "🔊 clique para ouvir";

          el.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var src = el.getAttribute("data-audio");
            if (!src) return;
            // Parar qualquer áudio em curso
            if (window._paliCurrentAudio) {
              window._paliCurrentAudio.pause();
              window._paliCurrentAudio.currentTime = 0;
            }
            var audio = new Audio(src);
            window._paliCurrentAudio = audio;
            audio.play().catch(function () {
              // Autoplay bloqueado em alguns browsers — silencioso
            });
          });
        });
      })
      .catch(function () {
        // Manifest ausente ou fetch bloqueado (ex: IPFS sem servidor)
        // Site continua funcional — tooltips CSS permanecem
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPaliAudio);
  } else {
    initPaliAudio();
  }
}());
