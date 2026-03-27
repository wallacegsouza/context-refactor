# Manutencao e Evolucao

## Areas Sensiveis

- Integracao com `token_report.py` (contrato de saida e disponibilidade).
- Registro/dispatch de tools MCP (`server.py`).
- Serializacao dos modelos usados por CLI e MCP.

## Pontos de Acoplamento

- tools dependem diretamente de funcoes core (`analyzer`, `planner`, heuristics).
- thresholds e criterios podem existir em mais de um ponto logico.
- comportamento de fallback precisa manter paridade funcional.

## Riscos Conhecidos

- divergencia entre documentacao historica e tools realmente expostas.
- ausencia de auth/rate-limit pode exigir controles no host.
- resposta grande pode impactar clientes sem paginacao.

## Debito Tecnico (Observavel)

- falta de camada formal de validacao de schema no servidor.
- falta de recursos MCP avancados (resources/prompts/templates/streams/events/auth).
- necessidade de padronizar codigos/formatos de erro para consumidores.

## Boas Praticas para Alteracoes Futuras

1. Altere contratos de forma retrocompativel sempre que possivel.
2. Se houver breaking change, documente deprecacao e migracao.
3. Atualize teste + docs na mesma PR.
4. Mantenha exemplos de integracao sincronizados com o codigo.

## Como Manter Compatibilidade

- preserve nomes de tools publicas.
- preserve campos de retorno existentes.
- adicione novos campos de forma aditiva.
- evite mudar defaults sem justificativa/documentacao.

## Roadmap Tecnico Sugerido

- adicionar observabilidade estruturada.
- introduzir validacao de entrada/saida por schema.
- avaliar suporte gradual a capabilities MCP adicionais.
