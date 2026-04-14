# Contratos e Comunicacao MCP

## Contratos principais

### `list_tools`

Retorna metadados das tools registradas:

- nome
- descricao
- schema de entrada

### `call_tool`

Recebe `name` e `arguments`, despacha para a funcao correspondente e retorna
payload JSON serializavel.

## Tools registradas

- `context_refactor.analyze_project`
- `context_refactor.context_budget`
- `context_refactor.detect_refactor_candidates`
- `context_refactor.generate_refactor_plan`
- `context_refactor.detect_code_smells`
- `context_refactor.generate_refactor_suggestions`

## Campos de entrada mais relevantes

Comuns:

- `project_path`
- `estimator`
- `analysis_profile`
- `config_path`
- `exclude_dirs`
- `exclude_globs`
- `exclude_files`
- `include_categories`
- `exclude_categories`

Dependendo da tool:

- `llm_context_size`
- `safety_margin`
- `top_n`

Opcionalmente, para enriquecimento por dependencia:

- `dependency_mode`
- `dependency_max_depth`
- `dependency_max_multiplier`
- `dependency_base_weight`
- `dependency_depth_decay`
- `dependency_depth_weights`

## Estruturas de resposta publicas

Campos compartilhados:

- `report_schema_version`
- `compatibility_mode`
- `analysis_scope`
- `noise_summary`
- `signal_score`
- `category_counts`
- `category_tokens`
- `dependency_analysis`

Campos por familia:

- analise completa: `project_summary`, `context_budget`, `largest_files`,
  `largest_directories`, `refactor_recommendations`, `refactor_plan`
- budget: `llm_context_size`, `safety_margin`, `context_budget`,
  `total_tokens`, `total_files`, `fits_context`, `overflow_tokens`,
  `overflow_ratio`
- candidatos legacy: `total_files_scanned`, `candidates_found`,
  `recommendations`
- heuristicas: `files_with_smells`, `results` ou `heuristic_results`

Ferramentas que incluem hotspots podem retornar:

- `dependency_hotspots`

## Regras de validacao

- validacao de categorias e perfis acontece no core
- nomes de tool fora do catalogo retornam erro de lookup
- valores invalidos podem gerar erro de execucao

## Tratamento de erros

- modo SDK: erro textual serializado para o cliente
- modo fallback: erro JSON-RPC com codigo e mensagem

O host deve tratar falhas de subprocess, argumentos invalidos e path
inexistente como erros recuperaveis de chamada.

## Timeouts, retries e fallback

- nao ha politica de retry nativa no servidor
- timeouts de transporte dependem do host
- fallback JSON-RPC entra automaticamente sem o SDK MCP

## Capabilities MCP nao implementadas

- resources
- prompts
- templates
- streams
- eventos
- context providers
- auth flows

## Exemplo resumido de chamada

```json
{
  "name": "context_refactor.detect_refactor_candidates",
  "arguments": {
    "project_path": "/repo",
    "top_n": 20,
    "analysis_profile": "source-only"
  }
}
```

