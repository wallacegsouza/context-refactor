# Modulos

## Mapa atual por dominio

### CLI

- `cli/main.py`: entrypoint publico do comando `context-refactor`
- `cli/app.py`: fabrica do app Typer e registro global
- `cli/commands/analysis.py`: comandos `analyze`, `budget`, `candidates`
- `cli/commands/heuristics.py`: comandos `smells`, `suggest`, `plan`
- `cli/commands/server.py`: comando `serve`
- `cli/options.py`: argumentos e opcoes reutilizaveis
- `cli/shared.py`: normalizacao, execucao de tool e contexto comum
- `cli/rendering.py`: saida textual e tabular

### Core de analise

- `context_refactor/analyzer.py`: fachada publica da analise
- `context_refactor/analyzer_runner.py`: execucao do `token_report.py`
- `context_refactor/analyzer_config.py`: perfis, filtros e opcoes de dependencia
- `context_refactor/analyzer_classification.py`: classificacao de arquivos
- `context_refactor/analyzer_metrics.py`: montagem de metricas e enriquecimento
- `context_refactor/context_budget.py`: calculo de cabimento

### Core de dependencias

- `context_refactor/dependency_analyzer.py`: fachada publica
- `context_refactor/dependency_extraction.py`: extracao estrutural
- `context_refactor/dependency_resolution.py`: resolucao de modulos para arquivo
- `context_refactor/dependency_graph_builder.py`: grafo de dependencias
- `context_refactor/dependency_weighting.py`: pesos, profundidade e prioridade

### Modelos

- `context_refactor/models.py`: fachada publica de tipos
- `context_refactor/model_tokens.py`: tokens, diretorios e budget
- `context_refactor/model_analysis.py`: entidades de analise estrutural
- `context_refactor/model_dependencies.py`: tipos de dependencia
- `context_refactor/model_refactoring.py`: recomendacoes e plano
- `context_refactor/model_results.py`: resultados agregados
- `context_refactor/model_enums.py`: enums compartilhados

### Refatoracao e heuristicas

- `context_refactor/refactor_engine.py`: candidatos legacy
- `context_refactor/refactor_planner.py`: agrupamento em plano sequencial
- `context_refactor/refactor_heuristics.py`: fachada publica do Heuristics Engine
- `context_refactor/refactor_heuristics_engine.py`: engine principal
- `context_refactor/refactor_heuristics_support.py`: helpers do engine
- `context_refactor/refactor_rules/`: regras plugaveis
- `context_refactor/code_refactor.py`: analise estrutural de codigo
- `context_refactor/markdown_refactor.py`: recomendacoes para markdown

### MCP

- `mcp_server/server.py`: registro de schema, transporte stdio e fallback
- `mcp_server/tools.py`: fachada publica das tools
- `mcp_server/tools_analysis.py`: tools de analise e plano legacy
- `mcp_server/tools_heuristics.py`: tools de heuristicas
- `mcp_server/tool_support.py`: fachada de helpers MCP
- `mcp_server/tool_support_analysis.py`: helpers de analise e payloads
- `mcp_server/tool_support_heuristics.py`: criacao do Heuristics Engine
- `mcp_server/tool_support_legacy.py`: compatibilidade com recomendacoes legacy

## Cuidados de manutencao

- preserve as fachadas publicas e seus nomes
- mova implementacoes novas para modulos especializados por dominio
- mantenha a CLI e o MCP alinhados nos argumentos publicos
- atualize a documentacao quando houver nova superficie publica

