# Ferramentas MCP

Este documento descreve as 6 tools publicas do servidor MCP, com foco em uso
pratico e nos campos estaveis de resposta.

## Visao rapida

| Tool | Quando usar | Retorno principal |
|---|---|---|
| `context_refactor.analyze_project` | diagnostico completo | summary + budget + recomendacoes + plano |
| `context_refactor.context_budget` | checagem rapida de cabimento | budget e overflow |
| `context_refactor.detect_refactor_candidates` | pipeline legacy de candidatos | lista priorizada de recomendacoes |
| `context_refactor.generate_refactor_plan` | plano sequencial | budget + plano |
| `context_refactor.detect_code_smells` | heuristicas por arquivo | `results[]` com problemas e refactors |
| `context_refactor.generate_refactor_suggestions` | heuristicas + plano | `heuristic_results` + `refactor_plan` |

## Parametros comuns

- `project_path` obrigatorio
- `estimator`: `bytes|chars|whitespace|heuristic`
- `analysis_profile`: `default|full|source-only|docs`
- `config_path`
- `exclude_dirs`, `exclude_globs`, `exclude_files`
- `include_categories`, `exclude_categories`
- `dependency_mode`: `off|report_only|blended|weighted`
- `dependency_max_depth`
- `dependency_max_multiplier`
- `dependency_base_weight`
- `dependency_depth_decay`
- `dependency_depth_weights`

## Campos compartilhados de resposta

As tools de analise e heuristicas retornam um subconjunto estavel dos campos
abaixo:

- `report_schema_version`
- `compatibility_mode`
- `analysis_scope`
- `noise_summary`
- `signal_score`
- `category_counts`
- `category_tokens`
- `dependency_analysis`

Algumas tools tambem retornam:

- `dependency_hotspots`

## Tool: context_refactor.analyze_project

Objetivo:

- retornar a visao mais completa para tomada de decisao

Campos principais:

- `project_summary`
- `context_budget`
- `largest_files`
- `largest_directories`
- `refactor_recommendations`
- `refactor_plan`

Exemplo resumido:

```json
{
  "project_summary": {
    "files": 120,
    "total_tokens": 180000,
    "context_budget": 102400,
    "fits_context": false
  },
  "context_budget": {
    "overflow_tokens": 77600
  },
  "refactor_plan": {
    "steps": [
      {"step_number": 1, "title": "Split oversized files"}
    ]
  }
}
```

## Tool: context_refactor.context_budget

Objetivo:

- responder rapidamente se o escopo analisado cabe no contexto

Campos principais:

- `llm_context_size`
- `safety_margin`
- `context_budget`
- `total_tokens`
- `total_files`
- `fits_context`
- `overflow_tokens`
- `overflow_ratio`

## Tool: context_refactor.detect_refactor_candidates

Objetivo:

- listar candidatos de refatoracao pela pipeline legacy

Campos principais:

- `total_files_scanned`
- `candidates_found`
- `recommendations[]`

Cada recomendacao inclui:

- `file_path`
- `category`
- `smell`
- `technique`
- `priority`
- `description`
- `estimated_token_reduction`

## Tool: context_refactor.generate_refactor_plan

Objetivo:

- produzir um plano ordenado para reduzir tokens e caber no contexto

Campos principais:

- `context_budget`
- `refactor_plan.steps[]`
- `refactor_plan.total_estimated_token_reduction`
- `refactor_plan.projected_tokens_after`
- `refactor_plan.fits_context_after`

## Tool: context_refactor.detect_code_smells

Objetivo:

- executar o Heuristics Engine e consolidar problemas por arquivo

Campos principais:

- `total_files_scanned`
- `files_with_smells`
- `results[]`

Cada item de `results[]` inclui:

- `file`
- `tokens`
- `language`
- `problems`
- `suggested_refactors`
- `recommendations`

Quando a analise por dependencia esta ativa, tambem podem aparecer:

- `dependency_weight`
- `effective_token_size`
- `refactor_priority_score`
- `fan_in`
- `fan_out`

## Tool: context_refactor.generate_refactor_suggestions

Objetivo:

- gerar sugestoes legiveis por heuristica e um plano associado

Campos principais:

- `context_budget`
- `heuristic_results`
- `refactor_plan`

## Erros possiveis

- tool desconhecida
- tipo ou valor invalido de argumento
- falha interna na analise
- erro de subprocess no `token_report.py`

## Observacoes de seguranca e performance

- nao ha auth nativa no servidor
- nao ha rate limiting embutido
- `top_n` reduz volume de resposta em varias rotas
- filtros de escopo e perfil sao a melhor defesa contra ruido

