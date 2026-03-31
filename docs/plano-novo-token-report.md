# Plano: Evolucao do Token Report com Peso de Dependencias

## Resumo Executivo

Este documento define um plano completo, detalhado e faseado para evoluir o
sistema de token report do ContextRefactor, adicionando um fator de
complexidade baseado em dependencias externas ao elemento analisado.

O objetivo e sair de uma leitura puramente volumetrica do codigo
(`token_size bruto`) para uma leitura mais proxima do custo real de
refatoracao, incorporando:

- superficie de acoplamento
- profundidade transitiva
- fan-out e fan-in
- ciclos
- confianca da analise por linguagem

O resultado esperado e uma nova metrica de `effective_token_size` e um
`refactor_priority_score` composto, usados para enriquecer relatorios,
priorizar hotspots e melhorar as heuristicas expostas via MCP.

## Estado Atual do Repositorio

Hoje o pipeline principal funciona assim:

1. `token_report.py` escaneia arquivos de texto e calcula `tokens`, `bytes` e
   `chars`.
2. `context_refactor.analyzer` invoca `token_report.py`, classifica arquivos e
   aplica filtros por categoria.
3. `refactor_engine` e `refactor_heuristics` consomem `FileTokenInfo` e
   tomam decisoes ainda fortemente baseadas em `tokens` brutos.

Ja existe um inicio de modelagem para dependencias no repositorio:

- `context_refactor/models.py` ja possui `DependencyEdge`,
  `FileDependencyInfo`, `DependencyWeightResult` e campos opcionais em
  `HeuristicResult`.
- `context_refactor/dependency_analyzer.py` ja possui um grafo de dependencias
  em nivel de arquivo e uma formula inicial para `dependency_weight`.

Porem, esse scaffold ainda nao resolve o problema completo:

- o pipeline principal ainda nao esta integrado a essa analise
- o modelo atual esta concentrado em arquivo, nao em todos os elementos
- a ordenacao de heuristicas ainda usa `tokens` brutos
- nao ha configuracao formal, schema versionado, rollout e explainability

## 1. Definicao do Problema e dos Objetivos

### Limitacao atual

O token report atual mede principalmente o tamanho bruto em tokens dos arquivos
ou elementos. Isso funciona como aproximacao de volume, mas nao mede o custo
real de entendimento e alteracao.

### Por que token size isolado e insuficiente

Um arquivo pequeno pode ser muito mais caro de refatorar do que um arquivo
grande quando:

- orquestra muitos modulos
- depende de frameworks, decorators ou tipos complexos
- participa de um ciclo
- possui alto fan-in e fan-out
- exige navegar por uma cadeia transitiva grande para qualquer mudanca segura

### Por que dependencias influenciam a complexidade

Dependencias externas ao elemento aumentam:

- custo de leitura
- custo de entendimento
- custo de navegacao contextual
- risco de regressao
- custo de teste e validacao
- necessidade de coordenacao entre componentes

### Objetivos da melhoria

- enriquecer o token report com uma metrica de complexidade baseada em
  dependencias
- diferenciar tamanho bruto de tamanho efetivo para refatoracao
- refletir acoplamento e profundidade transitiva nas heuristicas do MCP
- manter compatibilidade com o comportamento atual
- entregar um rollout gradual, mensuravel e configuravel

### Ganhos esperados para o MCP

- ranking mais realista de hotspots
- melhor distincao entre "arquivo grande" e "arquivo perigoso"
- recomendacoes mais alinhadas ao tipo de acoplamento
- melhor estrategia de refatoracao por risco e superficie de impacto

## 2. Definicao Conceitual da Nova Metrica

### Definicao de dependencia externa

Neste plano, "dependencia externa" significa dependencia fora da fronteira do
elemento analisado.

Essa definicao e ortogonal a outra classificacao importante:

- dependencia interna ao projeto: alvo resolvido dentro do repositorio
- dependencia externa ao projeto: alvo resolvido fora do repositorio, como
  pacote, framework, biblioteca ou runtime

Exemplo:

- um metodo que usa uma classe do mesmo arquivo tem dependencia externa ao
  metodo, mas nao externa ao arquivo
