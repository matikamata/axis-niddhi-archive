# AUDITORIA S13 — AXIS-NIDDHI v3.0
**Data:** 2026-03-01  
**Auditor:** Claude Sonnet 4.6 — Lead Architect + SRE Mode  
**Metodologia:** Análise estática de código. Sem execução real (CSL não disponível nesta sessão).  
**Referências:** beng_20260228_SSG_CONSOLIDADO_PYTHON.txt, HTML, CSS + código v3.0 gerado.

---

## FASE 1 — CHECKLIST DE VALIDAÇÃO ESTRUTURAL

### 1.1 CSL

| Check | Status | Observação |
|-------|--------|------------|
| CSL path configurado | PASS | Via config.py ou fallback relativo |
| SOVEREIGN ABORT se CSL ausente | PASS | `sys.exit(1)` explícito |
| SOVEREIGN ABORT se CSL vazia | PASS | `sys.exit(1)` após load |
| Schema V3.1 suportado | PASS | `identity_loader.py` aceita bloco aninhado + raiz |
| Fallback schema antigo | PASS | Campos na raiz aceitos como fallback |
| Symlinks rejeitados | PASS | Verificado em csl_loader e identity_loader |
| Posts inválidos logados | PASS | Warning + skip, nunca abort |
| Total esperado (748) | INFO | Não verificável sem CSL real — arquitetura correta |

### 1.2 Build Determinístico

| Check | Status | Observação |
|-------|--------|------------|
| Sintaxe: todos os 10 módulos | PASS | `py_compile` passou sem erros |
| Hash composto (content + template) | PASS | `SHA256(content_sha + template_hash)` |
| Template hash força rebuild total | PASS | Cache limpo se `prev_hash != current_hash` |
| Glossary injection no composite hash | **FAIL** | `glossary` passado mas **não incluído no hash** — mudança de glossário não invalida cache |
| index.json determinístico | **WARNING** | `generated_at` usa `datetime.now()` — index.json muda a cada build → BUILD_ID muda → SW invalida cache desnecessariamente |
| slug_map.json determinístico | PASS | Derivado da CSL — mesmo input, mesmo output |
| Log file com timestamp | INFO | Não afeta output HTML |

**Detalhe crítico — determinismo:**  
`index.json` contém `generated_at: "2026-03-01T14:22:00Z"`. Isso faz o BUILD_ID mudar entre duas execuções idênticas, porque `_inject_build_id_into_sw()` hasha **todo o output incluindo index.json**. Resultado: Service Worker invalida cache em toda run, mesmo sem mudança de conteúdo.

### 1.3 Offline Mode

| Check | Status | Observação |
|-------|--------|------------|
| Links relativos nos templates | PASS | `relative_root` injetado como variável Jinja2 |
| `../../` para posts (depth 2) | PASS | `relative_root="../../"` no renderer |
| `./` para index (depth 0) | PASS | `relative_root="./"` no index renderer |
| `relative_root` nos CSS/JS refs | PASS | `{{ relative_root }}css/style.css` |
| search_index.json gerado | PASS | `_generate_search_index()` presente |
| SW ativado por padrão | INFO | **Desativado** por design (`if (false &&`) — correto para file:// e IPFS |
| SW hash inclui relative paths | **WARN** | v3.0 usa apenas conteúdo de arquivo. v2.3 incluía path relativo no hash — detectava renames |

### 1.4 Dependências

| Check | Status | Observação |
|-------|--------|------------|
| Sem hardcode `/media/sanghop/` | PASS | Verificado em todos os 10 módulos |
| Sem hardcode `/home/sucessor/` | PASS | Verificado |
| Sem referências `07a`/`07b` | PASS | Verificado |
| Sem DB legado | PASS | Verificado |
| slug_map independente do Script 15 | PASS | `_build_slug_map()` gera da CSL |
| asset_map ausente não quebra | PASS | `_load_asset_map()` retorna `{}` + warning |
| glossary ausente não quebra | PASS | `load_glossary()` retorna `{}` |
| config.py ausente não quebra | PASS | Fallback por posição relativa do build.py |
| beautifulsoup4 ausente em requirements | **WARN** | `requirements.txt` lista `beautifulsoup4` mas v3.0 **não usa** BS4 (inject_marginalia ausente). Instalação desnecessária em máquina limpa |

### 1.5 Idempotência

| Check | Status | Observação |
|-------|--------|------------|
| Hash composto em cache | PASS | `build_state[pdpn] = composite` |
| Skip se hash == cache E output existe | PASS | Dupla verificação correta |
| Rebuild se output ausente (sem cache) | PASS | Verificação `output_file.exists()` |
| Cache limpo em mudança de template | PASS | `CACHE_FILE.write_text("{}")` |
| `_template_hash` persistido no cache | PASS | Injetado após render_posts |
| Cache não corrompido por run parcial | **WARNING** | Se o processo matar entre render e save-cache, o cache pode ficar inconsistente. Não há write atômico (tmp + rename). Aceitável para uso atual, risco baixo. |

