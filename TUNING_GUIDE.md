# Guia de Tuning do ContextRefactor

Este guia descreve como reduzir ruido nas analises para aumentar o valor das
recomendacoes.

## Objetivo

Evitar que artefatos gerados, cobertura, relatorios e saidas temporarias
dominem os resultados, mantendo o foco em codigo e documentacao acionaveis.

## Perfis de analise

| Perfil | Uso recomendado |
|---|---|
| `default` | Fluxo diario com reducao de ruido e visao ampla de codigo + markdown |
| `full` | Auditoria completa sem exclusoes padrao |
| `source-only` | Refatoracao de codigo de producao |
| `docs` | Limpeza e modularizacao de documentacao |

## Arquivo de configuracao por repositorio

Por padrao, o ContextRefactor procura `.context-refactor.json` na raiz do
projeto.

Exemplo:

```json
{
  "analysis": {
    "analysis_profile": "default",
    "exclude_dirs": ["coverage", "lcov-report", "reports", "token-report"],
    "exclude_globs": ["docs/planning", "docs/planning/*"],
    "exclude_files": ["backend/lint.result.txt", "*.map", "*.snap"],
    "include_categories": ["source_code", "markdown"],
    "exclude_categories": ["other"]
  }
}
```

## Precedencia

1. Defaults do perfil
2. Configuracao do repositorio
3. Parametros explicitos de CLI ou MCP

Ou seja, o comando sempre tem a palavra final.

## Campos aceitos

- `analysis_profile`
- `exclude_dirs`
- `exclude_globs`
- `exclude_files`
- `include_categories`
- `exclude_categories`

Categorias validas:

- `source_code`
- `markdown`
- `configuration`
- `binary`
- `other`

## Modos de dependencia

Use os modos de dependencia apenas quando quiser que a analise reflita custo
estrutural alem do volume bruto.

| Modo | Efeito |
|---|---|
| `off` | Mantem somente tokens brutos |
| `report_only` | Calcula metadados sem alterar a ordenacao legacy |
| `blended` | Mistura volume bruto com acoplamento |
| `weighted` | Priorizacao mais agressiva por tamanho efetivo |

Parametros adicionais:

- `dependency_max_depth`
- `dependency_max_multiplier`
- `dependency_base_weight`
- `dependency_depth_decay`
- `dependency_depth_weights`

## Estrategias recomendadas

### Refatoracao de codigo

- perfil: `source-only`
- incluir: `source_code`
- excluir: `coverage`, `reports`, snapshots e artefatos locais
- dependencia: `report_only` para observacao, `blended` para priorizacao

### Documentacao

- perfil: `docs`
- incluir: `markdown`
- excluir: `reports`, `token-report` e gerados temporarios

### Auditoria global

- perfil: `full`
- aplicar apenas exclusoes claramente temporarias
- usar `report_only` primeiro para inspecionar `dependency_analysis`

## Como interpretar a resposta

As respostas publicas incluem campos que ajudam a validar o escopo antes de
agir:

- `analysis_scope`: configuracao final efetivamente aplicada
- `noise_summary`: resumo do que foi filtrado
- `signal_score`: leitura agregada de sinal vs ruido
- `category_counts`: arquivos por categoria apos filtros
- `category_tokens`: tokens por categoria apos filtros
- `dependency_analysis`: metadados do modo de dependencia

Ferramentas que pedem hotspots tambem podem retornar:

- `dependency_hotspots`

## Checklist de qualidade da analise

- o top de arquivos nao deve ser dominado por coverage ou relatorios
- `analysis_scope` precisa refletir a intencao do comando
- `category_counts` deve bater com o objetivo da execucao
- se houver dependencia habilitada, `dependency_analysis` precisa fazer sentido
- se o resultado parecer ruidoso, ajuste primeiro filtros e perfil

## Comandos uteis

Analise focada em codigo:

```bash
context-refactor analyze /path/to/project --profile source-only
```

Budget focado em codigo com dependencia em modo observacao:

```bash
context-refactor budget /path/to/project --profile source-only --dependency-mode report_only
```

Analise com config explicita:

```bash
context-refactor analyze /path/to/project --config /path/to/.context-refactor.json
```

## Troubleshooting rapido

Erro `token_report.py not found`:

```bash
pip install --force-reinstall -e ".[dev,mcp]"
```

Erro de categoria invalida:

- revise `include_categories` e `exclude_categories`
- use apenas `source_code`, `markdown`, `configuration`, `binary`, `other`

Analise muito lenta:

- reduza o escopo com `source-only` ou `docs`
- aumente exclusoes no arquivo `.context-refactor.json`
- use `report_only` antes de `blended` ou `weighted`

