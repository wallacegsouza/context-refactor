# Qualidade, Testes e Validacao

## Suite de testes atual

- `tests/test_analyzer.py`
- `tests/test_cli_main.py`
- `tests/test_dependency_analyzer.py`
- `tests/test_mcp_tools.py`
- `tests/test_refactor_engine.py`
- `tests/test_refactor_heuristics.py`
- `tests/test_refactor_rules.py`
- `tests/test_token_report.py`

## Cobertura atual por area

- pipeline de analise e escopo
- CLI e roteamento de argumentos
- analise de dependencias
- wrappers MCP e contratos de resposta
- engine legacy de candidatos
- Heuristics Engine e regras plugaveis
- `token_report.py`

## Como executar

Suite completa:

```bash
pytest tests/ -v
```

Com cobertura:

```bash
pytest tests/ -v --cov=context_refactor --cov=mcp_server --cov=cli --cov-report=term-missing
```

Arquivos especificos:

```bash
pytest tests/test_mcp_tools.py -v
pytest tests/test_cli_main.py -v
pytest tests/test_dependency_analyzer.py -v
```

## Qualidade estatica

```bash
ruff check context_refactor tests cli mcp_server token_report.py
ruff format --check context_refactor tests cli mcp_server token_report.py
mypy context_refactor mcp_server cli --ignore-missing-imports
```

Atalhos via `make`:

```bash
make test
make test-cov
make lint
make format
make type-check
make ci
```

## Validacao de contratos MCP

Minimo recomendado para qualquer mudanca publica:

1. testar listagem da tool em `list_tools`
2. testar chamada com argumentos validos
3. testar erro de argumento invalido
4. testar serializacao da resposta

## Criterios minimos para merge

- testes relevantes para o comportamento novo
- sem regressao em `make ci`
- docs atualizadas quando a superficie publica mudar
- compatibilidade preservada nas fachadas publicas

