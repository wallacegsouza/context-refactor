## Evolução do Token Report com peso de dependências para análises e heurísticas do MCP

Crie um **plano de implementação completo, detalhado e faseado** para evoluir o sistema de **token report** do projeto, de forma que ele passe a considerar também a **quantidade de dependências externas associadas a cada elemento refatorável do código** como parte do cálculo de complexidade e priorização de refatoração.

O objetivo dessa melhoria é fazer com que o token report não considere apenas o **token size bruto** de cada elemento analisado, mas também um **fator multiplicador baseado em dependências**, permitindo uma visão mais realista do custo de leitura, entendimento, alteração e refatoração do código.

Essa nova informação deve ser incorporada às **próximas análises e heurísticas do MCP**, passando a influenciar a avaliação de prioridade, risco e estratégia de refatoração.

---

## Contexto da melhoria

Hoje o token report mede principalmente o tamanho em tokens dos arquivos ou elementos do projeto.
A nova proposta é enriquecer essa análise incluindo o **grau de dependência externa** de cada elemento analisado.

A contagem de dependências deve considerar, de forma configurável:

* dependências de **primeiro nível**
* dependências transitivas de níveis superiores
* profundidade máxima configurável
* diferentes tipos de elementos analisáveis, como:

  * arquivo
  * classe
  * método
  * função
  * script

A ideia é usar essa informação como um **fator multiplicador do token size**, produzindo uma métrica mais representativa da dificuldade real de refatoração.

---

## Objetivo da resposta

Produza um **plano de implementação completo** para essa melhoria, cobrindo:

* arquitetura da solução
* estratégia de análise de dependências
* alterações no token report
* impacto nas heurísticas do MCP
* configuração
* persistência e formato de saída
* qualidade
* testes
* compatibilidade com análises existentes
* rollout da mudança

A resposta deve ser suficientemente detalhada para orientar a implementação real da funcionalidade.

---

## Instruções obrigatórias para a resposta

### 1. Definição do problema e dos objetivos

Explique claramente:

* qual limitação existe hoje no token report
* por que o token size isolado é insuficiente
* por que dependências externas influenciam a complexidade de refatoração
* quais ganhos são esperados ao incorporar esse fator
* como isso melhora a qualidade das análises do MCP

---

### 2. Definição conceitual da nova métrica

Defina com precisão:

* o que será considerado uma **dependência externa**
* o que diferencia dependência de primeiro nível e níveis transitivos
* como a profundidade configurável deve funcionar
* quais tipos de relação devem entrar na conta:

  * imports
  * chamadas entre módulos
  * herança
  * composição
  * uso de tipos
  * decorators
  * dependências implícitas ou apenas explícitas
* quais relações devem ser ignoradas
* como tratar ciclos de dependência

Também defina se a métrica será aplicada em nível de:

* arquivo
* classe
* método/função
* script
* ou todos os níveis ao mesmo tempo

---

### 3. Estratégia de análise de dependências

Descreva como implementar a descoberta e contagem de dependências, incluindo:

* parsing estático
* análise por AST
* análise por linguagem/tecnologia
* fallback para linguagens menos estruturadas
* tratamento de imports relativos e absolutos
* resolução de aliases
* tratamento de módulos internos vs externos
* estratégia para limitar profundidade
* prevenção de loops infinitos em grafos cíclicos

Explique também:

* como identificar o grafo de dependências
* como calcular dependências por profundidade
* como associar dependências a elementos menores do que o arquivo, como classes e métodos

---

### 4. Modelo de cálculo da nova pontuação

Proponha uma fórmula ou conjunto de fórmulas para calcular a nova métrica.

A resposta deve detalhar:

* como combinar token size com número de dependências
* como ponderar dependências por profundidade
* se dependências de nível 1 devem pesar mais do que de nível 2+
* como evitar distorções por fan-out muito grande
* como normalizar a pontuação
* como gerar uma métrica final útil para ranqueamento de refatoração

Inclua pelo menos:

* uma fórmula base
* uma ou mais alternativas
* recomendação da abordagem principal
* exemplos numéricos de cálculo

---

### 5. Configuração e extensibilidade

Defina quais parâmetros devem ser configuráveis, por exemplo:

* profundidade máxima da análise de dependências
* peso por nível de profundidade
* peso-base do multiplicador
* tipos de dependência considerados
* limite para cap ou saturação do multiplicador
* ativação/desativação da métrica por linguagem
* ativação/desativação por tipo de elemento
* exclusão de paths, arquivos ou módulos

Explique como essas configurações devem ser expostas:

* arquivo de configuração
* CLI
* variáveis de ambiente
* configuração do MCP

---

### 6. Alterações no token report

Descreva como o token report deve ser alterado para suportar essa nova capacidade, incluindo:

* novas etapas do pipeline de análise
* novos campos no resultado
* novos indicadores por elemento
* alteração na ordenação e priorização
* compatibilidade com relatórios antigos
* impacto no CSV, JSON ou outros formatos existentes
* necessidade de versionar o schema do output

