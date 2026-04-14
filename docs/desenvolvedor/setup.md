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

