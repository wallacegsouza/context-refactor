# Manutencao e Evolucao

## Areas sensiveis

- integracao com `token_report.py`
- catalogo e dispatcher de tools em `mcp_server/server.py`
- serializacao dos modelos usados por CLI e MCP
- coerencia entre fachadas publicas e modulos especializados

## Estrategia de compatibilidade

O projeto usa fachadas pequenas para preservar imports e contratos:

- `cli.main`
- `mcp_server.tools`
- `mcp_server.tool_support`
- `context_refactor.analyzer`
- `context_refactor.models`
- `context_refactor.dependency_analyzer`
- `context_refactor.refactor_heuristics`

Ao evoluir o sistema:

- mantenha a fachada publica estavel
- mova a complexidade para modulos especializados
- evite expor helpers internos como contrato externo

## Pontos de acoplamento

- output do `token_report.py`
- forma como escopo e dependencia sao resolvidos no analyzer
- paridade de parametros entre CLI e MCP
- serializacao aditiva dos payloads publicos

## Riscos conhecidos

- divergencia entre documentacao historica e documentacao canonica
- respostas grandes para clientes sem paginacao
- falta de auth e rate limit no servidor MCP
- drift entre fallback JSON-RPC e modo SDK se novos campos nao forem testados

## Boas praticas para alteracoes futuras

1. altere contratos de forma retrocompativel sempre que possivel
2. se houver breaking change, documente deprecacao e migracao
3. atualize teste e docs na mesma PR
4. mantenha CLI e MCP sincronizados
5. prefira adicionar a nova logica no modulo de dominio, nao na fachada

## Roadmap tecnico sugerido

- validacao formal de schema
- observabilidade estruturada
- capabilities MCP adicionais
- melhor padronizacao de erros para consumidores

