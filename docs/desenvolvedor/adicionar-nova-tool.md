# Como Adicionar Nova Tool/Capability

## Objetivo

Guia seguro para extender o servidor MCP sem quebrar compatibilidade.

## Passo a Passo

1. Implementar funcao em `mcp_server/tools.py`.
2. Definir assinatura clara (tipos primitivos + defaults).
3. Registrar schema em `list_tools` em `mcp_server/server.py`.
4. Adicionar entrada no dispatcher de `call_tool`.
5. (Fallback) garantir que nome tambem exista no dispatcher JSON-RPC.
6. Criar testes unitarios/integracao para comportamento novo.
7. Atualizar docs em `docs/usuario/ferramentas.md` e `docs/integracao/contratos.md`.

## Checklist de Contrato

- nome consistente: `context_refactor.<novo_nome>`
- `project_path` quando aplicavel
- retorno JSON serializavel
- tratamento de erros compreensivel
- performance aceitavel para uso em host MCP

## Exemplo Minimo

```python
def my_new_tool(project_path: str, top_n: int = 10) -> dict[str, object]:
    return {"project_path": project_path, "top_n": top_n, "status": "ok"}
```

## Boas Praticas

- reutilize helpers de escopo (`_analysis_kwargs`) em tools existentes.
- mantenha compatibilidade de campos de retorno.
- adicione limites (`top_n`) para payload grande.
- evite depender de APIs privadas de outros modulos sem justificativa.

## Compatibilidade com Integracoes Existentes

- nao renomeie tools existentes sem deprecacao.
- nao remova campos de retorno usados por clientes.
- documente mudancas breaking no changelog e docs.