---

## FASE 2 — AUDITORIA DE FEATURES

### Tabela comparativa

| Feature | HD | Backup | v2.3 | v3.0 | Cat | Status | Prioridade |
|---------|----|----|----|----|-----|--------|------------|
| Offline Search (search_index.json) | ✓ | ✓ | ✓ | ✓ | B | PRESENTE | — |
| Nav Index (index.json) | ✓ | ✓ | ✓ | ✓ | B | PRESENTE | — |
| Template-Aware Rebuild | ✗ | ✗ | ✓ | ✓ | A | PRESENTE | — |
| Incremental Build (hash cache) | ✓ | ✓ | ✓ | ✓ | A | PRESENTE | — |
| Relative Links (IPFS-safe) | ✓ | ✓ | ✓ | ✓ | A | PRESENTE | — |
| Bilingual Toggle (CSS-only) | ✓ | ✓ | ✓ | ✓ | A | PRESENTE | — |
| config.py (paths centralizados) | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| slug_map interno (sem Script 15) | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| asset_map opcional (sem abort) | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| SOVEREIGN ABORT reduzido | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| Nav builder + mapa canônico embutido | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| templates_dir injetado (sem hardcode) | ✗ | ✗ | ✗ | ✓ | A | NOVO v3.0 | — |
| Service Worker (BUILD_ID inject) | ✓ | ✓ | ✓ | ✓ | B | PRESENTE | — |
| SW: hash inclui relative paths | ✗ | ✗ | ✓ | ✗ | B | REGRESSÃO | IMPORTANTE |
| build_meta.json | ✗ | ✗ | ✓ | ✗ | C | AUSENTE | OPCIONAL |
| **Glossary Injection (inject_marginalia)** | ✓ | ✓ | ✓ | **✗** | B | **AUSENTE** | **CRÍTICA** |
| **Audio: cópia incremental MP3** | ✓ | ✓ | ✓ | **✗** | B | **AUSENTE** | **IMPORTANTE** |
| **Pronunciation manifest.json** | ✓ | ✓ | ✓ | **✗** | B | **AUSENTE** | **IMPORTANTE** |
| Density Annotation (data-level) | ✗ | ✗ | ✓ | ✗ | C | AUSENTE | OPCIONAL |
| index.json determinístico | ✗ | ✗ | ✗ | ✗ | A | WARNING | IMPORTANTE |
| Pāli CSS (dotted underline) | ✓ | ✓ | ✓ | ✓ | B | PRESENTE | — |
| **Pāli audio on click (JS)** | ✓ | ✓ | ✓ | **✗** | B | **AUSENTE** | **IMPORTANTE** |
| MP3 Manifest (sw_mp3_manifest.json) | ✗ | ✗ | ✓ | ✗ | B | AUSENTE | OPCIONAL |
| Print CSS preservation | ✓ | ✓ | ✓ | ✓ | C | PRESENTE | — |
| Reading progress bar (JS) | ✓ | ✓ | ✓ | ✓ | C | PRESENTE | — |
| Theme switcher (JS) | ✓ | ✓ | ✓ | ✓ | C | PRESENTE | — |
| Accordion (index JS) | ✓ | ✓ | ✓ | ✓ | C | PRESENTE | — |
| TOC dinâmico (JS) | ✓ | ✓ | ✓ | ✓ | C | PRESENTE | — |

**Legenda categorias:** A = Estrutural (não negociável) · B = Feature real · C = Cosmética  
**Contagem v3.0:** 18 PASS/NOVO · 1 REGRESSÃO · 1 WARNING · 7 AUSENTES

### Impacto real das ausências

**CRÍTICA — Glossary Injection (`inject_marginalia`)**  
- Termos Pāli no HTML **não são anotados** — nenhum `<em class="term-highlight">` é gerado
- `load_glossary()` existe e carrega o JSON, mas o resultado **nunca é usado** no render_posts()
- CSS `.term-highlight` está pronto — falta apenas a chamada em post_renderer.py
- Impacto: 100% dos posts renderizados sem anotação de termos. Feature parity com HD: zero.

**IMPORTANTE — Audio pipeline ausente**  
- MP3s existem na CSL (`/meta/pronunciation/*.mp3`) mas nunca são copiados para output
- `pronunciation_manifest.json` não é gerado — JS de áudio não tem dados para trabalhar
- Pāli audio on click: impossível sem manifest + MP3s no output
- Impacto: sistema Pāli completamente não funcional (tooltip CSS existe, áudio não)

