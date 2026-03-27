# Fluxos Internos e Contratos

## Fluxo de Inicializacao do MCP

1. `run_server()` escolhe modo SDK ou fallback.
2. SDK: cria servidor, registra `list_tools` e `call_tool`.
3. Fallback: loop JSON-RPC em stdin/stdout.

## Fluxo de Registro de Tools

No boot, `list_tools` retorna o catalogo de 6 tools com schema de entrada.

## Fluxo de Recebimento e Execucao de Chamada

1. Cliente chama tool por nome.
2. Dispatcher resolve funcao em `mcp_server/tools.py`.
3. Tool chama `analyze_tokens` e/ou motores de recomendacao.
4. Resultado vira JSON para resposta ao cliente.

## Fluxo de Validacao

- Validacoes principais estao no core (`analyzer.py`), especialmente categorias/perfis.
- Sem camada dedicada de schema validation no servidor MCP atual.

## Fluxo de Resposta

- Modo SDK: `TextContent` com JSON serializado.
- Fallback: objeto JSON-RPC `result` ou `error`.

## Tratamento de Erros

- Tool desconhecida retorna erro de lookup.
- Excecoes internas retornam mensagem de erro.
- Falhas de subprocess/arquivo podem interromper analise.

## Timeouts, Retries e Fallback

- Timeout/retry: responsabilidade do host/cliente.
- Fallback: automatico quando SDK MCP nao instalado.

## Exemplo Resumido de Fluxo

```text
Host MCP -> call_tool(name, arguments)
          -> mcp_server.tools.fn(...)
          -> context_refactor.*
          -> JSON response
```

## Referencias

- [Contratos MCP](../integracao/contratos.md)
- [Arquitetura](./arquitetura.md)
