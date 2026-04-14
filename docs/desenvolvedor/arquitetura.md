# Arquitetura

## Visao geral

A arquitetura e organizada em tres blocos:

- `cli/`: interface humana em linha de comando
- `mcp_server/`: adaptador de protocolo MCP
- `context_refactor/`: dominio de analise, heuristicas e planejamento

`token_report.py` continua sendo a fonte de verdade para contagem bruta de
tokens.

## Principio estrutural atual

O projeto usa fachadas publicas estaveis e implementacao interna modular por
dominio.

Fachadas publicas relevantes:

- `cli.main`
- `mcp_server.tools`
- `mcp_server.tool_support`
- `context_refactor.analyzer`
- `context_refactor.models`
- `context_refactor.dependency_analyzer`
- `context_refactor.refactor_heuristics`

Implementacoes especializadas vivem em modulos por responsabilidade, como
`analyzer_*`, `dependency_*`, `model_*`, `tools_*` e `tool_support_*`.

## Camadas

1. Interface
   CLI Typer e servidor MCP.
2. Aplicacao
   Wrappers que adaptam argumentos externos para o dominio.
3. Dominio
   Analise de tokens, dependencias, heuristicas, planner e modelos.
4. Integracao externa
   `token_report.py` via subprocess.

## Fluxo arquitetural resumido

### CLI

`cli.main` -> `cli.app` -> `cli.commands.*` -> `mcp_server.tools.*` ->
`context_refactor.*`

### MCP

`mcp_server.server` -> catalogo/schema -> `mcp_server.tools.*` ->
`context_refactor.*`

## Decisoes arquiteturais relevantes

- preservar contratos publicos mesmo durante refactors internos
- manter `token_report.py` simples e isolado
- separar pipeline legacy e pipeline heuristica no MCP
- concentrar compatibilidade em fachadas pequenas e modulos especializados

## Pontos criticos

- contrato de saida do `token_report.py`
- coerencia entre CLI e MCP para filtros e parametros de dependencia
- estabilidade de serializacao dos modelos usados em JSON
- paridade entre modo SDK e fallback JSON-RPC

## Oportunidades de evolucao

- validacao formal de schema de entrada e saida
- observabilidade e logs estruturados
- capabilities MCP adicionais

## Referencias

- [Modulos](./modulos.md)
- [Fluxos Internos](./fluxos.md)
- [Manutencao e Evolucao](./manutencao.md)

