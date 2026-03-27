# Visao Geral do MCP

## Nome e Proposito

**ContextRefactor** e um servidor MCP para analise de footprint de tokens de um repositorio e geracao de recomendacoes/plano de refatoracao para caber em janelas de contexto de LLM.

ContextRefactor is an MCP server that analyzes repository token footprint and builds refactoring guidance to fit LLM context windows.

## Problema que Resolve

Projetos reais frequentemente excedem a janela de contexto. O MCP ajuda a:

- medir o tamanho util em tokens
- identificar pontos de maior impacto para reducao
- priorizar refatoracoes com estimativa de ganho

## Casos de Uso Principais

- Diagnosticar se um repo cabe em um contexto alvo.
- Gerar plano incremental de reducao de tokens.
- Integrar analise em hosts MCP para assistentes de engenharia.

## Publico-Alvo

- Desenvolvedores e tech leads que usam LLM no fluxo de desenvolvimento.
- Integradores que conectam MCP servers a clientes/hosts.
- Equipes que precisam de onboarding e manutencao previsivel.

## Contexto de Uso

- Monorepos e repositorios com muito codigo/documentacao.
- Times que precisam combinar automacao e revisao humana.
- Ambientes locais ou CI com Python 3.11+.

## Capacidades Oferecidas

### Tools MCP Expostas

1. `context_refactor.analyze_project`
2. `context_refactor.context_budget`
3. `context_refactor.detect_refactor_candidates`
4. `context_refactor.generate_refactor_plan`
5. `context_refactor.detect_code_smells`
6. `context_refactor.generate_refactor_suggestions`

### Capabilities Nao Expostas Atualmente

- resources
- prompts
- templates
- streams
- eventos
- context providers
- auth flows

## Dependencias Externas Relevantes

- `token_report.py` (fonte de verdade para contagem de tokens)
- `mcp` SDK (modo MCP nativo)
- `typer` + `rich` (CLI)

## Limitacoes Conhecidas

- Sem autenticacao e autorizacao nativas.
- Sem streaming de resposta.
- Sem contrato formal versionado para schema de saida alem dos objetos retornados.
- Parte da documentacao historica pode citar 4 tools, mas o servidor atual expoe 6 tools.

## Evidencias e Inferencias

### Evidencias no Codigo

- Registro de tools em `mcp_server/server.py`.
- Implementacoes em `mcp_server/tools.py`.
- Perfis de analise em `context_refactor/analyzer.py`.

### Inferencias

- O design atual privilegia simplicidade operacional sobre features MCP avancadas (resources/prompts/auth).
