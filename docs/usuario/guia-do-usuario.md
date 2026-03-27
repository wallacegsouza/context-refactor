# Guia do Usuario

## O que Este MCP Faz

O ContextRefactor avalia um projeto e responde perguntas praticas:

- "Meu repositorio cabe no contexto do modelo?"
- "Quais arquivos/trechos causam maior impacto?"
- "Que plano de refatoracao reduz tokens com melhor custo-beneficio?"

This MCP answers practical size/refactoring questions for LLM context management.

## Fluxo Recomendado de Uso

1. Rode budget para saber se cabe.
2. Rode candidates/smells para localizar causas.
3. Rode plan/suggest para priorizar acoes.
4. Reexecute e compare resultados.

## Comandos CLI Mais Usados

```bash
context-refactor budget /path/to/repo --context-size 128000 --safety-margin 0.8
context-refactor candidates /path/to/repo --top 30
context-refactor plan /path/to/repo --context-size 128000
```

## Perfis de Analise

- `default`: reduz ruido comum.
- `full`: inclui tudo.
- `source-only`: foco em codigo-fonte.
- `docs`: foco em markdown.

## Entradas Esperadas

- caminho valido para raiz do projeto
- parametros numericos coerentes (`context-size`, `safety-margin`)
- categorias validas quando usar filtros

## Saidas Esperadas

- resumo de tokens, budget e overflow
- recomendacoes priorizadas
- plano com passos, tecnicas e reducao estimada

## Comportamentos Importantes

- configuracoes de escopo sao combinadas de perfil + arquivo config + argumentos.
- se o SDK MCP nao estiver instalado, existe fallback JSON-RPC.
- algumas saidas sao truncadas por `top_n`.

## Erros Comuns

- path invalido: diretoria inexistente.
- categoria invalida: valor fora da lista permitida.
- erro no `token_report.py`: analise interrompida.

## Interpretacao de Resultados

- `fits_context=true`: contexto atual comporta o escopo analisado.
- `overflow_tokens>0`: excedente a ser reduzido.
- `priority`: ordem de urgencia da recomendacao.
- `estimated_token_reduction`: estimativa heuristica, nao garantia absoluta.

## Proximo Passo

- Consulte [Ferramentas MCP](./ferramentas.md) para contratos por tool.
- Consulte [Exemplos de Uso](./exemplos-de-uso.md) para payloads e respostas resumidas.
