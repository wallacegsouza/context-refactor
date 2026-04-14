# Exemplos de Uso

Exemplos resumidos de uso via CLI e via MCP.

## Exemplo 1: analise completa pela CLI

```bash
context-refactor analyze /repo \
  --context-size 128000 \
  --safety-margin 0.8 \
  --profile default \
  --dependency-mode report_only
```

Leitura rapida:

- veja `project_summary.total_tokens`
- compare com `context_budget.context_budget`
- use `dependency_analysis` para validar o modo de dependencia
- siga `refactor_plan.steps` se o projeto nao couber

## Exemplo 2: budget em JSON

```bash
context-refactor budget /repo --context-size 200000 --safety-margin 0.75 --json
```

Resposta resumida:

```json
{
  "fits_context": true,
  "overflow_tokens": 0,
  "analysis_scope": {
    "analysis_profile": "default"
  }
}
```

## Exemplo 3: candidatos legacy

```bash
context-refactor candidates /repo --top 30 --profile source-only
```

Quando usar:

- quando voce quer uma lista priorizada de recomendacoes por arquivo
- quando quer manter o fluxo legacy de candidatos

## Exemplo 4: smells por heuristica

```bash
context-refactor smells /repo --context-size 128000 --top 20 --dependency-mode blended
```

Quando usar:

- quando voce quer `problems` e `suggested_refactors` por arquivo
- quando quer ver impacto de dependencia no resultado por arquivo

## Exemplo 5: plano por heuristicas

```bash
context-refactor suggest /repo --profile source-only --json
```

Resposta resumida:

```json
{
  "context_budget": {
    "fits_context": false
  },
  "heuristic_results": [
    {
      "file": "/repo/service.py",
      "problems": ["Large Class"]
    }
  ],
  "refactor_plan": {
    "steps": [
      {"step_number": 1, "title": "Extract Class"}
    ]
  }
}
```

## Exemplo 6: chamada MCP

Payload logico:

```json
{
  "name": "context_refactor.context_budget",
  "arguments": {
    "project_path": "/repo",
    "llm_context_size": 128000,
    "safety_margin": 0.8,
    "analysis_profile": "default",
    "dependency_mode": "report_only"
  }
}
```

## Exemplo 7: filtros de escopo

```bash
context-refactor analyze /repo \
  --profile source-only \
  --exclude-dirs "coverage,reports" \
  --exclude-globs "*.map,*.snap" \
  --exclude-files "lint.result.txt"
```

Use filtros para remover ruido e melhorar a qualidade da recomendacao.

## Erros comuns

- path inexistente
- categoria invalida em include/exclude
- ambiente sem dependencias esperadas
- falha no subprocess de `token_report.py`

Consulte tambem [Ferramentas MCP](./ferramentas.md) e
[Troubleshooting](../operacao/troubleshooting.md).

