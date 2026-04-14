# ContextRefactor

[![Test Suite](https://github.com/wallacegsouza/context-refactor/actions/workflows/test.yml/badge.svg)](https://github.com/wallacegsouza/context-refactor/actions/workflows/test.yml)
[![Code Quality](https://github.com/wallacegsouza/context-refactor/actions/workflows/quality.yml/badge.svg)](https://github.com/wallacegsouza/context-refactor/actions/workflows/quality.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)


Analise semantica e refatoracao orientada a contexto para codebases que
precisam caber em uma janela de contexto de LLM.

O projeto combina `token_report.py`, analise estrutural, recomendacoes
heuristicas e um servidor MCP para responder perguntas praticas:

- o repositorio cabe no contexto alvo?
- quais arquivos concentram mais custo de entendimento e refatoracao?
- qual sequencia de refactors reduz melhor o tamanho efetivo do projeto?

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,mcp]"
```

Requisitos:

- Python 3.11+
- `mcp` e opcional para o servidor MCP nativo
- `matplotlib` e opcional para graficos do `token_report.py`

## Inicio rapido

Analise completa:

```bash
context-refactor analyze /path/to/project --profile default
```

Budget apenas:

```bash
context-refactor budget /path/to/project --context-size 128000 --safety-margin 0.8
```

Heuristicas por arquivo:

```bash
context-refactor smells /path/to/project --top 20
```

Plano por heuristicas:

```bash
context-refactor suggest /path/to/project --profile source-only
```

Servidor MCP:

```bash
context-refactor serve
```

Todos os comandos aceitam `--json`.

## Perfis de analise

| Perfil | Uso recomendado |
|---|---|
| `default` | Fluxo diario com reducao de ruido e visao ampla de codigo + markdown |
| `full` | Auditoria completa sem exclusoes padrao |
| `source-only` | Refatoracao de codigo de producao |
| `docs` | Revisao e modularizacao de documentacao |

Arquivo opcional por repositorio:

```json
{
  "analysis": {
    "analysis_profile": "default",
    "exclude_dirs": ["coverage", "reports", "token-report"],
    "exclude_globs": ["docs/planning", "docs/planning/*"],
    "exclude_files": ["*.map", "*.snap"],
    "include_categories": ["source_code", "markdown"],
    "exclude_categories": ["other"]
  }
}
```

## Modos de dependencia

As ferramentas publicas aceitam configuracao opcional de dependencias:

- `off`: desabilita enriquecimento por dependencias
- `report_only`: calcula metadados sem alterar a ordenacao legacy
- `blended`: combina tokens brutos e acoplamento
- `weighted`: prioriza o tamanho efetivo orientado a dependencia

Parametros relacionados:

- `dependency_mode`
- `dependency_max_depth`
- `dependency_max_multiplier`
- `dependency_base_weight`
- `dependency_depth_decay`
- `dependency_depth_weights`

## Tools MCP expostas

O servidor expoe 6 tools publicas:

| Tool | Objetivo |
|---|---|
| `context_refactor.analyze_project` | Analise completa com budget, hotspots, recomendacoes e plano |
| `context_refactor.context_budget` | Calculo rapido de cabimento no contexto |
| `context_refactor.detect_refactor_candidates` | Candidatos de refatoracao pela pipeline legacy |
| `context_refactor.generate_refactor_plan` | Plano sequencial para caber no contexto |
| `context_refactor.detect_code_smells` | Smells por arquivo via Heuristics Engine |
| `context_refactor.generate_refactor_suggestions` | Sugestoes heuristicas + plano |

Configuracao generica de host MCP:

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

Se o SDK `mcp` nao estiver instalado, o servidor entra em fallback JSON-RPC
via stdin/stdout.

## Arquitetura atual

O projeto foi modularizado para preservar contratos publicos enquanto a
implementacao interna foi dividida por dominio.

```text
context-refactor/
├── cli/
│   ├── main.py                 # entrypoint/facade do script context-refactor
│   ├── app.py                  # fabrica do app Typer
│   ├── commands/
│   │   ├── analysis.py         # analyze, budget, candidates
│   │   ├── heuristics.py       # smells, suggest, plan
│   │   └── server.py           # serve
│   ├── options.py              # opcoes compartilhadas
│   ├── rendering.py            # saida rich/tabular
│   └── shared.py               # execucao e normalizacao compartilhadas
├── context_refactor/
│   ├── analyzer.py             # facade publica da pipeline de analise
│   ├── analyzer_*.py           # classificacao, config, metricas e runner
│   ├── dependency_analyzer.py  # facade publica de dependencias
│   ├── dependency_*.py         # extracao, resolucao, grafo e pesos
│   ├── models.py               # facade publica de modelos
│   ├── model_*.py              # tipos de tokens, resultados e refatoracao
│   ├── refactor_heuristics.py  # facade publica do Heuristics Engine
│   ├── refactor_heuristics_*   # engine e helpers do dominio
│   ├── refactor_engine.py      # candidatos legacy
│   ├── refactor_planner.py     # montagem do plano
│   └── refactor_rules/         # regras plugaveis
├── mcp_server/
│   ├── server.py               # stdio MCP + fallback JSON-RPC
│   ├── tools.py                # facade publica das tools MCP
│   ├── tools_analysis.py       # tools de analise e plano legacy
│   ├── tools_heuristics.py     # tools do Heuristics Engine
│   ├── tool_support.py         # facade de helpers MCP
│   └── tool_support_*          # helpers de analise, heuristicas e legado
├── token_report.py             # fonte de verdade da contagem bruta
└── docs/                       # documentacao canonica do projeto
```

## Qualidade e validacao

Comandos mais usados:

```bash
make test
make test-cov
make lint
make format
make type-check
make ci
```

Ou diretamente:

```bash
pytest tests/ -v
ruff check context_refactor tests cli mcp_server token_report.py
ruff format --check context_refactor tests cli mcp_server token_report.py
mypy context_refactor mcp_server cli --ignore-missing-imports
```

## Documentacao

A documentacao canonica detalhada esta em [docs/INDEX.md](docs/INDEX.md).

Pontos de entrada recomendados:

- [Visao geral](docs/visao-geral.md)
- [Guia do usuario](docs/usuario/guia-do-usuario.md)
- [Ferramentas MCP](docs/usuario/ferramentas.md)
- [Arquitetura](docs/desenvolvedor/arquitetura.md)

