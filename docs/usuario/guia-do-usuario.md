# Guia do Usuario

## O que o ContextRefactor faz

O ContextRefactor responde perguntas praticas sobre tamanho, ruido e custo de
refatoracao:

- meu repositorio cabe no contexto do modelo?
- quais arquivos concentram maior impacto?
- qual plano reduz tokens com melhor custo-beneficio?

## Fluxo recomendado

1. Rode `budget` para saber se o escopo cabe no contexto.
2. Rode `analyze` para ter visao completa com hotspots e plano.
3. Rode `smells` ou `candidates` para localizar causas.
4. Rode `suggest` ou `plan` para priorizar acoes.
5. Reexecute a analise e compare os resultados.

## Comandos CLI mais usados

```bash
context-refactor budget /path/to/repo --context-size 128000 --safety-margin 0.8
context-refactor analyze /path/to/repo --profile default
context-refactor candidates /path/to/repo --top 30
context-refactor smells /path/to/repo --top 20
context-refactor suggest /path/to/repo --profile source-only
context-refactor plan /path/to/repo --context-size 128000
```

## Perfis de analise

- `default`: reduz ruido comum e mantem codigo + markdown
- `full`: inclui tudo o que o scanner conseguir ver
- `source-only`: foca em codigo-fonte
- `docs`: foca em markdown

Na CLI, o argumento e `--profile`.
No MCP, o campo equivalente e `analysis_profile`.

## Modos de dependencia

Use `--dependency-mode` na CLI ou `dependency_mode` no MCP quando quiser levar
em conta acoplamento estrutural alem do tamanho bruto:

- `off`
- `report_only`
- `blended`
- `weighted`

## Entradas esperadas

- `project_path` valido
- parametros numericos coerentes, como `context-size` e `safety-margin`
- categorias validas em `include_categories` e `exclude_categories`
- filtros de escopo quando quiser reduzir ruido

## Saidas mais importantes

Campos compartilhados por varias tools:

- `analysis_scope`
- `noise_summary`
- `signal_score`
- `category_counts`
- `category_tokens`
- `dependency_analysis`

Dependendo da tool, tambem aparecem:

- `project_summary`
- `context_budget`
- `largest_files`
- `largest_directories`
- `refactor_recommendations`
- `dependency_hotspots`
- `heuristic_results`
- `refactor_plan`

## Como interpretar rapidamente

- `fits_context=true`: o escopo atual cabe no budget configurado
- `overflow_tokens>0`: ainda existe excesso a reduzir
- `dependency_analysis`: mostra como a analise de dependencias foi aplicada
- `dependency_hotspots`: destaca arquivos mais caros no modo de dependencia
- `estimated_token_reduction`: e heuristico, nao garantia absoluta

## Erros comuns

- path invalido ou sem permissao
- categoria invalida
- `token_report.py` indisponivel
- ambiente sem `mcp` quando o host espera modo MCP nativo

## Proximo passo

- Consulte [Ferramentas MCP](./ferramentas.md) para contratos resumidos
- Consulte [Exemplos de Uso](./exemplos-de-uso.md) para payloads e respostas
- Consulte [Troubleshooting](../operacao/troubleshooting.md) para diagnostico

