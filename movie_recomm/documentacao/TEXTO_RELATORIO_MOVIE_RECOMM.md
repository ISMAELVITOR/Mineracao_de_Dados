# Continuação do relatório — banco `movie_recomm`

## Etapa 2 — Preparação dos dados

### 2.1 Seleção das tabelas e dos atributos

Para as etapas de preparação, análise exploratória e extração de regras de associação, foram selecionadas as tabelas `movielens_movies` e `movielens_ratings`. A primeira contém o identificador, o título e os gêneros de 9.742 filmes. A segunda contém 100.836 avaliações realizadas por 610 usuários, incluindo o identificador do filme, a nota e o instante da avaliação.

Essa seleção reduz a complexidade da base sem perder as informações necessárias para estudar associações entre gêneros, período de lançamento, avaliação média e popularidade. As demais tabelas representam outro subconjunto cinematográfico, com elenco, pessoas, categorias e palavras-chave, mas não possuem uma ligação direta documentada com os identificadores do MovieLens. Por esse motivo, não foram usadas nesta estratégia.

### 2.2 Qualidade e integridade dos dados

Não foram encontrados valores nulos nos atributos essenciais das duas tabelas. Todas as avaliações correspondem a filmes cadastrados, e não existem duplicatas da combinação `userId` e `movieId`. Foram identificados 18 filmes sem avaliação, 34 filmes com o marcador `(no genres listed)`, 13 títulos que não terminam com um ano no formato esperado e cinco pares de títulos repetidos associados a identificadores diferentes.

Os títulos repetidos não foram removidos, pois os registros possuem identificadores e, em alguns casos, classificações de gênero diferentes. Os filmes sem avaliações e sem gênero conhecido permaneceram no relatório de qualidade, mas não foram utilizados na mineração. Os textos foram normalizados por meio da remoção de espaços excedentes, os atributos numéricos foram convertidos para tipos adequados e o `timestamp` foi convertido para data e hora.

### 2.3 Agregação e criação de variáveis

As avaliações foram agregadas por filme. Para cada produção, foram calculadas a quantidade de avaliações, a média, a mediana, o desvio-padrão, a primeira avaliação e a última avaliação. Para reduzir a instabilidade de médias calculadas com poucas observações, foram mantidos apenas filmes com pelo menos cinco avaliações e gênero conhecido. Após os filtros, permaneceram 3.649 filmes.

Foram criadas as seguintes variáveis:

- `ano_lancamento`, extraído do final do título;
- `periodo_lancamento`: antes de 1950, 1950–1969, 1970–1989, 1990–1999, 2000–2009 e 2010–2018;
- `faixa_avaliacao`: baixa para média menor que 3,0, intermediária para média entre 3,0 e menos de 4,0 e alta para média igual ou superior a 4,0;
- `faixa_popularidade`: baixa para 5 a 9 avaliações, intermediária para 10 a 49 e alta para 50 ou mais;
- `quantidade_generos`, correspondente à quantidade de gêneros associados ao filme.

## Etapa 3 — Caracterização exploratória

### 3.1 Distribuição das avaliações

As notas variam de 0,5 a 5,0. A média geral é aproximadamente 3,50, a mediana é 3,5 e o desvio-padrão é cerca de 1,04. A nota 4,0 é a mais frequente, seguida pela nota 3,0. A Figura `01_distribuicao_notas.png` apresenta essa distribuição.

A distribuição das médias por filme é concentrada principalmente entre 3,0 e 4,0, conforme a Figura `02_histograma_media_avaliacoes.png`. Entre os 3.649 filmes preparados, 2.336 estão na faixa intermediária de avaliação, 873 na faixa baixa e 440 na faixa alta.

### 3.2 Popularidade e valores extremos

A quantidade de avaliações por filme apresenta forte assimetria. Na base completa, a mediana é três avaliações e o máximo é 329. Após o filtro mínimo de cinco avaliações, 1.380 filmes ficaram na faixa de baixa popularidade, 1.819 na faixa intermediária e 450 na faixa alta.

O histograma em escala logarítmica e o boxplot mostram que poucos filmes concentram grande quantidade de avaliações. Pelo critério do intervalo interquartil, foram identificados 335 valores extremos na quantidade de avaliações. Esses registros não foram removidos porque representam filmes realmente populares e são relevantes para compreender o comportamento da base. Também foram identificados 32 valores extremos na avaliação média e 85 no desvio-padrão.

### 3.3 Frequência dos gêneros e períodos

Os gêneros mais frequentes são drama, presente em 1.597 filmes (43,77%), comédia, em 1.479 (40,53%), ação, em 928 (25,43%), e suspense, em 890 (24,39%). Como um filme pode possuir vários gêneros, os percentuais não somam 100%. A Figura `06_generos_mais_frequentes.png` apresenta as quinze categorias mais frequentes.