- uma classe que herda de outra classe do projeto tem dependencia externa a
  classe e interna ao projeto
- um arquivo que importa `fastapi` tem dependencia externa ao arquivo e externa
  ao projeto

### Dependencias de primeiro nivel e transitivas

- primeiro nivel: relacoes diretas a partir do elemento
- transitivas: relacoes alcancadas ao expandir o grafo a partir das diretas
- profundidade maxima: controla ate quantos saltos o grafo sera explorado

### Relacoes que entram na conta

Relacoes explicitamente consideradas em v1:

- imports e requires
- imports relativos e absolutos
- chamadas entre modulos quando houver resolucao estatica confiavel
- heranca
- composicao explicita
- uso de tipos
- decorators

### Dependencias implicitas

Dependencias implicitas nao devem entrar no score principal em v1, porque
geram muito ruido e pouca confianca:

- reflection
- `eval`
- imports dinamicos nao resolviveis
- strings usadas por DI containers
- convencoes de framework sem resolucao estatica

Essas dependencias podem ser registradas depois em metadados auxiliares, como
`unresolved_dynamic_dependencies_count`.

### Relacoes ignoradas

- builtins
- stdlib, por default
- referencias locais dentro do mesmo elemento
- codigo gerado e artefatos excluidos pelo escopo de analise
- templates ou formatos sem estrutura confiavel

### Tratamento de ciclos

Grafo ciclico nao deve inflar contagens por repeticao de caminho. O tratamento
recomendado e:

- detectar SCCs
- condensar SCCs em um DAG logico
- contar cada componente fortemente conectado uma unica vez por caminhada
- aplicar um `cycle_penalty` separado no score final

### Niveis de aplicacao

A metrica deve ser desenhada para todos os niveis, mas entregue em fases:

- v1 obrigatoria: `file` e `script`
- v2: `class`, `function`, `method` em linguagens com AST forte
- v3: `all`, com fallback para arquivo quando nao houver confianca suficiente

## 3. Arquitetura da Solucao

### Decisao arquitetural principal

Nao transformar `token_report.py` em um analisador estrutural completo.

`token_report.py` deve continuar como fonte de verdade do token bruto, simples,
deterministica e barata. O enriquecimento com dependencias deve acontecer em
uma segunda etapa no core do projeto.

### Arquitetura alvo

1. `token_report.py` continua gerando o report bruto.
2. `context_refactor.analyzer` passa a oferecer um pipeline enriquecido.
3. `dependency_analyzer.py` evolui para um servico de grafo e scoring.
4. `refactor_heuristics.py` passa a consumir `effective_token_size` e
   `refactor_priority_score`.
5. MCP e CLI passam a expor configuracao de dependencia e modos de rollout.

### Componentes recomendados

- `DependencyAnalysisConfig`
- `RefactorableElementKind`
- `RefactorableElementInfo`
- `ElementDependencyInfo`
- `DependencyExplainability`
- `DependencyAnalysisSummary`

### Estrategia de reuso

Ha duas opcoes:

- aproveitar `dependency_analyzer.py` como nucleo inicial e expandi-lo
- extrair um `source_index` comum para evitar parse duplicado entre
  `code_refactor.py` e o analisador de dependencias

Recomendacao:

- curto prazo: reutilizar o scaffold atual
- medio prazo: criar um indice estrutural compartilhado

## 4. Estrategia de Analise de Dependencias

### Descoberta e parsing

- Python: AST obrigatoria
- TS/JS: regex inicialmente, AST depois se o custo se justificar
- Java e Go: heuristicas de import em nivel de arquivo primeiro
- outras linguagens: `file-only` ou `low-confidence`

### Resolucao

A resolucao precisa tratar:

- imports absolutos
- imports relativos
- aliases
- reexports
- modulos internos vs externos
- `index.ts` e padroes equivalentes

### Grafo de dependencias

Dois grafos devem existir conceitualmente:

- grafo de arquivos
- grafo de elementos

O grafo de arquivos e a base de v1. O grafo de elementos e derivado, com
vinculo a:

