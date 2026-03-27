# Configuracao em Clientes/Hosts MCP

## Como Este MCP e Consumido

O servidor e executado via stdio e pode ser registrado em clientes MCP que suportam comando externo.

The server uses stdio transport and can be registered in MCP-compatible clients.

## Requisitos de Integracao

- Python 3.11+
- Ambiente com pacote instalado (`pip install -e ".[mcp]"` recomendado)
- Acesso ao diretorio do projeto alvo

## Exemplo de Registro (Generico)

```json
{
  "mcpServers": {
    "context-refactor": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "${workspaceFolder}",
      "env": {"PYTHONUNBUFFERED": "1"}
    }
  }
}
```

## Transporte/Comunicacao

- Modo principal: MCP SDK sobre stdio.
- Modo fallback: loop JSON-RPC em stdin/stdout quando SDK nao esta disponivel.

## Como Validar Carregamento Correto

1. Inicie o cliente/host.
2. Verifique se a listagem de tools inclui as 6 tools `context_refactor.*`.
3. Execute chamada simples (`context_budget`).
4. Confirme resposta JSON valida.

## Exemplo de Validacao Rapida Fora do Host

```bash
python3 -m mcp_server.server
```

Se o SDK MCP nao estiver instalado, a mensagem de fallback e esperada.

## Observacoes de Compatibilidade

- Sem auth flow nativo: use isolamento do host/ambiente.
- Sem streaming/eventos: respostas sao completas por chamada.
- Garanta path absoluto correto em `project_path` para evitar erros de resolucao.

## Referencias

- [Contratos e Comunicacao MCP](./contratos.md)
- [Ferramentas MCP](../usuario/ferramentas.md)
- [Troubleshooting](../operacao/troubleshooting.md)
