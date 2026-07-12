# Pipeline do banco `movie_recomm.duckdb`

Este pacote continua o projeto a partir da Etapa 2. A análise utiliza as tabelas `movielens_movies` e `movielens_ratings`.

## Estratégia adotada

Cada transação representa um filme e contém:

- um item para cada gênero;
- período de lançamento;
- faixa da avaliação média;
- faixa de popularidade, medida pela quantidade de avaliações.

São mantidos filmes com pelo menos cinco avaliações e gênero conhecido. O filtro reduz a instabilidade de médias calculadas a partir de uma ou duas notas.

## Instalação

```bash
python -m pip install -r requirements.txt
```

## Execução no Windows PowerShell

Execute os comandos dentro da pasta que contém os scripts. Ajuste o caminho do banco quando necessário.

```powershell
python .\01_preparacao_dados_filmes.py `
  --db "..\BasesDeDados\movie_recomm.duckdb" `
  --saida "..\saida_movie_recomm"

python .\02_eda_filmes.py `
  --db "..\BasesDeDados\movie_recomm.duckdb" `
  --dados "..\saida_movie_recomm\filmes_preparados.csv" `
  --saida "..\saida_movie_recomm\eda"

python .\03_regras_associacao_filmes.py `
  --transacoes "..\saida_movie_recomm\transacoes_filmes.csv" `
  --saida "..\saida_movie_recomm\regras"
```

## Arquivos gerados

- `filmes_preparados.csv`: dados agregados, limpos e discretizados;
- `transacoes_filmes.csv`: uma transação por filme;
- `relatorio_qualidade_dados.csv`: nulos, duplicatas e integridade;
- `eda/`: gráficos, estatísticas, frequências, correlação e outliers;
- `regras/itemsets_frequentes.csv`;
- `regras/regras_associacao_completas.csv`;
- `regras/regras_nao_redundantes.csv`;
- `regras/top_30_perguntas_respostas.csv`;
- `regras/parametros_e_resumo.csv`;
- `regras/texto_resultados_regras.md`.

## Parâmetros utilizados

- algoritmo: FP-Growth;
- suporte mínimo: 0,02;
- confiança mínima: 0,55;
- lift mínimo: 1,10;
- tamanho máximo dos itemsets: quatro;
- antecedente com no máximo dois itens;
- consequente com exatamente um item.

Com 3.649 transações, suporte de 0,02 exige aproximadamente 73 filmes. O filtro de antecedente e consequente torna as regras mais fáceis de interpretar. Regras com dois itens no antecedente são removidas quando aumentam a confiança em menos de cinco pontos percentuais em relação a uma regra mais simples com o mesmo consequente.

## Textos para o relatório

- `TEXTO_RELATORIO_MOVIE_RECOMM.md`: redação das Etapas 2 a 6;
- `COMPARACAO_F1_MOVIE_RECOMM.md`: comparação exigida entre os dois bancos do Spider 2.0;
- `Etapas - Banco filmes - atualizado.txt`: checklist atualizado e pendências finais.
