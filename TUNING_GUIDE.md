# ContextRefactor Tuning Guide

Este guia descreve como reduzir ruído nas análises para aumentar o valor das recomendações.

## Objetivo

Evitar que artefatos gerados (coverage, reports, outputs temporários, snapshots) dominem os resultados, mantendo foco em código acionável.

## Perfis de análise

| Perfil | Uso recomendado |
|---|---|
| default | Fluxo diário com redução de ruído e visão ampla de código + markdown |
| full | Auditoria completa sem exclusões padrão |
| source-only | Refatoração de código de produção |
| docs | Limpeza e modularização de documentação |

## Arquivo de configuração por repositório

Por padrão, o ContextRefactor procura um arquivo chamado .context-refactor.json na raiz do projeto.

Exemplo:

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

## Precedência

1. Defaults do perfil
2. Configuração do repositório
3. Parâmetros explícitos do CLI/MCP

Ou seja, parâmetros passados no comando sempre têm prioridade final.

## Campos aceitos

- analysis_profile
- exclude_dirs
- exclude_globs
- exclude_files
- include_categories
- exclude_categories

Categorias válidas:

- source_code
- markdown
- configuration
- binary
- other

## Estratégias recomendadas por tipo de execução

### Refatoração de backend/frontend

- Perfil: source-only
- Include categories: source_code
- Excluir docs/planning e outputs de cobertura

### Planejamento de documentação

- Perfil: docs
- Include categories: markdown
- Excluir coverage, reports e outputs gerados

### Auditoria de footprint global

- Perfil: full
- Sem include/exclude de categoria
- Usar apenas exclusões estritamente temporárias

## Interpretação dos novos metadados

As respostas agora incluem:

- analysis_scope: configuração final efetivamente aplicada
- category_counts: total de arquivos por categoria após filtros
- category_tokens: total de tokens por categoria após filtros

Esses três blocos permitem validar rapidamente se o escopo está correto antes de agir sobre recomendações.

## Checklist de qualidade da análise

- Top 20 não deve ser dominado por coverage/lcov-report
- category_counts deve refletir o objetivo da execução
- Smells prioritários devem aparecer em source_code para execução de refatoração
- Se os resultados parecerem ruidosos, ajustar primeiro exclude_globs e include_categories

## Comandos úteis

Executar análise source-only:

context-refactor analyze /path/to/project --profile source-only

Executar análise com config explícita:

context-refactor analyze /path/to/project --config /path/to/.context-refactor.json

Executar orçamento de contexto focado em código:

context-refactor budget /path/to/project --profile source-only

---

## Autonomia e Integração Independente

### Contrato de Execução

O ContextRefactor é um produto autônomo que:

1. **Não depende de projetos externos** — Todas as dependências estão em `pyproject.toml`
2. **Executa em qualquer diretório** — token_report.py é localizado dinamicamente
3. **Suporta fallback graceful** — MCP funciona via JSON-RPC se SDK não está instalado
4. **Valida configuração explicitamente** — .context-refactor.json inválido resulta em erro claro

### Troubleshooting

#### "FileNotFoundError: token_report.py not found"

**Solução:**

```bash
pip install --force-reinstall -e .[dev,mcp]
```

#### "Unknown category" ValueError

**Solução:** Verificar que `include_categories` e `exclude_categories` usam apenas:
- `source_code`, `markdown`, `configuration`, `binary`, `other`

#### Análise muito lenta (timeout)

**Solução:** Usar perfil `source-only` ou aumentar exclusões na configuração
