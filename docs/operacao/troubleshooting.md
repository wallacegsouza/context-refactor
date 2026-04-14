# Operacao e Troubleshooting

## Visao operacional

O ContextRefactor roda como processo stdio, normalmente sob controle de um
host MCP ou pela propria CLI.

## Modos de execucao

- CLI: `context-refactor ...`
- MCP nativo: `python3 -m mcp_server.server`
- fallback: JSON-RPC em stdin/stdout sem o SDK `mcp`

## Problemas comuns

### 1. A tool nao aparece no host

Causas provaveis:

- comando ou `cwd` incorreto no registro do host
- pacote nao instalado no ambiente do host
- processo nao iniciou corretamente

Diagnostico:

1. Execute `python3 -m mcp_server.server` manualmente.
2. Confirme que o ambiente consegue importar o pacote.
3. Verifique se `list_tools` retorna 6 tools `context_refactor.*`.

### 2. `Unknown tool`

Causas provaveis:

- nome incorreto
- cache antigo no host
- servidor diferente do esperado

Acao:

- use nomes `context_refactor.*` exatos
- reinicie o host
- valide o catalogo retornado por `list_tools`

### 3. Erro de `project_path`

Sintoma:

- falha ao analisar o diretorio

Acao:

- confirme que o path existe
- prefira path absoluto
- confira permissao de leitura

### 4. Erro de categoria, perfil ou dependencia

Acao:

- categorias validas:
  `source_code`, `markdown`, `configuration`, `binary`, `other`
- perfis validos:
  `default`, `full`, `source-only`, `docs`
- modos de dependencia validos:
  `off`, `report_only`, `blended`, `weighted`

### 5. Falha no `token_report.py`

Causas provaveis:

- script ausente ou indisponivel
- erro no subprocess
- ambiente Python inconsistente

Acao:

- verifique a existencia de `token_report.py`
- valide a execucao local do script
- revise o ambiente virtual e dependencias

### 6. Host sem SDK MCP

Sintoma:

- mensagem de fallback em stderr

Leitura:

- isso e esperado quando o pacote `mcp` nao esta instalado
- o servidor continua funcional em fallback JSON-RPC

## Checklist rapido

1. O processo sobe sem erro?
2. `list_tools` retorna 6 tools?
3. `context_refactor.context_budget` responde com JSON?
4. O host esta no ambiente Python correto?
5. O mesmo problema ocorre pela CLI?

## Monitoramento e limites

- nao ha monitoramento embutido
- retries e timeouts de transporte ficam a cargo do host
- respostas grandes devem ser limitadas com `top_n`, perfil e filtros

## Escalacao de diagnostico

- reproduza pela CLI para isolar o problema do host
- reproduza por uma chamada minima de MCP
- colete o payload de entrada e a mensagem de erro retornada