Os períodos com mais filmes são 2000–2009, com 1.145 registros, e 1990–1999, com 1.111. Em seguida aparecem 1970–1989, com 651, e 2010–2018, com 463. A concentração nos períodos mais recentes deve ser considerada na interpretação das regras temporais.

### 3.4 Correlações

A matriz de correlação mostra relação muito alta entre média e mediana das avaliações, aproximadamente 0,93, o que é esperado porque ambas resumem a mesma distribuição. A quantidade de avaliações possui correlação positiva fraca com a média, aproximadamente 0,26. O ano de lançamento apresenta correlação negativa fraca com a média, aproximadamente -0,19. Essas relações descrevem associação linear e não devem ser interpretadas como causalidade.

## Etapa 4 — Modelagem da estratégia transacional

Foi adotada uma transação por filme. Cada transação combina todos os gêneros associados ao filme com seu período de lançamento, sua faixa de avaliação média e sua faixa de popularidade. Um exemplo é:

`{genero_animacao, genero_aventura, genero_infantil, periodo_1990_1999, avaliacao_media, popularidade_alta}`.

A estratégia reúne três abordagens previstas no trabalho: agregação por entidade, discretização de atributos numéricos e junção entre tabelas. A alternativa de criar uma transação por usuário foi descartada porque produziria apenas 610 transações e tenderia a gerar padrões muito gerais de consumo. A estratégia por filme fornece 3.649 transações e permite interpretar diretamente as características que coexistem nas produções.

## Etapa 5 — Extração das regras de associação

Foi utilizado o algoritmo FP-Growth, disponível na biblioteca `mlxtend`. O algoritmo foi escolhido por ser eficiente na identificação de conjuntos frequentes sem gerar explicitamente todos os candidatos do Apriori.

Os parâmetros utilizados foram:

- suporte mínimo: 0,02;
- confiança mínima: 0,55;
- lift mínimo: 1,10;
- tamanho máximo de quatro itens por conjunto frequente;
- antecedente com no máximo dois itens;
- consequente com exatamente um item.

Com 3.649 transações, o suporte mínimo exige que um padrão apareça em aproximadamente 73 filmes. A confiança mínima exige que o consequente ocorra em mais da metade dos filmes que contêm o antecedente. O lift mínimo mantém apenas associações pelo menos 10% mais frequentes que o esperado pelas frequências individuais.

Foram obtidos 501 conjuntos frequentes e 121 regras após os filtros. Para reduzir redundância, uma regra com dois itens no antecedente foi removida quando aumentava a confiança em menos de cinco pontos percentuais em relação a uma regra mais simples com o mesmo consequente. Restaram 85 regras não redundantes. Trinta delas foram selecionadas para a elaboração das perguntas e respostas exigidas pelo trabalho.

## Etapa 6 — Análise das regras relevantes

Algumas regras com maior relevância são:

1. `{genero_animacao} → {genero_infantil}`: suporte de 4,08%, confiança de 65,64% e lift de 7,53. A associação é forte e coerente com as convenções de classificação cinematográfica.
2. `{genero_aventura, genero_suspense} → {genero_acao}`: suporte de 3,15%, confiança de 85,19% e lift de 3,35. A combinação de aventura e suspense aparece frequentemente acompanhada por ação.
3. `{genero_misterio} → {genero_suspense}`: suporte de aproximadamente 4,74%, confiança de cerca de 67,05% e lift de aproximadamente 2,75. O padrão é esperado devido à proximidade temática entre os gêneros.
4. `{genero_imax} → {periodo_2010_2018}`: suporte de 2,19%, confiança de 66,12% e lift de 5,21. A regra mostra forte concentração do formato IMAX no período mais recente da base.
5. `{avaliacao_alta} → {genero_drama}`: suporte de aproximadamente 7,95%, confiança de cerca de 65,91% e lift de aproximadamente 1,51. Filmes com avaliação média alta apresentam drama com frequência superior à presença geral desse gênero na amostra.

As regras de gêneros possuem, em geral, maior lift e interpretação mais direta. Algumas regras com `avaliacao_media` como consequente possuem suporte e confiança elevados, mas lift próximo do limite mínimo, pois essa é a faixa de avaliação mais frequente. Por isso, a seleção das regras não deve considerar apenas a confiança.

### Limitações

As regras indicam coocorrência, não causalidade. A base é influenciada pela seleção dos usuários, pelo período em que as avaliações foram realizadas e pelo fato de filmes populares possuírem mais oportunidades de receber notas. O filtro de pelo menos cinco avaliações reduz a instabilidade, mas não elimina o viés de popularidade. Além disso, os gêneros são rótulos editoriais, e parte das associações reflete convenções de classificação, como animação e infantil.

As trinta perguntas e respostas estão no arquivo `top_30_perguntas_respostas.csv`, e uma versão pronta para inclusão no relatório está em `texto_resultados_regras.md`.