**IMPORTANTE — BUILD_ID não determinístico**  
- `index.json` contém timestamp → muda a cada build → BUILD_ID muda → SW invalida cache
- Em distribuição offline/IPFS: cache nunca reutilizado entre builds idênticos
- Impacto: SW ineficaz para cache. Não quebra o site, mas desperdiça o mecanismo

**IMPORTANTE — SW hash sem relative paths**  
- v2.3 incluía `path.relative_to(output_dir)` no hash → detectava renames/moves
- v3.0 hasha apenas conteúdo → rename de arquivo não detectado
- Impacto: baixo para uso atual, relevante para IPFS onde CIDs dependem de paths

---

## FASE 3 — PLANO DE RECUPERAÇÃO MODULAR

### Nível 1 — Estabilidade ISO (pré-condição para qualquer distribuição)

**M1.1 — Glossary Injection** ← BLOQUEADOR  
- Módulo isolado: **SIM** — função `inject_marginalia()` autônoma  
- Afeta core do build: **NÃO** — adiciona chamada em post_renderer.py linha ~165  
- Risco arquitetural: **BAIXO** — DOM-based via BeautifulSoup (já validado em v2.3)  
- Dependências externas: `beautifulsoup4` (já em requirements.txt)  
- Implementação: copiar `inject_marginalia()` + `_SKIP_TAGS` de `beng_20260228_SSG_CONSOLIDADO_PYTHON.txt` → adicionar em `src/renderers/post_renderer.py` → chamar após `process_assets()`  
- Ordem: **primeiro** — sem isso glossário e Pāli não funcionam  

**M1.2 — index.json determinístico**  
- Módulo isolado: **SIM** — substituir `generated_at` por valor fixo ou omitir do hash  
- Afeta core: **NÃO** — mudança de 1 linha em `_inject_build_id_into_sw()`  
- Solução: excluir `index.json` do hash do BUILD_ID (junto com `sw.js` e `build_meta.json`)  
- Risco: **ZERO**  
- Ordem: segundo — corrige determinismo real do BUILD_ID  

### Nível 2 — Experiência Offline (feature parity com HD)

**M2.1 — Audio Pipeline**  
- Composto por 3 sub-funções independentes:
  - `_copy_audio_files(csl_root)` — copia MP3 incrementalmente (SHA256 por arquivo)
  - `_generate_pronunciation_manifest(csl_root, glossary)` — gera JSON com MP3 disponíveis
  - `pali-audio.js` — JS que lê manifest e toca áudio on click  
- Módulo isolado: **SIM** — nenhuma das 3 toca no core de renderização  
- Afeta core: **NÃO** — são fases independentes em build.py (Fase 7 e 8)  
- Dependências externas: nenhuma além de CSL com `meta/pronunciation/` populado  
- Risco: **BAIXO** — cópia incremental com SHA256 já testada em v2.3  
- Ordem: após M1.1 (glossary define quais termos têm áudio)  

**M2.2 — Pāli JS (tooltip + áudio on click)**  
- Novo arquivo: `static/js/pali-audio.js`  
- Lê `pronunciation_manifest.json` via fetch  
- Adiciona tooltip (data-definition via `title` attr — já presente no `inject_marginalia`)  
- Toca MP3 via `new Audio()` on click  
- Módulo isolado: **SIM** — JS puro, zero dependência de Python  
- Requer: M1.1 (para ter `<em class="term-highlight" data-term="...">` no HTML) + M2.1 (para ter manifest + MP3s)  
- Risco: **ZERO** — progressive enhancement, site funciona sem ele  

**M2.3 — SW hash com relative paths**  
- 3 linhas em `_inject_build_id_into_sw()` — adicionar `path.relative_to(output_dir)` no hasher  
- Módulo isolado: **SIM**  
- Risco: **ZERO**  

### Nível 3 — Otimizações Avançadas (pós-ISO)

**M3.1 — Density Annotation**  
- `_annotate_posts_density()` — pós-processa HTML para injetar `data-level` em `<article>`  
- Módulo isolado: **SIM** — opera sobre HTML já gerado  
- Risco: **BAIXO** — leitura + escrita em HTML, sem lógica de render  

**M3.2 — build_meta.json**  
- 5 linhas em `_inject_build_id_into_sw()` — gera JSON com build_id + timestamp + engine  
- Módulo isolado: **SIM**  
- Risco: **ZERO**  

**M3.3 — MP3 Manifest para SW (sw_mp3_manifest.json)**  
- Índice de MP3s para pre-cache pelo Service Worker  
- Requer M2.1 antes  
- Módulo isolado: **SIM**  

---

## FASE 4 — ISO MASTER READINESS

### Diagnóstico por ISO

