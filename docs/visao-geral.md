# Visao Geral do ContextRefactor

## Nome e proposito

O ContextRefactor e um servidor MCP e uma CLI para analise de footprint de
tokens, ruido e acoplamento estrutural em repositorios.

O objetivo e transformar volume bruto de codigo em uma leitura mais util para
refatoracao e cabimento em janelas de contexto de LLM.

## Problema que resolve

Projetos reais frequentemente excedem a janela de contexto. O ContextRefactor
ajuda a:

- medir o tamanho bruto e o tamanho efetivo do escopo analisado
- identificar hotspots por volume, categoria e dependencias
- priorizar refators com melhor relacao entre impacto e custo

## Publico-alvo

- desenvolvedores e tech leads que usam LLM no fluxo de engenharia
- integradores que conectam servidores MCP a clientes/hosts
- equipes que precisam de onboarding e manutencao previsivel

## Formas de uso

- CLI via `context-refactor`
- servidor MCP via `python3 -m mcp_server.server`
- fallback JSON-RPC quando o SDK `mcp` nao esta instalado

## Tools MCP publicas

1. `context_refactor.analyze_project`
2. `context_refactor.context_budget`
3. `context_refactor.detect_refactor_candidates`
4. `context_refactor.generate_refactor_plan`
5. `context_refactor.detect_code_smells`
6. `context_refactor.generate_refactor_suggestions`

## Capacidades principais

- budget de contexto
- classificacao por categoria de arquivo
- filtros por perfil e configuracao local
- priorizacao legacy por recomendacoes
- Heuristics Engine com regras plugaveis
- enriquecimento opcional por dependencias

## Arquitetura atual em alto nivel

O desenho atual usa fachadas publicas estaveis sobre implementacoes modulares:

- `cli.main` e o entrypoint publico da CLI
- `mcp_server.tools` e `mcp_server.tool_support` sao fachadas de compatibilidade
- `context_refactor.analyzer`, `models`, `dependency_analyzer` e
  `refactor_heuristics` sao fachadas publicas do core

Isso permite evolucao interna sem quebrar consumidores externos ou imports
internos existentes.

## Dependencias externas relevantes

- `token_report.py` como fonte de verdade da contagem bruta
- SDK `mcp` para o modo MCP nativo
- `typer` e `rich` para a CLI

## Limitacoes conhecidas

- sem auth ou autorizacao nativas
- sem streaming de resposta
- sem resources, prompts ou templates MCP
- contrato de saida evolutivo, sem versionamento externo separado alem dos
  campos de schema do proprio payload

## Evidencias no codigo

- catalogo das tools em `mcp_server/server.py`
- fachada publica MCP em `mcp_server/tools.py`
- entrypoint da CLI em `cli/main.py`
- pipeline de analise em `context_refactor/analyzer.py`

## Referencias

- [Ferramentas MCP](./usuario/ferramentas.md)
- [Arquitetura](./desenvolvedor/arquitetura.md)
- [Fluxos Internos](./desenvolvedor/fluxos.md)

