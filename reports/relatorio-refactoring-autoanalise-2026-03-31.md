# Relatorio de Refactoring - Autoanalise do ContextRefactor

Data: 2026-03-31

## Como o teste foi executado

Analise executada no proprio repositorio usando a implementacao nova com peso de dependencias:

```bash
poetry run context-refactor analyze . \
  --json \
  --profile default \
  --exclude-dirs reports \
  --dependency-mode blended \
  --dependency-max-depth 3

poetry run context-refactor suggest . \
  --json \
  --profile default \
  --exclude-dirs reports \
  --dependency-mode blended \
  --dependency-max-depth 3
```

Parametros principais:

- `analysis_profile=default`
- `exclude_dirs=["reports"]`
- `dependency_mode=blended`
- `dependency_max_depth=3`
- `llm_context_size=128000`
- `safety_margin=0.80`

## Resumo executivo

- Arquivos analisados: `56`
- Tokens brutos: `79,323`
- Orcamento util de contexto: `102,400`
- Resultado bruto: `cabe no contexto`
- Effective tokens com dependencias: `229,592`
- Signal score: `98.18/100`

Leitura pratica:

- O repositorio cabe no contexto quando olhamos apenas para volume bruto.
- No modo `blended`, o custo efetivo sobe para quase `2.9x` o tamanho bruto.
- O principal problema atual nao e volume puro; e concentracao de responsabilidades somada a alto acoplamento nas camadas de orquestracao.

## Smells consolidados

- `High Coupling`: `23` arquivos
- `Long Method`: `6`
- `Long Parameter List`: `6`
- `God File`: `4`
- `Duplicate Code`: `3`

## Hotspots prioritarios

| Arquivo | Tokens | Effective | Score | Principais sinais |
| --- | ---: | ---: | ---: | --- |
| `cli/main.py` | 8,743 | 39,092 | 1.0000 | God File, High Coupling, Duplicate Code |
| `context_refactor/dependency_analyzer.py` | 7,369 | 26,300 | 0.6821 | God File, Long Method, High Coupling |
| `context_refactor/analyzer.py` | 6,802 | 25,553 | 0.6724 | God File, Long Method, High Coupling |
| `mcp_server/tools.py` | 5,325 | 22,497 | 0.5942 | God File, High Coupling, Duplicate Code |
| `context_refactor/models.py` | 3,908 | 11,219 | 0.4370 | High Coupling por alto fan-in |
| `token_report.py` | 3,438 | 12,978 | 0.3320 | High Coupling, Long Method |
| `context_refactor/refactor_heuristics.py` | 2,831 | 11,371 | 0.3096 | High Coupling |

Hotspot de documentacao relevante:

- `docs/plano-novo-token-report.md`: `6,512` tokens, recomendado para `Split Document` em `19` topicos.

## Plano automatico gerado

O plano retornado pela ferramenta tem `5` etapas, com reducao estimada de `28,805` tokens brutos e projecao de `50,518` tokens apos refactor.

1. `Split Document`
   Arquivos alvo: `CONTRIBUTING.md`, `FIXES_SUMMARY.md`, `README.md`, `TOKEN_REPORT.md`, `TUNING_GUIDE.md`, `docs/plano-novo-token-report.md`, `docs/usuario/ferramentas.md`
   Reducao estimada: `2,372`

2. `Extract Module`
   Arquivos alvo: `cli/main.py`, `context_refactor/analyzer.py`, `context_refactor/dependency_analyzer.py`, `mcp_server/tools.py`
   Reducao estimada: `8,469`

3. `Invert Dependency`
   Arquivos alvo: camada de CLI, analyzer, MCP tools, varios modulos core e testes
   Reducao estimada: `16,472`

4. `Extract Method`
   Arquivos alvo: `cli/main.py`, `context_refactor/analyzer.py`, `context_refactor/dependency_analyzer.py`, `context_refactor/refactor_planner.py`, `mcp_server/tools.py`, `token_report.py`
   Reducao estimada: `1,492`

5. `Extract Variable`
   Arquivos alvo: listas de parametros longas em CLI, analyzer, dependency analyzer, high coupling rule, MCP tools e `token_report.py`
   Reducao estimada: `0`

## Interpretacao tecnica

### 1. `cli/main.py` e o maior alvo imediato

O arquivo concentra comandos, rendering e montagem de opcoes. Ele aparece ao mesmo tempo como:

- maior arquivo de codigo do repositorio;
- maior effective token size;
- maior score de prioridade;
- ponto com duplicacao e alto acoplamento.

Direcao recomendada:

- extrair comandos para modulos separados;
- centralizar parsing de opcoes compartilhadas;
- reduzir repeticao de tabelas e paineis.

### 2. `context_refactor/dependency_analyzer.py` precisa ser quebrado por responsabilidade

O problema aqui nao e apenas tamanho. O arquivo combina:

- resolucao de caminhos/modulos;
- construcao de grafo;
- calculo de pesos;
- normalizacao e ranking.

Direcao recomendada:

- separar `resolver`, `graph`, `weights` e `ranking`;
- reduzir o tamanho de `compute_dependency_weights`;
- deixar as regras de score mais localizadas e testaveis.

### 3. `context_refactor/analyzer.py` e `mcp_server/tools.py` estao pagando o custo de orquestracao excessiva

Ambos parecem modulos que cresceram por acumulacao de fluxo e configuracao.

Direcao recomendada:

- mover resolucao de config/escopo/dependency merge para helpers dedicados;
- separar tools MCP por familia: budget, analysis, planning e heuristics;
- reaproveitar builders compartilhados para argumentos e payloads.

### 4. Nem todo `High Coupling` tem a mesma prioridade

Dois casos pedem leitura mais cuidadosa:

- `context_refactor/models.py` tem score alto, mas `fan_in=16` indica modulo central compartilhado. Eu nao trataria esse caso como primeira frente de refactor.
- arquivos de teste aparecem com `High Coupling`, mas isso reflete integracao ampla. Tambem nao sao prioridade antes da modularizacao dos arquivos de producao.

## Ordem pratica recomendada

1. Quebrar `cli/main.py` em modulos de comando.
2. Separar `mcp_server/tools.py` em grupos menores e remover duplicacao de builders.
3. Extrair de `context_refactor/analyzer.py` a parte de configuracao e merge de metricas.
4. Fatiar `context_refactor/dependency_analyzer.py` em submodulos menores.
5. Rodar a autoanalise novamente para medir a queda de `effective_token_size` nos hotspots.

## Limitacoes observadas nesta rodada

- O plano automatico ainda projeta reducao sobre tokens brutos, nao sobre `effective_token_size`.
- Isso significa que a ordem do ataque esta util, mas o ganho estrutural real do modo `blended` ainda precisa ser validado em uma segunda rodada apos modularizacao.

## Conclusao

O teste pratico confirmou que a nova implementacao adiciona sinal util. Sem dependencia, o repositorio parece confortavel dentro do contexto. Com dependencia, a ferramenta mostra que a camada de orquestracao ainda concentra risco estrutural demais.

Se eu fosse atacar isso agora, comecaria por `cli/main.py`, `mcp_server/tools.py`, `context_refactor/analyzer.py` e `context_refactor/dependency_analyzer.py`. Esses quatro arquivos concentram o maior retorno esperado por refactor.
