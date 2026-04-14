---
name: mcp-refactor-workflow
description: "Use when you need code refactoring workflow with context-refactor MCP tools. Covers refatoracao/refactoring, context budget, code smells detection, candidate selection, and refactor plan generation with validation and testing checkpoints."
license: MIT
metadata:
  author: GitHub Copilot
  version: "1.0.0"
  language: "pt-BR + en-US"
---

# MCP Refactor Workflow Skill

Specialist workflow to run refactoring analysis using the context-refactor MCP.

Fluxo especialista para executar analise e planejamento de refatoracao usando o MCP do context-refactor.

## When To Apply / Quando Aplicar

Use this skill when you need one of these outcomes:
- Check if a repository fits an LLM context window.
- Detect refactor candidates by profile (legacy, heuristics, blend).
- Detect code smells with dependency-aware heuristics.
- Generate an executable refactor plan with ordered steps.
- Compare analysis depth/cost before running expensive scans.

Use esta skill quando voce precisa de um destes resultados:
- Validar se o repositorio cabe no contexto da LLM.
- Detectar candidatos de refatoracao por perfil (legacy, heuristics, blend).
- Detectar code smells com heuristicas e dependencias.
- Gerar um plano executavel com passos ordenados.
- Comparar profundidade/custo antes de rodar analises caras.

## MCP Tools Covered / Tools MCP Cobertas

- `analyze_project`: Full analysis (budget + recommendations + refactor plan).
- `context_budget`: Fast preflight only (fit, overflow, total tokens).
- `detect_refactor_candidates_tool`: Recommendations without full plan.
- `generate_refactor_plan_tool`: Build plan from recommendations.
- `detect_code_smells`: Heuristic smells per file with ranking.
- `generate_refactor_suggestions`: One-shot heuristics + plan.

Canonical entry points in codebase:
- `mcp_server/tools.py`
- `mcp_server/tools_analysis.py`
- `mcp_server/tools_heuristics.py`

## Decision Flow / Fluxo de Decisao

1. Preflight first.
   - Call `context_budget` when repository size is unknown or likely large.
   - If `fits_context` is true and objective is only sizing, stop.
   - If overflow is high, apply exclusions and rerun before deeper analysis.

2. Choose analysis profile.
   - `legacy`: faster baseline candidate detection.
   - `heuristics`: richer smell detection and prioritization.
   - `blend`: combine both when confidence and coverage are required.

3. Choose execution mode by objective.
   - Need complete report now: `analyze_project`.
   - Need candidates only: `detect_refactor_candidates_tool`.
   - Need smells + prioritization: `detect_code_smells`.
   - Need one-shot heuristics and plan: `generate_refactor_suggestions`.
   - Already have recommendations and want plan only: `generate_refactor_plan_tool`.

4. Enable dependencies only when needed.
   - Turn on dependency analysis for coupling-driven refactor scenarios.
   - Keep dependency mode light or disabled for quick iterations.

## Standard Workflow / Workflow Padrao

### Phase 1 - Preflight

Required checks before any expensive tool call:
- `project_path` exists and is readable.
- `llm_context_size` is coherent with target model.
- `safety_margin` is between 0 and 1.
- Profiles and modes are valid for the selected tool.

Recommended first call:
- `context_budget` with `project_path`, `llm_context_size`, and `safety_margin`.

### Phase 2 - Analysis And Detection

Pick one branch:
- Full branch: `analyze_project`.
- Candidate branch: `detect_refactor_candidates_tool`.
- Heuristic branch: `detect_code_smells`.
- One-shot branch: `generate_refactor_suggestions`.

Apply filters early to reduce noise and cost:
- `exclude_dirs`
- `exclude_globs`
- `exclude_files`
- `include_categories`
- `exclude_categories`

### Phase 3 - Planning

If analysis returns recommendations and no plan yet:
- Call `generate_refactor_plan_tool`.

If using one-shot heuristics:
- `generate_refactor_suggestions` already returns plan + heuristic results.

### Phase 4 - Output Validation

Validate output contract before sharing final conclusions:
- Presence of expected keys for the called tool.
- Presence of `report_schema_version` when available.
- Plan integrity when `refactor_plan` exists (non-empty steps).
- Coherence between counts (`total_files_scanned`, candidates, smells).

## Guardrails / Regras de Seguranca

Input guardrails:
- Do not run deep scans on invalid path.
- Do not run with contradictory include/exclude rules.
- Do not activate expensive dependency options without purpose.

Execution guardrails:
- Prefer `context_budget` before heavy operations on unknown projects.
- If scan fails due to problematic files, retry with targeted exclusions.
- Keep profile/mode choice explicit in the response.

Output guardrails:
- Report assumptions and skipped areas.
- Separate confirmed findings from estimated impact.
- Do not claim automatic code changes unless applied and validated.

## Parameter Tuning Quick Guide

Use this order for tuning:
1. Scope first: narrow files/categories.
2. Profile second: `legacy` -> `blend` -> `heuristics` as needed.
3. Dependencies third: enable only for coupling-heavy decisions.
4. Top-N and thresholds last for report readability.

## Failure Recovery / Recuperacao de Falhas

Common recovery actions:
- Invalid path: correct `project_path` and rerun preflight.
- Timeout or very long scan: reduce scope with exclusions.
- Unexpected output shape: fallback to simpler tool (`context_budget` or candidates only).
- Too many low-value findings: increase focus with categories and `top_n`.

## Implementation Checklist / Checklist de Implementacao

- [ ] Run preflight (`context_budget`) for unknown or large projects.
- [ ] Select profile (`legacy`, `heuristics`, or `blend`) based on objective.
- [ ] Select tool branch (full, candidates, smells, one-shot).
- [ ] Apply exclusions and category filters before deep scan.
- [ ] Generate plan when recommendations are available.
- [ ] Validate output contract keys and plan consistency.
- [ ] Summarize findings with clear priority and actionable next steps.

## Testing Checklist / Checklist de Testes

Use existing test suites as reference:
- `tests/test_mcp_tools.py`
- `tests/test_cli_main.py`
- `tests/test_refactor_heuristics.py`

Minimum scenarios:
- [ ] Happy path for each MCP tool.
- [ ] Invalid `project_path` handling.
- [ ] Empty or tiny project behavior.
- [ ] Profile switching (`legacy`, `heuristics`, `blend`).
- [ ] Dependency mode impact in heuristic ranking.
- [ ] Retry strategy with exclusions for problematic files.

## Prompt Starters / Prompts de Ativacao

PT:
- "Use a skill de refatoracao MCP para avaliar se este projeto cabe em 128k tokens e me dar o melhor proximo passo."
- "Aplique o fluxo heuristico do context-refactor, priorize code smells, e gere plano executavel."
- "Compare legacy vs heuristics para candidatos de refatoracao e justifique a escolha final."

EN:
- "Use the MCP refactor workflow skill to check context fit for 128k and propose the next action."
- "Run the heuristic branch, prioritize code smells, and produce an executable refactor plan."
- "Compare legacy vs heuristics candidate detection and justify the final branch selection."

## Source Of Truth / Fontes de Verdade

- `docs/desenvolvedor/fluxos.md`
- `docs/integracao/contratos.md`
- `context_refactor/refactor_engine.py`
- `context_refactor/refactor_heuristics_engine.py`
- `context_refactor/refactor_planner.py`

Always keep this skill aligned with these files whenever MCP contracts or refactor pipelines change.