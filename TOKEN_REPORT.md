# Token Report — Documentação

Utilitário CLI para estimar a contagem de tokens de todos os arquivos de texto de um projeto. Gera relatórios em CSV, JSON e Markdown, com suporte opcional a gráficos.

## Uso Básico

```bash
# A partir da raiz do projeto
python token_report.py
```

Isso escaneia o diretório atual e gera os relatórios em `token-report/`.

## Saídas Geradas

| Arquivo | Descrição |
|---|---|
| `token-report/files.csv` | Lista de todos os arquivos com tokens, bytes e caracteres |
| `token-report/files.json` | Mesmo conteúdo em JSON, incluindo agregação por diretório |
| `token-report/summary.md` | Resumo em Markdown com tabelas dos maiores arquivos e diretórios |

## Opções Principais

| Flag | Padrão | Descrição |
|---|---|---|
| `--root` | `.` | Diretório raiz do projeto |
| `--estimator` | `bytes` | Método de estimativa: `bytes`, `chars`, `whitespace`, `heuristic` |
| `--include-ext` | várias | Extensões a incluir (ex: `.py,.ts,.md`) |
| `--exclude-dirs` | `node_modules`, `dist`, `.git`, etc. | Diretórios a ignorar |
| `--exclude-globs` | — | Padrões glob extras para exclusão (ex: `*.lock,*.min.*`) |
| `--exclude-files` | — | Arquivos específicos a excluir |
| `--extra-exclude-dirs` | — | Diretórios extras adicionados às exclusões padrão |
| `--extra-exclude-globs` | — | Globs extras adicionados às exclusões padrão |
| `--extra-exclude-files` | — | Arquivos extras adicionados às exclusões padrão |
| `--use-gitignore` | desativado | Respeitar regras do `.gitignore` |
| `--max-mb` | `5` | Tamanho máximo por arquivo (MB) |
| `--depth` | `2` | Profundidade de agregação de diretórios |
| `--top` | `25` | Quantidade de itens exibidos no terminal |
| `--chart` | desativado | Gerar gráficos PNG (requer `matplotlib`) |
| `--chart-kind` | `bar` | Tipo de gráfico: `bar` ou `pie` |
| `--no-json` | — | Não gerar saída JSON |
| `--no-md` | — | Não gerar saída Markdown |

## Estimadores de Tokens

| Estimador | Lógica |
|---|---|
| `bytes` | `ceil(bytes_utf8 / 4)` — rápido e razoável para a maioria dos LLMs |
| `chars` | `ceil(caracteres / 4)` |
| `whitespace` | Conta tokens separados por espaços em branco |
| `heuristic` | Combina bytes + splitting por `_` e camelCase (mais preciso para código) |

## Exemplos

### Escanear com gitignore e estimador heurístico

```bash
python token_report.py --use-gitignore --estimator heuristic
```

### Gerar gráficos dos top 15 itens

```bash
python token_report.py --chart --chart-top 15 --chart-kind bar
```

### Escanear apenas arquivos TypeScript e Markdown

```bash
python token_report.py --include-ext .ts,.tsx,.md
```

### Excluir arquivos de teste e lock

```bash
python token_report.py --exclude-globs "*.spec.ts,*.lock" --exclude-files "package-lock.json"
```

### Somar exclusões extras sem sobrescrever defaults

```bash
python token_report.py --extra-exclude-dirs "coverage,reports" --extra-exclude-files "*.snap"
```

### Relatório rápido sem JSON/Markdown

```bash
python token_report.py --no-json --no-md --top 10
```

## Saída no Terminal

O script imprime um resumo direto no terminal:

```
Estimator: bytes
Files: 342
Total tokens (est.): 185,420
Total bytes: 741,680

Top files by tokens (est.):
     8,234      32,936  src/components/big-form.tsx
     ...

Top directories by tokens (est.):
    42,100     120  frontend/src
     ...
```

## Requisitos

- **Python 3.11+**
- **matplotlib** (opcional, apenas para `--chart`)

```bash
pip install matplotlib  # opcional para gráficos
```

---

## Integração com ContextRefactor

### Contrato de Execução

O `token_report.py` é invocado como subprocess isolado pelo módulo `context_refactor.analyzer`. Garantias:

1. **Execução determinística** — Mesmos parâmetros = mesmos resultados
2. **JSON bem-formado** — stdout sempre contém JSON válido em arquivo de saída
3. **Timeout de 120 segundos** — Projetos maiores serão truncados com aviso
4. **Código de retorno** — 0 para sucesso, não-zero para erro

### Localização

O script é **sempre localizado relativamente ao pacote**, nunca por PATH.

Estrutura esperada:

```
context-refactor/
├── context_refactor/analyzer.py   (procura ../token_report.py)
├── token_report.py                (aqui)
└── pyproject.toml
```

Se instalado via `pip install -e .`, o script é encontrado automaticamente.

### Requisitos de Dependência

matplotlib é **opcional**. Se não instalado:
- `--chart` é silenciosamente ignorado
- Um aviso é enviado para stderr
- Programa continua normalmente

Para gráficos, instalar antes:

```bash
pip install matplotlib
```

### Limitações Conhecidas

1. **Timeout fixo de 120s** — Não configurável. Para projetos muito grandes, use `--max-mb` menor
2. **Encoding UTF-8** — Presume UTF-8/ASCII. Outros encodings são ignorados
3. **Tamanho máximo de arquivo: 5MB** — Ajuste com `--max-mb`
4. **Symlinks não seguidos por padrão** — Use `--follow-symlinks` se necessário
