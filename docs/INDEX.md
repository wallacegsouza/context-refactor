# Documentacao do ContextRefactor

Documentacao canonica do ContextRefactor organizada por audiencia e objetivo.

## Navegacao rapida

### Visao geral

- [Visao Geral](./visao-geral.md)
- [Guia do Usuario](./usuario/guia-do-usuario.md)
- [Ferramentas MCP](./usuario/ferramentas.md)
- [Exemplos de Uso](./usuario/exemplos-de-uso.md)

### Integracao

- [Configuracao em Clientes/Hosts](./integracao/configuracao-em-clientes.md)
- [Contratos e Comunicacao MCP](./integracao/contratos.md)

### Desenvolvimento

- [Arquitetura](./desenvolvedor/arquitetura.md)
- [Modulos](./desenvolvedor/modulos.md)
- [Fluxos Internos](./desenvolvedor/fluxos.md)
- [Setup de Desenvolvimento](./desenvolvedor/setup.md)
- [Adicionar Nova Tool](./desenvolvedor/adicionar-nova-tool.md)
- [Qualidade e Testes](./desenvolvedor/qualidade-e-testes.md)
- [Manutencao e Evolucao](./desenvolvedor/manutencao.md)

### Operacao

- [Operacao e Troubleshooting](./operacao/troubleshooting.md)

## Documentacao canonica vs historico

Use `README.md` e os documentos desta arvore `docs/` como fonte de verdade do
estado atual do projeto.

O documento abaixo e historico e descreve a evolucao da feature, nao o desenho
canonico atual:

- [Plano: Evolucao do Token Report com Peso de Dependencias](./plano-novo-token-report.md)

## Guia por audiencia

- Usuario final: comece por [Guia do Usuario](./usuario/guia-do-usuario.md)
- Integrador MCP: comece por
  [Configuracao em Clientes/Hosts](./integracao/configuracao-em-clientes.md)
- Desenvolvedor: comece por [Arquitetura](./desenvolvedor/arquitetura.md) e
  [Setup](./desenvolvedor/setup.md)

## Estado atual de capability

Implementado:

- 6 tools MCP publicas via `list_tools` e `call_tool`
- transporte stdio no modo SDK
- fallback JSON-RPC em stdin/stdout
- perfis de analise, filtros de escopo e modos de dependencia

Nao implementado:

- resources
- prompts
- templates
- streaming
- eventos
- context providers
- auth flows
