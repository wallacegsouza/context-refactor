# Qualidade, Testes e Validacao

## Suite de Testes Atual

- `tests/test_analyzer.py`
- `tests/test_refactor_heuristics.py`
- `tests/test_refactor_rules.py`

Test coverage focuses on analyzer behavior, heuristics engine, and rule correctness.

## Estrategia Atual

- unit/integration style para core de analise
- validacao de perfis, categorias e limites
- validacao de plano de refatoracao e deduplicacao de regras

## Como Executar

```bash
pytest tests/ -v
pytest tests/ -v --tb=short --cov=context_refactor --cov=mcp_server --cov=cli
```

## Qualidade Estatica

```bash
ruff check context_refactor tests cli mcp_server token_report.py
ruff format --check context_refactor tests cli mcp_server token_report.py
mypy context_refactor mcp_server cli --ignore-missing-imports
```

## Validacao de Contratos MCP

Minimo recomendado para novas features:

1. Testar listagem da nova tool.
2. Testar chamada com argumentos validos.
3. Testar erro de argumento invalido.
4. Testar serializacao da resposta.

## Mocks/Stubs

- Isolar chamadas a subprocess quando testar `analyzer` em cenarios de falha.
- Criar fixtures de arquivo para casos de smells (long method, large class etc.).

## Criterios Minimos para Merge

- testes relevantes para comportamento novo
- sem regressao em CI (`make ci`)
- docs de usuario/integracao/desenvolvedor atualizadas