- `file_path`
- `qualname`
- `start_line`
- `end_line`
- `element_kind`
- `tokens`

### Associacao a elementos menores

Para classes, funcoes e metodos:

- mapear imports efetivamente usados no corpo
- mapear bases, decorators e tipos
- mapear composicao e chamadas resolviveis
- herdar contexto do arquivo apenas quando a resolucao fina nao for possivel

Quando houver fallback para o contexto do arquivo, o resultado deve carregar
`analysis_confidence` menor.

### Profundidade e loops

- caminhar o grafo por BFS
- usar `visited` por origem
- interromper em `max_depth`
- trabalhar sobre SCCs condensados para ciclos
- nao expandir transitivamente para dentro de pacotes externos

### Regra importante para dependencias externas ao projeto

Dependencias externas ao projeto devem ser contadas, mas tratadas como folhas.
O sistema nao deve tentar expandir transitivamente `site-packages`,
`node_modules` ou dependencias do ambiente.

## 5. Modelo de Calculo da Nova Pontuacao

### Formula principal recomendada

```text
dep_raw(e) =
  SUM depth=1..D (
    depth_weight[depth] *
    SUM dep in unique_deps_at_depth(depth, e) (
      scope_weight[project_scope(dep)] *
      kind_weight[kind(dep)]
    )
  )

dep_score(e) = log1p(dep_raw(e))
dependency_weight(e) = min(max_multiplier, 1 + base_multiplier * dep_score(e))
effective_token_size(e) = round(raw_tokens(e) * dependency_weight(e))

risk_score(e) =
  0.65 * percentile(effective_token_size) +
  0.20 * percentile(log1p(fan_in)) +
  0.10 * cycle_penalty +
  0.05 * smell_severity

refactor_priority_score(e) = risk_score(e) * confidence_factor
```

### Justificativas

- profundidade 1 deve pesar mais do que profundidade 2+
- `log1p` ou `sqrt` evitam distorcao por fan-out gigante
- `effective_token_size` mede custo de entendimento/refatoracao
- `refactor_priority_score` mede prioridade final, ja incluindo risco
- `fan_in` entra na prioridade, nao no tamanho efetivo

### Formula alternativa simples

Boa para shadow mode e alinhada ao scaffold atual:

```text
weighted_count = SUM(depth_count * depth_decay^(depth-1))
dampened = sqrt(weighted_count)
dependency_weight = min(max_multiplier, base_weight + dampened)
effective_token_size = floor(tokens * dependency_weight)
```

### Formula alternativa por percentis

Indicada para repositorios muito grandes:

```text
refactor_priority_score =
  0.50 * percentile(tokens) +
  0.30 * percentile(dep_raw) +
  0.20 * percentile(fan_in + cycle_penalty)
```

Ela e mais robusta contra outliers, mas menos explicavel.

### Recomendacao final

- v1: implementar a formula simples e coletar comparacoes
- v2: migrar para a formula principal composta
- percentis: opcao configuravel para bases muito grandes

### Exemplos numericos

Assumindo:

- `depth_weights = [1.0, 0.55, 0.30]`
- `base_multiplier = 0.35`
- `max_multiplier = 2.5`
- `scope_weight.internal = 1.0`
- `scope_weight.external_package = 0.7`

Exemplo A, arquivo grande e isolado:

- `tokens = 2000`
- `deps diretas = 2`
- `deps transitivas = 0`
- `dep_raw = 2`
- `dep_score = log1p(2) = 1.10`
- `dependency_weight = 1 + 0.35 * 1.10 = 1.39`
- `effective_token_size = 2780`

Exemplo B, funcao pequena e muito acoplada:

- `tokens = 180`
- `deps nivel 1 = 5`
- `deps nivel 2 = 8`
- `dep_raw = 5 + 0.55 * 8 = 9.4`
- `dep_score = log1p(9.4) = 2.34`
- `dependency_weight = 1 + 0.35 * 2.34 = 1.82`
- `effective_token_size = 328`

Mesmo com poucos tokens, essa funcao pode subir no ranking se tiver alto
`fan_in`.

Exemplo C, classe media com profundidade transitiva:

