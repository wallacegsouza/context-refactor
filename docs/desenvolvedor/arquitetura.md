# Arquitetura

## Visao Geral

A arquitetura e dividida em tres blocos:

- `cli/`: interface de linha de comando
- `mcp_server/`: adaptador de protocolo MCP
- `context_refactor/`: dominio e logica de analise/refatoracao

Architecture is split into CLI, MCP adapter, and core domain logic.

## Camadas

1. Interface: comandos CLI e endpoints MCP.
2. Aplicacao: funcoes em `mcp_server/tools.py` que orquestram chamadas.
3. Dominio: modelos, analisadores, regras heuristicas e planner.
4. Integracao externa: `token_report.py` (subprocess).

## Decisoes Arquiteturais Relevantes

- `token_report.py` e a fonte de verdade da contagem de tokens.
- Modelos tipados centralizados em `context_refactor/models.py`.
- Regras plugaveis por classe via `RefactorRule`.
- Fallback JSON-RPC para ambientes sem SDK MCP.

## Pontos Criticos

- Acoplamento com o formato de saida de `token_report.py`.
- Dependencia de funcoes de analise estrutural para varias regras.
- Sem auth/rate limit/streaming no servidor MCP.

## Oportunidades de Evolucao

- Versionamento formal de contrato de resposta.
- Camada de validacao de schema de entrada/saida no servidor.
- Observabilidade (logs estruturados e metricas).

## Relacao com Outros Docs

- [Modulos](./modulos.md)
- [Fluxos Internos](./fluxos.md)
- [Manutencao e Evolucao](./manutencao.md)
