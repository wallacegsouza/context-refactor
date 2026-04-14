# Token Report

Utilitario CLI para estimar a contagem de tokens de todos os arquivos de texto
de um projeto. Gera relatorios em CSV, JSON e Markdown, com suporte opcional a
graficos.

## Uso basico

```bash
python3 token_report.py
```

O comando escaneia o diretorio atual e gera os arquivos em `token-report/`.

## Saidas geradas

| Arquivo | Descricao |
|---|---|
| `token-report/files.csv` | Lista de arquivos com tokens, bytes e caracteres |
| `token-report/files.json` | Mesmo conteudo em JSON, incluindo agregacoes |
| `token-report/summary.md` | Resumo em Markdown com top arquivos e diretorios |

## Opcoes principais

| Flag | Padrao | Descricao |
|---|---|---|
| `--root` | `.` | Diretorio raiz do projeto |
| `--estimator` | `bytes` | `bytes`, `chars`, `whitespace` ou `heuristic` |
| `--include-ext` | varias | Extensoes a incluir |
| `--exclude-dirs` | padrao interno | Diretorios ignorados |
| `--exclude-globs` | vazio | Globs extras de exclusao |
| `--exclude-files` | vazio | Arquivos ou padroes especificos |
| `--extra-exclude-dirs` | vazio | Diretorios extras somados ao padrao |
| `--extra-exclude-globs` | vazio | Globs extras somados ao padrao |
| `--extra-exclude-files` | vazio | Arquivos extras somados ao padrao |
| `--use-gitignore` | desativado | Respeitar regras do `.gitignore` |
| `--max-mb` | `5` | Tamanho maximo por arquivo em MB |
| `--depth` | `2` | Profundidade de agregacao de diretorios |
| `--top` | `25` | Quantidade de itens exibidos no terminal |
| `--chart` | desativado | Gerar graficos PNG |
| `--chart-kind` | `bar` | `bar` ou `pie` |
| `--no-json` | desativado | Nao gerar JSON |
| `--no-md` | desativado | Nao gerar Markdown |

## Estimadores

| Estimador | Logica |
|---|---|
| `bytes` | `ceil(bytes_utf8 / 4)` |
| `chars` | `ceil(caracteres / 4)` |
| `whitespace` | Conta tokens separados por espaco |
| `heuristic` | Combina bytes e heuristicas para codigo |

## Exemplos

Com `.gitignore` e estimador heuristico:

```bash
python3 token_report.py --use-gitignore --estimator heuristic
```

Somente arquivos TypeScript e Markdown:

```bash
python3 token_report.py --include-ext .ts,.tsx,.md
```

Exclusoes extras sem sobrescrever defaults:

```bash
python3 token_report.py --extra-exclude-dirs "coverage,reports" --extra-exclude-files "*.snap"
```

## Integracao com ContextRefactor

`token_report.py` continua sendo a fonte de verdade da contagem bruta de
tokens. O restante do projeto consome esse output e enriquece a analise com:

- classificacao por categoria de arquivo
- filtros por perfil e configuracao local
- budget de contexto
- metadados de dependencia
- recomendacoes legacy e heuristicas

### Como o core executa o script

- a chamada publica passa por `context_refactor.analyzer`
- a execucao do subprocess fica em `context_refactor/analyzer_runner.py`
- o script e localizado relativamente ao pacote, nao por `PATH`
- a chamada usa `python3`, `--use-gitignore` e arquivos temporarios para JSON,
  CSV e Markdown

### Contrato esperado pelo core

- execucao deterministica para o mesmo conjunto de entradas
- arquivo JSON valido em disco ao final da execucao
- codigo de retorno `0` em sucesso
- timeout de `120` segundos no subprocess

### Localizacao do script

O core resolve `token_report.py` a partir do diretorio do pacote
`context_refactor`. Isso preserva funcionamento tanto em desenvolvimento quanto
em instalacao editavel.

### Dependencias opcionais

`matplotlib` e opcional. Se nao estiver instalado:

- o restante do script continua funcionando
- apenas a geracao de graficos fica indisponivel

## Limitacoes conhecidas

- timeout fixo de `120s`
- leitura assumindo UTF-8/ASCII para arquivos de texto
- tamanho maximo por arquivo controlado por `--max-mb`
- symlinks nao sao seguidos por padrao

Para o restante do sistema, consulte [README.md](README.md) e
[docs/INDEX.md](docs/INDEX.md).

