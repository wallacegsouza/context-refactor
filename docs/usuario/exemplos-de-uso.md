# Exemplos de Uso

Exemplos resumidos de interacao via CLI e via MCP.

Short practical examples for CLI and MCP integration.

## Exemplo 1: Diagnostico Completo (CLI)

```bash
context-refactor analyze /repo --context-size 128000 --safety-margin 0.8 --profile default
```

### Leitura rapida do resultado

- Veja `project_summary.total_tokens`.
- Compare com `context_budget.context_budget`.
- Se nao couber, siga `refactor_plan.steps`.

## Exemplo 2: Somente Budget (CLI)

```bash
context-refactor budget /repo --context-size 200000 --safety-margin 0.75 --json
```

### Resultado esperado (resumo)

```json
{
  "fits_context": true,
  "overflow_tokens": 0
}
```

## Exemplo 3: Smells por Heuristica (CLI)

```bash
context-refactor smells /repo --context-size 128000 --top 20
```

### Quando usar

Quando voce quer problemas por arquivo (`problems`, `suggested_refactors`), nao apenas candidatos agregados.

## Exemplo 4: Chamada MCP (tools/call)

Exemplo logico de payload (SDK/fallback abstraem detalhes no cliente):

```json
{
  "name": "context_refactor.context_budget",
  "arguments": {
    "project_path": "/repo",
    "llm_context_size": 128000,
    "safety_margin": 0.8,
    "analysis_profile": "default"
  }
}
```

## Exemplo 5: Filtros de Escopo

```bash
context-refactor candidates /repo \
  --profile source-only \
  --exclude-dirs "coverage,reports" \
  --exclude-globs "*.map,*.snap"
```

Use filtros para remover ruido e melhorar a qualidade da recomendacao.

## Erros Comuns em Uso

- Path nao existe.
- Categoria invalida em include/exclude.
- Ambiente sem dependencias (`mcp`, `typer`, etc.).
- Falha no subprocess de `token_report.py`.

Consulte tambem [Ferramentas MCP](./ferramentas.md) e [Troubleshooting](../operacao/troubleshooting.md).