- `tokens = 900`
- `deps nivel 1 = 4`
- `deps nivel 2 = 10`
- `deps nivel 3 = 6`
- `dep_raw = 4 + 5.5 + 1.8 = 11.3`
- `dep_score = log1p(11.3) = 2.51`
- `dependency_weight = 1 + 0.35 * 2.51 = 1.88`
- `effective_token_size = 1692`

## 6. Configuracao e Extensibilidade

### Parametros configuraveis

- `enabled`
- `mode = off | report_only | blended | weighted`
- `element_levels = [file, class, function, method, script]`
- `languages`
- `max_depth`
- `depth_weights`
- `base_multiplier`
- `max_multiplier`
- `saturation = log1p | sqrt | linear`
- `scope_weights`
- `kind_weights`
- `fan_in_weight`
- `cycle_penalty`
- `ignore_stdlib`
- `include_dependency_kinds`
- `exclude_paths`
- `exclude_modules`
- `exclude_packages`
- `analysis_confidence_threshold`

### Exposicao recomendada

#### Arquivo de configuracao

Adicionar um bloco `dependency_analysis` a `.context-refactor.json`:

```json
{
  "analysis": {
    "analysis_profile": "default"
  },
  "dependency_analysis": {
    "enabled": true,
    "mode": "report_only",
    "element_levels": ["file"],
    "languages": ["python", "typescript", "javascript", "java", "go"],
    "max_depth": 3,
    "depth_weights": [1.0, 0.55, 0.30],
    "base_multiplier": 0.35,
    "max_multiplier": 2.5,
    "saturation": "log1p",
    "scope_weights": {
      "project_internal": 1.0,
      "project_external": 0.7
    },
    "kind_weights": {
      "import": 1.0,
      "inheritance": 1.3,
      "composition": 1.2,
      "type_usage": 0.8,
      "decorator": 0.7,
      "call": 0.9
    },
    "ignore_stdlib": true,
    "exclude_paths": ["docs/**", "tests/**"]
  }
}
```

#### CLI

Adicionar flags aos comandos `analyze`, `smells`, `suggest` e `plan`:

- `--dependency-mode`
- `--dependency-level`
- `--dependency-max-depth`
- `--dependency-explain`

#### Variaveis de ambiente

- `CONTEXT_REFACTOR_DEP_MODE`
- `CONTEXT_REFACTOR_DEP_LEVEL`
- `CONTEXT_REFACTOR_DEP_MAX_DEPTH`

#### MCP

Expor o mesmo bloco de configuracao na entrada das tools, preferencialmente em
um objeto `dependency_analysis` para evitar proliferacao de parametros soltos.

## 7. Alteracoes no Token Report

### Pipeline proposto

1. executar `token_report.py`
2. construir `FileTokenInfo`
3. montar grafo de dependencias
4. calcular metrica de dependencia
5. enriquecer arquivos e elementos com novos campos
6. produzir ordenacoes legadas e enriquecidas

### Campos novos por elemento

- `direct_dependencies_count`
- `direct_internal_dependencies_count`
- `direct_external_dependencies_count`
- `transitive_dependencies_count`
- `dependency_depth_analyzed`
- `fan_in`
- `fan_out`
- `cycle_group_id`
- `dependency_weight`
- `effective_token_size`
- `refactor_priority_score`
- `analysis_confidence`

### Campos de explainability

- `top_dependency_contributors`
- `depth_breakdown`
- `ignored_dependencies_count`
- `unresolved_dependencies_count`
- `calculation_mode`

### Ordenacao e priorizacao

O report deve permitir duas visoes:

- ordenacao legada por `tokens`
- ordenacao enriquecida por `effective_token_size` ou
  `refactor_priority_score`

### Compatibilidade

- manter `files`, `dirs` e `totals` existentes
- adicionar novos campos de forma opcional
- evitar quebrar consumidores que esperam o formato atual

### Schema versionado

Recomenda-se introduzir:

- `report_schema_version`
- `dependency_metrics_version`
- `compatibility_mode`

### Saidas recomendadas

