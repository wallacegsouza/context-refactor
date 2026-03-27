# Operacao e Troubleshooting

## Visao Operacional

Este MCP roda por stdio, normalmente sob controle de um host/cliente MCP.

Operationally, this server is a stdio process managed by a host/client.

## Logs e Sinais

- Em fallback sem SDK MCP, mensagem de aviso e emitida em stderr.
- Erros de tool podem retornar texto/JSON-RPC error dependendo do modo.

## Problemas Comuns

### 1. Tool nao aparece no host

Causas provaveis:
- caminho/command incorreto no registro do host
- ambiente sem pacote instalado
- processo nao iniciou

Diagnostico:
1. Executar `python3 -m mcp_server.server` manualmente.
2. Confirmar imports do pacote no mesmo ambiente.
3. Validar configuracao do host.

### 2. `Unknown tool`

Causas provaveis:
- nome incorreto
- host usando cache antigo
- versao diferente do server

Acao:
- usar nomes `context_refactor.*` exatos.
- reiniciar host para recarregar catalogo.

### 3. Erro de path/projeto

Sintoma:
- falha ao analisar diretoria

Acao:
- confirmar `project_path` absoluto e existente.
- conferir permissao de leitura.

### 4. Erro de categoria/perfil

Sintoma:
- erro de validacao ao passar filtros

Acao:
- usar categorias validas: `source_code`, `markdown`, `configuration`, `binary`, `other`.
- usar perfis validos: `default`, `full`, `source-only`, `docs`.

### 5. Falha no `token_report.py`

Causas provaveis:
- script ausente/indisponivel
- erro no subprocess
- ambiente Python inconsistente

Acao:
- verificar existencia do arquivo `token_report.py`.
- validar execucao local do script.
- revisar ambiente virtual e dependencias.

## Troubleshooting de Integracao MCP

Checklist rapido:

1. Processo sobe sem erro?
2. `list_tools` retorna 6 tools?
3. `context_budget` responde com JSON?
4. Host esta no ambiente Python correto?

## Monitoramento e Limites

- Nao ha monitoramento embutido no servidor atual.
- Nao ha retries/timeouts internos; configure no host.
- Respostas podem ser grandes; prefira filtros e `top_n`.

## Escalacao de Diagnostico

- Reproduzir via CLI (`context-refactor ...`) para isolar problema de host.
- Reproduzir via chamada MCP minima (`context_budget`).
- Se persistir, coletar payload de entrada e erro retornado para analise.
