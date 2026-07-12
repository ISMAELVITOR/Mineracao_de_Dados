# Mineração de Regras de Associação

Projeto acadêmico desenvolvido para a disciplina de Mineração de Dados, com o objetivo de comparar regras de associação extraídas de dois bancos da coleção Spider 2.0:

- `f1.duckdb`: resultados históricos do Campeonato Mundial de Fórmula 1;
- `movie_recomm.duckdb`: filmes e avaliações de usuários do conjunto MovieLens.

Na base F1, foi utilizado o algoritmo Apriori sobre transações compostas pela posição de largada discretizada, pelo resultado obtido na corrida e pela equipe do piloto.

Na base de filmes, foi utilizado o algoritmo FP-Growth sobre transações compostas por gêneros, período de lançamento, faixa de avaliação e faixa de popularidade.

## Execução

Python 3.11 ou 3.12.

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python executar_projeto.py