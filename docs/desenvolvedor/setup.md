# Setup de Desenvolvimento

## Pre-requisitos

- Python 3.11+
- `pip` atualizado
- ambiente virtual recomendado

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,mcp]"
```

## Execucao local

### CLI

```bash
context-refactor --help
context-refactor analyze /path/to/repo
context-refactor budget /path/to/repo --profile source-only
```

### Servidor MCP

```bash
python3 -m mcp_server.server
```

Ou:

```bash
context-refactor serve
```

## Configuracao local

Arquivo opcional por repositorio: `.context-refactor.json`.

Exemplo:

```json
{
  "analysis": {
    "analysis_profile": "default",
    "exclude_dirs": ["coverage", "reports"],
    "exclude_globs": ["*.map"],
    "include_categories": ["source_code"]
  }
}
```

## Skills locais para agentes

O workspace inclui skills locais em `.claude/skills/` para acelerar o uso do projeto em clientes com suporte a customizacoes de agente.

Skills disponiveis:

- `.claude/skills/mcp_refactor_workflow/SKILL.md`: orienta um agente no fluxo completo de refatoracao via MCP, incluindo preflight com `context_budget`, escolha entre analise completa e heuristicas, geracao de plano e validacao de resultados.
- `.claude/skills/mcp_refactor_tuning/SKILL.md`: orienta o ajuste fino de parametros como `analysis_profile`, `dependency_mode`, filtros, `llm_context_size`, `safety_margin` e `top_n`.

Uso recomendado:

- use a skill de workflow quando a duvida principal for qual tool MCP chamar e em que sequencia
- use a skill de tuning quando o fluxo ja estiver definido, mas ainda houver ruido, custo alto ou cobertura insuficiente

Essas skills nao alteram o runtime do servidor. Elas documentam e padronizam como um agente deve conduzir a analise sobre as tools publicas do projeto.

## Extras e empacotamento

- script CLI: `context-refactor = cli.main:main`
- extras: `dev`, `mcp`
- build backend: `setuptools`

## Variaveis de ambiente uteis

- `PYTHONUNBUFFERED=1` em hosts MCP por stdio

## Comandos uteis

```bash
make install
make install-dev
make test
make test-cov
make lint
make format
make type-check
make ci
```

## Observacoes de desenvolvimento

- `cli.main` e apenas o entrypoint publico
- a implementacao da CLI fica em `cli/app.py`, `cli/commands/*` e helpers
- a superficie MCP publica fica em `mcp_server/tools.py`
- a logica do core deve evoluir em modulos especializados, nao nas fachadas

