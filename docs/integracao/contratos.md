# Contratos e Comunicacao MCP

## Contratos Principais

### list_tools

Retorna metadados das tools registradas (nome, descricao, schema de entrada).

### call_tool

Recebe `name` e `arguments`, despacha para a funcao correspondente e retorna JSON serializado.

## Tools Registradas

- `context_refactor.analyze_project`
- `context_refactor.context_budget`
- `context_refactor.detect_refactor_candidates`
- `context_refactor.generate_refactor_plan`
- `context_refactor.detect_code_smells`
- `context_refactor.generate_refactor_suggestions`

## Campos de Entrada Relevantes

- `project_path` (required em todas as tools)
- `llm_context_size`, `safety_margin`, `top_n` (quando aplicavel)
- `estimator`: `bytes|chars|whitespace|heuristic`
- `analysis_profile`: `default|full|source-only|docs`
- filtros de escopo: `exclude_*`, `include_categories`, `exclude_categories`

## Regras de Validacao

- validacao de categorias ocorre no core (`analyzer`).
- valores invalidos podem gerar erro de execucao.
- tool desconhecida retorna erro/unknown tool.

## Estruturas de Resposta (Alto Nivel)

- `analysis_scope`, `noise_summary`, `signal_score`
- resumo de budget (`fits_context`, `overflow_tokens`)
- listas de recomendacao/plano dependendo da tool

## Timeouts, Retries e Fallback

- Nao ha politica de retry nativa no servidor.
- Timeouts dependem do host/cliente integrador.
- Fallback JSON-RPC entra automaticamente sem SDK MCP.

## Tratamento de Erros

- Modo SDK: retorno textual com `Error: ...` em excecoes.
- Modo fallback: erro JSON-RPC com codigo e mensagem.

## Capabilities MCP Nao Implementadas

- resources
- prompts
- templates
- streams
- eventos
- context providers
- auth flows

Documente essa lacuna no host para evitar expectativas incorretas.

## Exemplo Resumido de Chamada

```json
{
  "name": "context_refactor.detect_refactor_candidates",
  "arguments": {"project_path": "/repo", "top_n": 20}
}
```