- `token-report/files.json` continua existindo
- `token-report/summary.md` continua existindo
- `token-report/dependency_hotspots.json`
- `token-report/dependency_hotspots.csv`
- `token-report/dependency_graph.json`

### Exemplo de output JSON

```json
{
  "report_schema_version": 2,
  "dependency_metrics_version": 1,
  "compatibility_mode": "report_only",
  "dependency_analysis": {
    "enabled": true,
    "max_depth": 3,
    "element_levels": ["file"]
  },
  "files": [
    {
      "path": "src/service.py",
      "ext": ".py",
      "tokens": 420,
      "direct_dependencies_count": 6,
      "transitive_dependencies_count": 14,
      "dependency_depth_analyzed": 3,
      "dependency_weight": 1.74,
      "effective_token_size": 731,
      "refactor_priority_score": 0.83
    }
  ]
}
```

## 8. Impacto nas Heuristicas do MCP

### O que precisa mudar

- `HeuristicsEngine` deve receber um mapa de metricas por arquivo/elemento
- `HeuristicResult` deve ser populado com os campos de dependencia quando a
  feature estiver ativa
- a ordenacao de resultados deve migrar para `refactor_priority_score` em
  `blended` ou `weighted`

### O que nao deve mudar automaticamente

Thresholds de smell estrutural, como `Large File`, `Long Method` e
`Large Class`, nao devem ser substituidos por `effective_token_size`.

Justificativa:

- tamanho estrutural continua sendo um sinal proprio
- acoplamento e um sinal complementar
- confundir os dois degrada explicabilidade

### Ajustes recomendados

- adicionar `HighCouplingRule`
- promover `HIGH_COUPLING` como smell efetivo
- enriquecer prioridades de recomendacoes existentes
- diferenciar estrategia de refatoracao por tipo de acoplamento

### Interpretacao de casos

Arquivo grande com poucas dependencias:

- alta prioridade por volume
- risco moderado
- recomendacoes centradas em `Extract Module`, `Extract Class`, `Split`

Funcao pequena com alto acoplamento:

- nao deve virar `Large Method`
- pode virar hotspot de acoplamento
- recomendacoes centradas em `Invert Dependency`, `Introduce Interface`,
  `Extract Adapter`, `Move Method`

Classe media com grande profundidade transitiva:

- prioridade sobe por superficie de impacto
- recomendacao inicial pode ser quebrar fronteiras e remover dependencias
  antes de extrair metodos

## 9. Consideracoes por Linguagem e Tipo de Artefato

### Participam da metrica

- arquivos de codigo fonte
- scripts com semantica de dependencia detectavel
- classes/funcoes/metodos em linguagens com estrutura confiavel

### Excluidos por default

- Markdown
- arquivos de configuracao
- binarios
- arquivos gerados
- artefatos auxiliares do build

### Tratamento especial

- shell scripts: suporte inicial em nivel de arquivo, baixa confianca
- TS/JS frontend: comecar por imports e reexports, evoluir depois para uso de
  simbolos
- Python backend: priorizar elemento-level cedo, pois AST e forte
- Java/Go: comecar por arquivo, depois expandir

### Regra geral

Quando a analise estrutural nao for confiavel, o sistema deve:

- recuar para `file-only`
- reduzir `confidence_factor`
- nao aplicar heuristicas agressivas baseadas nessa metrica

## 10. Performance e Custo da Analise

### Custos esperados

- parse estrutural por arquivo
- resolucao de import
- caminhada transitiva no grafo
- associacao a elementos menores

### Principais riscos de custo

- BFS por muitos nos em projetos grandes
- parse duplicado entre engine de smells e engine de dependencias
- explosao de elementos por arquivo

### Estrategias de eficiencia

- cache por arquivo usando `(path, mtime, size, config_hash)`
- cache por grafo para execucoes repetidas
- reuso do parse estrutural entre heuristicas e dependencias
- SCC condensation para reduzir caminhadas
- `max_depth` curto por default
- limite de elementos por arquivo
- limite de arestas por elemento

### Invalidao de cache

Invalidar quando mudar:

- conteudo do arquivo
- tipo de linguagem detectada
- configuracao de dependencia relevante
- escopo de analise

