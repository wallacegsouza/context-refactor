# Como Adicionar Nova Tool ou Capability

## Objetivo

Guia para estender o servidor MCP sem quebrar compatibilidade publica.

## Fluxo recomendado

1. Defina a responsabilidade da nova tool:
   analise/legacy ou heuristicas.
2. Implemente a funcao no modulo de dominio apropriado:
   `mcp_server/tools_analysis.py` ou `mcp_server/tools_heuristics.py`.
3. Reexporte a funcao em `mcp_server/tools.py` se ela fizer parte da
   superficie publica MCP.
4. Registre schema, descricao e nome da tool em `mcp_server/server.py`.
5. Garanta que o fallback JSON-RPC continue enxergando a tool via o mesmo
   caminho publico.
6. Adicione testes cobrindo listagem, chamada valida, erro e serializacao.
7. Atualize docs de usuario, integracao e desenvolvedor.

## Checklist de contrato

- nome consistente: `context_refactor.<novo_nome>`
- `project_path` quando aplicavel
- retorno JSON serializavel
- tratamento de erros compreensivel
- parametros alinhados com CLI, se houver comando correspondente

## Boas praticas

- reutilize `tool_support_analysis.py`, `tool_support_heuristics.py` e
  `tool_support_legacy.py`
- preserve campos existentes de retorno
- adicione novos campos de forma aditiva
- imponha limites como `top_n` quando houver listas grandes
- evite colocar logica nova na fachada `mcp_server/tools.py`

## Compatibilidade

- nao renomeie tools existentes sem estrategia de deprecacao
- nao remova campos publicos usados por clientes
- mantenha `mcp_server/tools.py` como fachada pequena e estavel
- documente breaking changes antes de implementa-las

## Validacao minima

1. A tool aparece em `list_tools`.
2. A chamada com argumentos validos funciona.
3. Entradas invalidas falham de forma compreensivel.
4. A resposta e serializavel no modo SDK e no fallback.