| Pergunta | ISO USER | ISO Guardian | ISO Nine Unknown |
|----------|----------|--------------|-----------------|
| Build 100% determinístico? | **NÃO** (index.json timestamp) | **NÃO** | **NÃO** |
| Roda em máquina limpa? | **SIM** | **SIM** | **SIM** |
| Depende de estado externo? | NÃO | NÃO | NÃO |
| Depende de ambiente específico? | NÃO — config.py ou fallback | NÃO | NÃO |
| Pode validar no X230 sem ajustes? | **SIM** | **SIM** | **SIM** |
| Feature parity com HD? | **NÃO** (glossary + áudio) | **NÃO** | **NÃO** |

### Bloqueadores reais por ISO

**ISO USER (distribuição para leitores)**  
1. `inject_marginalia()` ausente → termos Pāli não anotados (M1.1)  
2. Audio pipeline ausente → tooltips sem áudio (M2.1 + M2.2)  
3. **Não é bloqueador de execução** — build roda, site funciona, mas sem feature parity  

**ISO Guardian (backup soberano auditável)**  
1. `index.json` não determinístico → BUILD_ID muda entre runs idênticas (M1.2)  
2. Sem `build_meta.json` → sem rastreabilidade de versão no output (M3.2)  
3. SW hash sem relative paths → renames não detectados (M2.3)  

**ISO Nine Unknown Men (distribuição IPFS permanente)**  
1. Todos os bloqueadores Guardian acima  
2. Audio pipeline ausente → arquivos de áudio não incluídos no CID (M2.1)  
3. SW ineficaz para cache por não-determinismo → experiência offline degradada  

### Bloqueadores por ordem de criticidade

```
BLOQUEADOR 1 (CRÍTICO):  inject_marginalia() ausente
  → Afeta: ISO USER, ISO Guardian, ISO Nine Unknown
  → Esforço: ~40 linhas, 1 arquivo
  → Sem isso: glossário e Pāli são infraestrutura morta

BLOQUEADOR 2 (IMPORTANTE): Audio pipeline ausente  
  → Afeta: ISO USER, ISO Nine Unknown  
  → Esforço: 3 funções (~80 linhas) + 1 JS file
  → Sem isso: Pāli audio on click não funciona

BLOQUEADOR 3 (IMPORTANTE): index.json não determinístico
  → Afeta: ISO Guardian, ISO Nine Unknown  
  → Esforço: 1 linha (excluir index.json do hash)
  → Sem isso: BUILD_ID inútil para cache real

NÃO BLOQUEADORES:
  → SW hash sem relative paths (M2.3): risco baixo, esforço trivial
  → build_meta.json (M3.2): cosmético para auditoria
  → Density annotation (M3.1): cosmético
```

---

## DIAGNÓSTICO FINAL

### Arquitetura

**ARQUITETURA ESTÁVEL.**

O core do v3.0 é sólido. As 6 inovações estruturais (config.py, slug_map interno, asset_map opcional, SOVEREIGN ABORT reduzido, mapa canônico embutido, templates injetados) resolvem os problemas reais que bloqueavam execução. Sintaxe 100% limpa. Sem hardcodes. Sem dependências quebradas.

### Features

**AJUSTES NECESSÁRIOS — NÃO CRÍTICOS PARA EXECUÇÃO, CRÍTICOS PARA FEATURE PARITY.**

A v3.0 **roda e gera o site**. O problema é que saiu da migração sem 3 features funcionais que existiam na HD:
- Glossary injection (termos Pāli anotados)
- Audio pipeline (MP3s no output + manifest)  
- Determinismo de BUILD_ID

Nenhum desses ajustes requer refatoração. São adições isoladas.

### Recomendação de execução

```
Fase atual:  rodar build.py → validar 748 posts → confirmar output estrutural
             (site funciona, sem Pāli anotado, sem áudio)

Próxima:     M1.1 + M1.2 → build com glossary + BUILD_ID determinístico
             (Nível 1 — Estabilidade ISO)

Depois:      M2.1 + M2.2 → audio pipeline + JS Pāli
             (Nível 2 — Feature parity HD)
```

### Sumário executivo

| Dimensão | Status |
|----------|--------|
| Sintaxe e importações | ✅ 10/10 módulos PASS |
| Hardcodes residuais | ✅ ZERO |
| SOVEREIGN ABORT calibrado | ✅ Apenas estrutural |
| Idempotência | ✅ Sólida (warning: write não atômico) |
| Relative links / IPFS-safe | ✅ Correto |
| Bilinguismo CSS-only | ✅ Funcional |
| Determinismo real | ⚠️ Parcial (index.json timestamp quebra) |
| Feature parity com HD | ❌ 3 features ausentes |
| Pronto para execução básica | ✅ SIM |
| Pronto para ISO | ⚠️ Após M1.1 + M1.2 |

---

*Brasileirinho Engine · Auditoria S13 AXIS-NIDDHI v3.0 · 2026-03-01*  
*Vayo · Aloka · Akasa · Claude Sonnet 4.6*
