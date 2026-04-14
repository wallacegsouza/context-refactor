# Fluxos Internos e Contratos

## Inicializacao do MCP

1. `run_server()` escolhe modo SDK ou fallback.
2. No modo SDK, o servidor registra `list_tools` e `call_tool`.
3. No fallback, o processo entra em loop JSON-RPC em stdin/stdout.

## Registro das tools

`mcp_server/server.py` publica o catalogo das 6 tools com:

- nome
- descricao
- schema de entrada

## Fluxo de chamada MCP

```text
Host MCP
  -> call_tool(name, arguments)
  -> mcp_server.tools.<tool publica>
  -> mcp_server.tools_analysis ou tools_heuristics
  -> tool_support_* e context_refactor.*
  -> JSON serializavel de resposta
```

## Fluxo de chamada CLI

```text
context-refactor
  -> cli.main
  -> cli.app
  -> cli.commands.*
  -> mcp_server.tools.<tool publica>
  -> context_refactor.*
  -> rendering/JSON
```

## Fluxo de analise

1. A interface publica resolve parametros e filtros.
2. `context_refactor.analyzer` resolve escopo e opcoes de dependencia.
3. `analyzer_runner.py` executa `token_report.py`.
4. `analyzer_metrics.py` classifica, filtra, agrega e enriquece os resultados.
5. O MCP ou a CLI consomem esses dados para budget, candidatos ou heuristicas.

## Fluxo de heuristicas

1. As tools de heuristica usam a mesma base de `analyze_tokens`.
2. `tool_support_heuristics.py` cria o `HeuristicsEngine`.
3. O engine executa regras plugaveis sobre os arquivos analisados.
4. O resultado vira `results` ou `heuristic_results`, com plano quando
   aplicavel.

## Fluxo legacy

1. A tool chama a pipeline de analise.
2. `refactor_engine.py` produz recomendacoes legacy.
3. `refactor_planner.py` transforma recomendacoes em passos ordenados.

## Validacao e erros

- validacoes de categoria e perfil ficam no core
- erros do `token_report.py` sobem como falha de execucao
- tool desconhecida falha no lookup do servidor
- fallback e modo SDK retornam formatos de erro diferentes

## Referencias

- [Arquitetura](./arquitetura.md)
- [Contratos MCP](../integracao/contratos.md)

