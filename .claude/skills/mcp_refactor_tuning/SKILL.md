---
name: mcp-refactor-tuning
description: "Use when you need to tune context-refactor MCP parameters for cost, precision, and scope. Covers tuning/ajuste de analysis_profile, dependency_mode, exclusions, llm_context_size, safety_margin, top_n, and prioritization tradeoffs."
license: MIT
metadata:
  author: GitHub Copilot
  version: "1.0.0"
  language: "pt-BR + en-US"
---

# MCP Refactor Tuning Skill

Specialist guidance for parameter tuning in context-refactor MCP workflows.

Guia especialista para ajuste fino de parametros no fluxo MCP do context-refactor.

## When To Apply / Quando Aplicar

Use this skill when the main refactor workflow is already clear, but parameter choice is still uncertain.

Use esta skill quando o fluxo principal de refatoracao ja esta claro, mas a escolha de parametros ainda gera duvida.

Typical triggers:
- Analysis is too slow or too noisy.
- Results are too broad or too shallow.
- Dependency weighting needs calibration.
- Context fit is close to the model limit.
- You need to trade cost vs coverage explicitly.

Gatilhos comuns:
- A analise esta lenta ou ruidosa demais.
- O resultado ficou amplo demais ou superficial demais.
- O peso de dependencias precisa de calibracao.
- O budget de contexto esta perto do limite da LLM.
- E preciso trocar custo por cobertura de forma explicita.

## Parameters In Scope / Parametros Cobertos

- `analysis_profile`
- `dependency_mode`
- `dependency_max_depth`
- `dependency_max_multiplier`
- `dependency_base_weight`
- `dependency_depth_decay`
- `dependency_depth_weights`
- `llm_context_size`
- `safety_margin`
- `top_n`
- `exclude_dirs`
- `exclude_globs`
- `exclude_files`
- `include_categories`
- `exclude_categories`

## Tuning Principles / Principios de Ajuste

1. Tune scope before algorithm depth.
   - Narrow files and categories before enabling heavier analysis.

2. Tune profile before dependency weighting.
   - First decide if the problem is legacy, heuristics, or blend.

3. Tune readability separately from correctness.
   - `top_n` improves report usefulness, not detection quality.

4. Tune context budget conservatively.
   - Prefer realistic `llm_context_size` and explicit `safety_margin`.

## Parameter Playbook / Playbook de Parametros

### `analysis_profile`

Choose by intent:
- `legacy`: lower cost, simpler candidate detection.
- `heuristics`: richer smell analysis and prioritization.
- `blend`: broader coverage with moderate extra cost.

Use `legacy` when:
- You want a quick baseline.
- You are validating broad hotspots first.

Use `heuristics` when:
- You need file-level smells and prioritization.
- Coupling, class size, or method size matters.

Use `blend` when:
- You want stronger confidence before planning.
- You need to compare rule-based and legacy signals.

### `dependency_mode`

Guideline:
- Disable or minimize for quick scans.
- Enable for architecture-heavy refactor work.

Use stronger dependency analysis when:
- High coupling is part of the problem statement.
- Refactor order depends on fan-in/fan-out.

Avoid stronger dependency analysis when:
- The question is only context fit.
- You only need a fast first-pass shortlist.

### Dependency Weight Parameters

Tune only if default dependency ranking is not useful.

- `dependency_max_depth`: increase only when indirect coupling matters.
- `dependency_max_multiplier`: cap impact to avoid coupling dominating every score.
- `dependency_base_weight`: raise only if direct dependency importance is understated.
- `dependency_depth_decay`: lower values preserve deeper-node influence longer.
- `dependency_depth_weights`: use only when you need explicit per-depth shaping.

Safe rule:
- Change one dependency parameter at a time and compare outputs.

### Context Budget Parameters

Use these rules:
- `llm_context_size` should match the real target model, not an optimistic maximum.
- `safety_margin` should leave room for prompts, system instructions, and final answer.

Heuristic guidance:
- More conservative runs: higher effective reserve.
- Exploratory runs: lower reserve may be acceptable.

### Scope Parameters

Prefer scope narrowing before profile escalation.

Recommended exclusions for large repositories:
- Virtual environments
- Build outputs
- Generated files
- Binary or cache directories

Recommended category strategy:
- Start with source-focused categories.
- Reintroduce tests/docs only when they matter to the refactor decision.

### `top_n`

Use `top_n` to improve prioritization clarity:
- Smaller value for focused review.
- Larger value for portfolio or backlog generation.

Do not confuse `top_n` with detection depth.

## Tuning Recipes / Receitas de Ajuste

### Recipe 1 - Fast First Pass

- Run `context_budget`.
- Narrow scope with exclusions.
- Use `analysis_profile=legacy`.
- Keep dependency analysis disabled or light.
- Use small `top_n`.

### Recipe 2 - Smell Prioritization

- Use `analysis_profile=heuristics`.
- Keep source categories only.
- Enable dependency analysis only if coupling is suspected.
- Compare top files before and after dependency tuning.

### Recipe 3 - Plan With Higher Confidence

- Start with `blend` or heuristics.
- Validate that recommendations stay stable after modest scope changes.
- Generate plan only after tuning noise down.

### Recipe 4 - Near Context Limit

- Run `context_budget` first.
- Increase exclusions before reducing quality.
- Keep `safety_margin` explicit.
- Split the analysis into phases if overflow remains high.

## Comparison Checklist / Checklist de Comparacao

When tuning, compare runs on:
- Total files scanned.
- Candidate or smell count.
- Top-ranked items stability.
- Presence or absence of coupling-driven files.
- Estimated plan usefulness.
- Runtime and scan cost.

## Guardrails / Regras de Seguranca

- Do not tune many parameters at once without a baseline.
- Do not interpret ranking changes without checking scope differences.
- Do not lower `safety_margin` just to force fit without noting the risk.
- Do not enable deep dependency analysis on every run by default.

## Suggested Iteration Pattern / Padrao de Iteracao

1. Baseline run.
2. Scope adjustment.
3. Profile adjustment.
4. Dependency adjustment.
5. Final comparison and selection.

## Prompt Starters / Prompts de Ativacao

PT:
- "Ajuste os parametros do context-refactor para reduzir custo sem perder os principais hotspots."
- "Otimize analysis_profile, dependency_mode e filtros para priorizar code smells com menos ruido."
- "O projeto esta perto do limite de contexto; ajuste budget e escopo antes da analise completa."

EN:
- "Tune context-refactor parameters to lower cost without losing the main hotspots."
- "Optimize analysis_profile, dependency_mode, and filters to prioritize code smells with less noise."
- "The project is near the context limit; tune budget and scope before running full analysis."

## Related Skills / Skills Relacionadas

- `mcp-refactor-workflow`: main orchestration workflow.

Use this tuning skill together with the main workflow skill when branch selection is known but parameter calibration still needs work.