Sugira campos como:

* `direct_dependencies_count`
* `transitive_dependencies_count`
* `dependency_depth_analyzed`
* `dependency_weight`
* `effective_token_size`
* `refactor_priority_score`

---

### 7. Impacto nas heurísticas do MCP

Explique como essa nova métrica deve refletir nas análises e heurísticas do MCP.

Detalhe:

* quais heurísticas existentes precisam ser ajustadas
* como a nova pontuação influencia a priorização de refatoração
* como afetar recomendações do Refactor Heuristics Engine
* como diferenciar elementos grandes mas isolados de elementos menores porém muito acoplados
* como usar essa métrica para sugerir estratégias diferentes de refatoração

Inclua exemplos de interpretação, como:

* arquivo grande com poucas dependências
* função pequena com alto acoplamento
* classe média com grande profundidade transitiva

---

### 8. Considerações por linguagem e tipo de artefato

Descreva como essa melhoria deve se comportar em diferentes cenários, por exemplo:

* arquivos Markdown
* arquivos de configuração
* scripts simples
* backend
* frontend
* linguagens com boa análise de AST
* linguagens ou formatos onde a análise estrutural é limitada

Explique quais artefatos devem participar da métrica e quais devem ser excluídos ou tratados de forma especial.

---

### 9. Performance e custo da análise

Avalie os impactos de performance da nova abordagem, incluindo:

* custo de analisar dependências transitivas
* cache de resultados
* reaproveitamento de grafos
* invalidação de cache
* limites para evitar explosão combinatória
* trade-off entre profundidade e custo computacional

Proponha estratégias para manter a solução eficiente em projetos grandes.

---

### 10. Qualidade e testes

Defina uma estratégia de qualidade completa para validar a nova funcionalidade, incluindo:

* testes unitários do cálculo da métrica
* testes de parsing e resolução de dependências
* testes com grafos cíclicos
* testes com profundidade configurável
* testes de regressão do token report
* testes das heurísticas atualizadas
* fixtures com projetos pequenos e médios
* comparação entre resultado esperado e resultado calculado

Inclua casos de teste importantes.

---

### 11. Compatibilidade e rollout

Explique como introduzir essa funcionalidade sem quebrar o comportamento atual, incluindo:

* rollout gradual
* feature flag
* modo compatível com comportamento antigo
* comparação entre métrica antiga e nova
* estratégia de validação antes de tornar a nova pontuação padrão
* versionamento de saída e documentação da mudança

---

### 12. Riscos e trade-offs

Liste e explique os principais riscos, como:

* falso aumento de complexidade em arquivos agregadores
* distorção da prioridade por dependências pouco relevantes
* dificuldade de resolução precisa em linguagens dinâmicas
* custo excessivo da análise transitiva
* ruído em projetos com aliases ou estrutura inconsistente
* risco de heurísticas supervalorizarem acoplamento e subvalorizarem tamanho real

Explique os trade-offs entre precisão, simplicidade e custo computacional.

---

### 13. Plano de implementação faseado

Monte um plano de implementação em fases, por exemplo:

* Fase 0: definição conceitual e critérios da métrica
* Fase 1: modelagem do grafo de dependências
* Fase 2: contagem de dependências por profundidade
* Fase 3: integração da nova métrica ao token report
* Fase 4: atualização do schema de saída
* Fase 5: ajuste das heurísticas do MCP
* Fase 6: testes, calibração e rollout

Para cada fase, detalhe:

* objetivo
* entregáveis
* dependências
* riscos
* critérios de aceite

---

### 14. Checklist final

Gere um checklist operacional em Markdown com caixas de seleção cobrindo:

* definição da métrica
* análise de dependências
* configuração
* atualização do token report
* atualização das heurísticas
* testes
* compatibilidade
* documentação
* rollout

---

## Artefatos obrigatórios na resposta

A resposta deve incluir:

1. definição clara da nova métrica
2. estratégia de análise de dependências
3. proposta de fórmula de cálculo
4. impacto esperado no token report
5. impacto esperado nas heurísticas do MCP
6. plano faseado de implementação
7. checklist final em Markdown

---

## Restrições importantes

* não responder apenas com ideias genéricas
* não entregar apenas um backlog
* não assumir que dependência sempre significa maior prioridade sem justificar
* considerar cenários com diferentes linguagens e tipos de artefato
* justificar decisões de cálculo e arquitetura
* considerar compatibilidade com análises já existentes
* pensar em implementação realista para projetos grandes

---

## Ideias adicionais para considerar

Se fizer sentido, avalie também:

* separar dependências internas e externas em métricas distintas
* distinguir fan-in e fan-out
* incluir peso diferente para dependência estrutural vs dependência incidental
* medir centralidade no grafo além da contagem simples
* usar score composto com acoplamento, profundidade e token size
* gerar visualização do grafo de dependências
* criar modo “explainability” mostrando por que um elemento recebeu determinada pontuação
* permitir calibração por linguagem ou framework
* usar percentis ao invés de valores absolutos em projetos muito grandes