### Trade-off

Mais profundidade aumenta precisao, mas encarece custo. O default recomendado
e profundidade 3.

## 11. Qualidade e Testes

### Suites recomendadas

- `tests/test_dependency_analyzer.py`
- `tests/test_dependency_scoring.py`
- `tests/test_dependency_output_schema.py`
- `tests/test_refactor_heuristics_dependency.py`

### Casos obrigatorios

- import absoluto e relativo em Python
- alias e reexport em TS/JS
- heranca e decorator
- uso de tipos
- composicao simples
- ciclos pequenos e SCCs maiores
- profundidade 1, 2 e 3
- `max_depth = 0`
- arquivo sem dependencias
- arquivo com muitas dependencias diretas
- elemento pequeno mas acoplado
- arquivo grande e isolado

### Testes de regressao

Com feature desligada:

- JSON deve permanecer compativel
- ordenacao por tokens deve permanecer identica
- heuristicas atuais nao devem mudar

Com `report_only`:

- campos novos aparecem
- ranking legado continua acessivel

### Fixtures

Criar fixtures pequenos e medios:

- repo Python puro
- repo misto Python/TS
- repo com ciclos
- repo com frontend modular
- repo sintetico com alto fan-out

### Validacao

Comparar:

- resultado esperado
- resultado calculado
- ranking antigo vs ranking novo
- snapshots de explainability

## 12. Compatibilidade e Rollout

### Principios

- nao quebrar consumidores atuais
- liberar primeiro em modo observavel
- comparar novo score com o antigo antes de promover padrao

### Rollout recomendado

#### Etapa 1: shadow mode

- calcular metricas novas
- nao mudar ranking padrao
- expor `legacy_rank` e `weighted_rank`

#### Etapa 2: report only

- incluir campos novos no output
- manter heuristicas e ordenacao legadas como default

#### Etapa 3: blended

- usar `refactor_priority_score` para ranking
- manter fallback explicito para `legacy`

#### Etapa 4: default novo

- tornar `blended` o default do MCP
- preservar `legacy` por pelo menos uma release de transicao

### Versionamento

- `report_schema_version = 2`
- documentar migracao
- atualizar README, TOKEN_REPORT.md e docs MCP

## 13. Riscos e Trade-offs

### Riscos principais

- arquivos agregadores parecerem complexos demais
- dependencias pouco relevantes inflarem score
- resolucao imperfeita em linguagens dinamicas
- custo excessivo da analise transitiva
- ruido por aliases ou convencoes inconsistentes
- heuristicas passarem a supervalorizar acoplamento

### Mitigacoes

- peso menor para reexports e imports incidentais
- `log1p` ou `sqrt` para saturacao
- separacao entre `effective_token_size` e `refactor_priority_score`
- `analysis_confidence`
- modo `legacy`
- calibracao com fixtures reais

### Trade-off central

Precisao, simplicidade e custo computacional estao em tensao.

A recomendacao deste plano e:

- v1 simples, explicavel e barata
- v2 mais precisa e composta
- sempre com fallback e observabilidade

## 14. Plano de Implementacao Faseado

### Fase 0: definicao conceitual e criterios da metrica

Objetivo:

- fechar semantica, relacoes, defaults, escopo por linguagem e nivel

Entregaveis:

- ADR curta
- schema de configuracao
- defaults da formula

Dependencias:

- alinhamento funcional

Riscos:

- escopo inicial grande demais

Criterios de aceite:

- formula e relacoes aprovadas
- matriz de suporte por linguagem definida

### Fase 1: modelagem do grafo de dependencias

Objetivo:

- consolidar o grafo de arquivos e a deteccao de ciclos

Entregaveis:

- resolucao de imports
- SCCs
- contagem por profundidade

Dependencias:

- Fase 0

Riscos:

- resolucao inconsistente entre linguagens

Criterios de aceite:

- testes de parse, resolucao e ciclo passando

### Fase 2: contagem de dependencias por profundidade e elemento

Objetivo:

- introduzir a associacao a `file`, `class`, `function`, `method`, `script`

Entregaveis:

