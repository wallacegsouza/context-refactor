# Setup de Desenvolvimento

## Pre-requisitos

- Python 3.11+
- pip atualizado
- ambiente virtual recomendado

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,mcp]"
```

## Execucao Local

### CLI

```bash
context-refactor --help
context-refactor analyze /path/to/repo
```

### Servidor MCP

```bash
python3 -m mcp_server.server
# ou
context-refactor serve
```

## Configuracao

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

## Variaveis de Ambiente

- `PYTHONUNBUFFERED=1` recomendado em hosts MCP via stdio.

## Segredos

Nao ha segredos obrigatorios no projeto atual (sem auth flows internos).

## Comandos Uteis

```bash
make install-dev
make test
make test-cov
make lint
make format
make type-check
make ci
```

## Build e Distribuicao

Projeto empacotado via setuptools (`pyproject.toml`).

- script CLI: `context-refactor = cli.main:main`
- extras: `dev`, `mcp`
