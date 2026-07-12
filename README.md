# Mineração de Regras de Associação

Projeto acadêmico que compara regras de associação em dois bancos do Spider 2.0: resultados históricos da Fórmula 1 (`f1.duckdb`) e avaliações MovieLens (`movie_recomm.duckdb`). A F1 usa Apriori em transações formadas por grid, resultado e equipe; filmes usam FP-Growth com gêneros, período, avaliação e popularidade.

## Estrutura

- `BasesDeDados/`: bancos DuckDB originais, usados somente para leitura.
- `codigos/f1/`: compreensão, preparação, EDA, transações, três experimentos e validação.
- `codigos/movie_recomm/`: compreensão, preparação, EDA, FP-Growth e validação.
- `resultados/`: gráficos, itemsets, regras por experimento e `regras_finais_trabalho.csv`.
- `Relatorio.pdf`: relatório acadêmico final.
- `executar_projeto.py`: executor e verificador de todas as etapas.

## Ambiente e execução

Recomenda-se Python 3.11 ou 3.12. No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python executar_projeto.py
```

Todos os scripts resolvem caminhos com `pathlib` e podem ser iniciados da raiz. As pastas de saída são criadas automaticamente.

## Métodos e arquivos gerados

Na F1, `03_preparacao_transacoes_f1.py` centraliza as discretizações e produz os períodos 1950–2024, 1950–1959 e 2014–2024. Os scripts `04_*` aplicam Apriori com suporte 0,02 e confiança 0,60; `05_validacao_regras_f1.py` exige lift de pelo menos 1,10 e seleciona 15 regras.

Nos filmes, a preparação exige cinco avaliações por título. O FP-Growth usa suporte 0,02, confiança 0,55, itemsets de até quatro itens, antecedente de até dois itens e consequente unitário. A validação exige lift 1,30 e seleciona 30 regras.

Ao final, confira que `resultados/regras_finais_trabalho.csv` possui 45 linhas, 15 da F1 e 30 de filmes, sem campos vazios nas perguntas, respostas ou análises. Regras de associação descrevem coocorrências; associação não significa causalidade.
