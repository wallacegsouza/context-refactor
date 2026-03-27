# ContextRefactor Documentation

Documentacao oficial do projeto ContextRefactor como servidor MCP (Model Context Protocol), segmentada por audiencia e objetivo.

Official documentation for ContextRefactor as an MCP server, organized by audience and objective.

## Quick Navigation

- [Visao Geral](./visao-geral.md)
- [Guia do Usuario](./usuario/guia-do-usuario.md)
- [Ferramentas MCP](./usuario/ferramentas.md)
- [Exemplos de Uso](./usuario/exemplos-de-uso.md)
- [Configuracao em Clientes/Hosts](./integracao/configuracao-em-clientes.md)
- [Contratos e Comunicacao MCP](./integracao/contratos.md)
- [Arquitetura](./desenvolvedor/arquitetura.md)
- [Modulos](./desenvolvedor/modulos.md)
- [Setup de Desenvolvimento](./desenvolvedor/setup.md)
- [Fluxos Internos](./desenvolvedor/fluxos.md)
- [Adicionar Nova Tool](./desenvolvedor/adicionar-nova-tool.md)
- [Qualidade e Testes](./desenvolvedor/qualidade-e-testes.md)
- [Manutencao e Evolucao](./desenvolvedor/manutencao.md)
- [Operacao e Troubleshooting](./operacao/troubleshooting.md)

## Audience Guide

- Usuario final: comece por [Guia do Usuario](./usuario/guia-do-usuario.md).
- Integrador MCP: comece por [Configuracao em Clientes/Hosts](./integracao/configuracao-em-clientes.md).
- Desenvolvedor: comece por [Arquitetura](./desenvolvedor/arquitetura.md) e [Setup](./desenvolvedor/setup.md).

User-facing path: start with the user guide. Integrators: start with MCP client configuration. Developers: start with architecture and setup.

## Scope Coverage Matrix

- Proposito, publico e limitacoes: [Visao Geral](./visao-geral.md)
- Uso das tools/capabilities: [Ferramentas MCP](./usuario/ferramentas.md)
- Integracao com hosts/clientes: [Configuracao](./integracao/configuracao-em-clientes.md), [Contratos](./integracao/contratos.md)
- Arquitetura, modulos e fluxos: [Arquitetura](./desenvolvedor/arquitetura.md), [Modulos](./desenvolvedor/modulos.md), [Fluxos](./desenvolvedor/fluxos.md)
- Setup, execucao e testes: [Setup](./desenvolvedor/setup.md), [Qualidade e Testes](./desenvolvedor/qualidade-e-testes.md)
- Operacao e troubleshooting: [Troubleshooting](./operacao/troubleshooting.md)
- Manutencao e evolucao: [Manutencao](./desenvolvedor/manutencao.md), [Adicionar Nova Tool](./desenvolvedor/adicionar-nova-tool.md)

## Capability Status (Current Project)

### Implemented

- MCP tools via `list_tools` + `call_tool`.
- Stdio transport (SDK mode) and JSON-RPC fallback mode.
- Analysis profiles and scope filters.

### Not Implemented (as of this version)

- MCP resources
- MCP prompts
- MCP templates
- streaming responses
- events/pub-sub
- context providers
- auth flows

This is intentional current scope, not a runtime error.
