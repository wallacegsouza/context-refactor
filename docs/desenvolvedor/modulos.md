# Modulos

## Mapa de Modulos

### `context_refactor/models.py`

- Objetivo: tipos de dominio (FileTokenInfo, ContextBudget, RefactorPlan etc.).
- Cuidados: manter compatibilidade de serializacao (`to_dict`) para consumidores MCP/CLI.

### `context_refactor/analyzer.py`

- Objetivo: invocar `token_report.py`, classificar arquivos, resolver escopo/perfis.
- Dependencias: subprocess Python, config `.context-refactor.json`.
- Cuidados: validacao de categorias e robustez de erro de subprocess.

### `context_refactor/refactor_engine.py`

- Objetivo: detectar candidatos via analise por categoria de arquivo.
- Relacoes: usa analise de codigo e markdown.

### `context_refactor/refactor_heuristics.py`

- Objetivo: orquestrar regras plugaveis (`RefactorRule`) e consolidar `HeuristicResult`.
- Cuidados: deduplicacao de recomendacoes e thresholds consistentes.

### `context_refactor/refactor_rules/*`

- Objetivo: heuristicas especificas (large file, long method, large class, duplicate code).
- Contrato: implementar `applies_to` e `evaluate`.

### `context_refactor/refactor_planner.py`

- Objetivo: transformar recomendacoes em plano sequencial.
- Saida: passos com tecnicas, arquivos afetados e reducao estimada.

### `mcp_server/server.py`

- Objetivo: registrar tools MCP e despachar chamadas.
- Fluxos: modo SDK e fallback JSON-RPC.

### `mcp_server/tools.py`

- Objetivo: ponte entre payload primitivo e core do dominio.
- Cuidados: manter assinatura e retorno estaveis por tool.

### `cli/main.py`

- Objetivo: comandos de uso humano (`analyze`, `budget`, `candidates`, `smells`, `suggest`, `plan`, `serve`).
- Cuidados: manter alinhamento dos parametros com MCP tools.

## Oportunidades de Reutilizacao/Desacoplamento

- Isolar contrato de analise estrutural em interface publica.
- Centralizar thresholds em configuracao unica.
- Unificar normalizacao/validacao de entrada entre CLI e MCP.