- `RefactorableElementInfo`
- associacao de dependencias a elementos menores
- `analysis_confidence`

Dependencias:

- Fase 1

Riscos:

- parse duplicado e custo alto

Criterios de aceite:

- Python em element-level funcionando
- outras linguagens com fallback explicito

### Fase 3: integracao da nova metrica ao token report

Objetivo:

- calcular `effective_token_size` e `refactor_priority_score`

Entregaveis:

- scorer configuravel
- shadow mode
- explainability minima

Dependencias:

- Fase 2

Riscos:

- score instavel e pouco intuitivo

Criterios de aceite:

- exemplos numericos reproduziveis
- snapshots coerentes

### Fase 4: atualizacao do schema de saida

Objetivo:

- enriquecer JSON, CSV e Markdown sem quebrar legado

Entregaveis:

- schema v2
- arquivos `dependency_hotspots.*`
- `dependency_graph.json`

Dependencias:

- Fase 3

Riscos:

- consumidores quebrarem com campos novos

Criterios de aceite:

- modo legado identico ao atual
- modo enriquecido validado por testes

### Fase 5: ajuste das heuristicas do MCP

Objetivo:

- refletir a nova metrica no ranking e nas recomendacoes

Entregaveis:

- `HighCouplingRule`
- ordenacao blended
- recomendacoes diferenciadas por perfil de acoplamento

Dependencias:

- Fase 4

Riscos:

- priorizacao artificial

Criterios de aceite:

- ranking em heuristicas validado
- MCP retornando scores coerentes

### Fase 6: testes, calibracao e rollout

Objetivo:

- estabilizar pesos e liberar gradualmente

Entregaveis:

- fixtures finais
- comparacao `legacy` vs `blended`
- documentacao e guia de migracao

Dependencias:

- Fases 0 a 5

Riscos:

- defaults mal calibrados

Criterios de aceite:

- calibracao aprovada
- docs publicadas
- rollout seguro

## Checklist Operacional

- [ ] Definir `DependencyAnalysisConfig`
- [ ] Definir semantica de dependencia externa ao elemento
- [ ] Separar dependencia interna ao projeto e externa ao projeto
- [ ] Definir matriz de suporte por linguagem e por tipo de elemento
- [ ] Consolidar grafo de arquivos com SCC e profundidade configuravel
- [ ] Criar modelo de elementos refatoraveis
- [ ] Associar dependencias a classes, funcoes e metodos onde houver confianca
- [ ] Implementar formula de `dependency_weight`
- [ ] Implementar `effective_token_size`
- [ ] Implementar `refactor_priority_score`
- [ ] Adicionar `analysis_confidence`
- [ ] Adicionar explainability minima
- [ ] Expor configuracao em `.context-refactor.json`
- [ ] Expor configuracao na CLI
- [ ] Expor configuracao nas tools MCP
- [ ] Versionar o schema de saida
- [ ] Enriquecer JSON, CSV e Markdown
- [ ] Criar `dependency_hotspots.json`
- [ ] Criar `dependency_hotspots.csv`
- [ ] Criar `dependency_graph.json`
- [ ] Atualizar `HeuristicsEngine`
- [ ] Adicionar `HighCouplingRule`
- [ ] Manter `legacy_mode`
- [ ] Implementar `shadow mode`
- [ ] Cobrir parse, resolucao, ciclo e profundidade com testes
- [ ] Cobrir regressao de output com a feature desligada
- [ ] Cobrir heuristicas em modo blended
- [ ] Calibrar pesos com fixtures reais
- [ ] Atualizar README
- [ ] Atualizar `TOKEN_REPORT.md`
- [ ] Atualizar documentacao MCP

## Recomendacao Final

A implementacao deve comecar em nivel de arquivo, com score simples,
explicavel e barato, usando `report_only` como modo padrao inicial.

So depois de validar ranking, custo e qualidade da resolucao vale promover:

- element-level amplo
- score composto com fan-in e ciclo
- `blended` como default do MCP

Esse caminho reduz risco, preserva compatibilidade e usa bem o scaffold de
dependencias que o repositorio ja comecou a introduzir.
