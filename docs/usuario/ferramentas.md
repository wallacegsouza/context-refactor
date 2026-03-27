# Ferramentas MCP

Este documento descreve as tools expostas pelo servidor MCP, com foco em uso pratico.

This page describes MCP tools with practical usage focus.

## Visao Rapida

| Tool | Quando usar | Retorno principal |
|---|---|---|
| `context_refactor.analyze_project` | diagnostico completo | summary + budget + recommendations + plan |
| `context_refactor.context_budget` | checagem rapida de cabimento | budget e overflow |
| `context_refactor.detect_refactor_candidates` | listar oportunidades | lista priorizada de recomendacoes |
| `context_refactor.generate_refactor_plan` | obter plano estruturado | passos de refatoracao |
| `context_refactor.detect_code_smells` | heuristicas por arquivo | resultados por arquivo (problems/suggestions) |
| `context_refactor.generate_refactor_suggestions` | sugestoes + plano via heuristicas | heuristic_results + refactor_plan |

## Parametros Comuns

- `project_path` (obrigatorio)
- `estimator`: `bytes|chars|whitespace|heuristic`
- `analysis_profile`: `default|full|source-only|docs`
- `config_path`
- `exclude_dirs`, `exclude_globs`, `exclude_files`
- `include_categories`, `exclude_categories`

## Tool: context_refactor.analyze_project

### Objetivo

Retornar a analise mais completa para tomada de decisao.

### Entradas-chave

- `project_path` (required)
- `llm_context_size` (default 128000)
- `safety_margin` (default 0.8)
- `top_n` (default 50)

### Estrutura de saida (alto nivel)

- `analysis_scope`, `noise_summary`, `signal_score`
- `project_summary`
- `context_budget`
- `largest_files`, `largest_directories`
- `refactor_recommendations`
- `refactor_plan`

### Exemplo resumido

```json
{
  "project_summary": {"files": 120, "total_tokens": 180000, "fits_context": false},
  "context_budget": {"context_budget": 102400, "overflow_tokens": 77600},
  "refactor_plan": {"steps": [{"step_number": 1, "title": "Split oversized files"}]}
}
```

## Tool: context_refactor.context_budget

### Objetivo

Responder rapidamente se o escopo analisado cabe no contexto.

### Validacoes relevantes

- `safety_margin` deve representar fracao utilizavel.
- categorias devem ser valores aceitos.

### Exemplo resumido

```json
{
  "fits_context": false,
  "total_tokens": 180000,
  "context_budget": 102400,
  "overflow_tokens": 77600
}
```

## Tool: context_refactor.detect_refactor_candidates

### Objetivo

Listar candidatos de refatoracao com prioridade e tecnica.

### Saida principal

- `total_files_scanned`
- `candidates_found`
- `recommendations[]`

### Exemplo resumido

```json
{
  "candidates_found": 2,
  "recommendations": [
    {"priority": "high", "smell": "God File", "technique": "Extract Module"}
  ]
}
```

## Tool: context_refactor.generate_refactor_plan

### Objetivo

Produzir passos ordenados para reduzir tokens.

### Saida principal

- `context_budget`
- `refactor_plan.steps[]`
- `fits_context_after`

### Exemplo resumido

```json
{
  "refactor_plan": {
    "steps": [{"step_number": 1, "title": "Extract large modules"}],
    "fits_context_after": true
  }
}
```

## Tool: context_refactor.detect_code_smells

### Objetivo

Executar heuristicas plugaveis e consolidar problemas por arquivo.

### Saida principal

- `files_with_smells`
- `results[]` com `problems` e `suggested_refactors`

### Exemplo resumido

```json
{
  "files_with_smells": 1,
  "results": [
    {"language": "python", "problems": ["Long Method"], "suggested_refactors": ["Extract Method: process"]}
  ]
}
```

## Tool: context_refactor.generate_refactor_suggestions

### Objetivo

Gerar sugestoes legiveis + plano a partir do Heuristics Engine.

### Saida principal

- `heuristic_results`
- `context_budget`
- `refactor_plan`

### Exemplo resumido

```json
{
  "heuristic_results": [{"file": "/repo/service.py", "problems": ["Large Class"]}],
  "refactor_plan": {"steps": [{"step_number": 1, "title": "Extract Class"}]}
}
```

## Erros Possiveis

- `Unknown tool`: nome nao registrado.
- erro de argumento: tipo/valor invalido.
- erro interno de execucao (ex.: excecao em analise).

## Dependencias Internas e Externas

- Internas: `analyzer`, `context_budget`, `refactor_engine`, `refactor_heuristics`, `refactor_planner`.
- Externas: `token_report.py`, `mcp` SDK (modo nativo), Python runtime.

## Observacoes de Seguranca e Performance

- Nao ha auth nativa no servidor.
- Sem rate limiting embutido.
- `top_n` reduz volume de resposta para clientes.
- Escopo de analise deve ser filtrado para evitar ruido/custo desnecessario.
