# Configuracao em Clientes e Hosts MCP

## Como este servidor e consumido

O servidor roda por stdio e pode ser registrado em clientes MCP que suportam
comando externo.

Se o SDK `mcp` nao estiver instalado, o processo entra em fallback JSON-RPC em
stdin/stdout.

## Requisitos de integracao

- Python 3.11+
- pacote instalado no ambiente do host
- acesso ao diretorio do projeto alvo
- `cwd` coerente quando o host usar `${workspaceFolder}`

## Configuracao generica

```json
{
  "mcpServers": {
    "context-refactor": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Como validar o carregamento

1. Inicie o host.
2. Verifique se `list_tools` retorna 6 tools `context_refactor.*`.
3. Execute uma chamada simples, como `context_refactor.context_budget`.
4. Confirme resposta JSON valida.

## Validacao rapida fora do host

```bash
python3 -m mcp_server.server
```

Se o SDK `mcp` nao estiver instalado, a mensagem de fallback e esperada.

## Observacoes de compatibilidade

- o contrato publico das tools esta em `mcp_server/server.py`
- a fachada publica de execucao esta em `mcp_server/tools.py`
- modulos internos podem mudar sem alterar o nome das tools
- use `project_path` absoluto sempre que possivel

## Limitacoes operacionais

- sem auth flow nativo
- sem streaming ou eventos
- sem retries internos; isso fica a cargo do host
- respostas grandes podem exigir `top_n` menor ou filtros de escopo

## Referencias

- [Contratos e Comunicacao MCP](./contratos.md)
- [Ferramentas MCP](../usuario/ferramentas.md)
- [Operacao e Troubleshooting](../operacao/troubleshooting.md)

