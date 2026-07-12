import duckdb
import pandas as pd

from pathlib import Path

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules

# ==========================================================
# ETAPA 5 - EXTRAÇÃO DE REGRAS DE ASSOCIAÇÃO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_DIR = BASE_DIR / "BasesDeDados"

RESULTADOS_DIR = BASE_DIR / "resultados"

RESULTADOS_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_DIR / "f1.duckdb"))

# ==========================================================
# EQUIPES PRINCIPAIS
# ==========================================================

equipes_principais = con.sql("""

SELECT

    c.name

FROM results r

JOIN constructors c

ON r.constructorId = c.constructorId

GROUP BY c.name

HAVING COUNT(*) >= 500

ORDER BY COUNT(*) DESC

""").df()["name"].tolist()

print("=" * 70)
print("EQUIPES UTILIZADAS")
print("=" * 70)

for equipe in equipes_principais:
    print(equipe)

# ==========================================================
# LEITURA DA BASE
# ==========================================================

consulta = con.sql("""

SELECT

    r.grid,

    r.position,

    r.points,

    c.name AS equipe

FROM results r

JOIN constructors c

ON r.constructorId = c.constructorId

WHERE r.grid > 0

""").df()

print("\n")
print("=" * 70)
print("BASE")
print("=" * 70)

print(consulta.head())

# ==========================================================
# CONSTRUÇÃO DAS TRANSAÇÕES
# ==========================================================

transacoes = []

for _, linha in consulta.iterrows():

    itens = []

    # ---------------- GRID ----------------

    if linha["grid"] <= 6:

        itens.append("Grid_Front")

    elif linha["grid"] <= 12:

        itens.append("Grid_Middle")

    else:

        itens.append("Grid_Back")

    # ---------------- RESULTADO ----------------

    if pd.isna(linha["position"]):

        itens.append("Abandono")

    elif linha["position"] == 1:

        itens.append("Venceu")

    elif linha["position"] <= 3:

        itens.append("Podio")

    elif linha["points"] > 0:

        itens.append("Pontuou")

    else:

        itens.append("Nao_Pontuou")

    # ---------------- EQUIPE ----------------

    if linha["equipe"] in equipes_principais:

        itens.append("Equipe_" + linha["equipe"])

    else:

        itens.append("Equipe_Outras")

    transacoes.append(itens)

print("\n")
print("=" * 70)
print("TRANSAÇÕES")
print("=" * 70)

print(f"Quantidade de transações: {len(transacoes)}")

print("\nPrimeiras transações:\n")

for t in transacoes[:10]:
    print(t)

# ==========================================================
# MATRIZ BINÁRIA
# ==========================================================

encoder = TransactionEncoder()

matriz = encoder.fit(transacoes).transform(transacoes)

df = pd.DataFrame(

    matriz,

    columns=encoder.columns_

)

print("\n")
print("=" * 70)
print("MATRIZ BINÁRIA")
print("=" * 70)

print(df.head())

print("\nItens diferentes:", len(df.columns))

# ==========================================================
# TESTE DOS PARÂMETROS
# ==========================================================

print("\n")
print("=" * 70)
print("TESTE DOS PARÂMETROS")
print("=" * 70)

suportes = [

    0.05,
    0.04,
    0.03,
    0.02,
    0.015,
    0.01,
    0.005

]

resultado_testes = []

for suporte in suportes:

    itemsets = apriori(

        df,

        min_support=suporte,

        use_colnames=True

    )

    regras = association_rules(

        itemsets,

        metric="confidence",

        min_threshold=0.60

    )

    resultado_testes.append({

        "Suporte": suporte,

        "Itemsets": len(itemsets),

        "Regras": len(regras)

    })

resultado = pd.DataFrame(resultado_testes)

print(resultado)

print("\n")

SUPORTE_MINIMO = 0.02

CONFIANCA_MINIMA = 0.60

print("\n")
print("=" * 70)
print("PARÂMETROS UTILIZADOS")
print("=" * 70)

print(f"Suporte mínimo   : {SUPORTE_MINIMO:.2f}")

print(f"Confiança mínima : {CONFIANCA_MINIMA:.2f}")

# ==========================================================
# ITEMSETS FREQUENTES
# ==========================================================

itemsets = apriori(

    df,

    min_support=SUPORTE_MINIMO,

    use_colnames=True

)

itemsets = itemsets.sort_values(

    by="support",

    ascending=False

)

print("\n")
print("=" * 70)
print("ITEMSETS FREQUENTES")
print("=" * 70)

print(itemsets.head(20))

# ==========================================================
# REGRAS DE ASSOCIAÇÃO
# ==========================================================

regras = association_rules(

    itemsets,

    metric="confidence",

    min_threshold=CONFIANCA_MINIMA

)

if len(regras) == 0:

    print("\nNenhuma regra encontrada com esses parâmetros.")

else:

    regras = regras[

        [

            "antecedents",

            "consequents",

            "support",

            "confidence",

            "lift"

        ]

    ]

    regras = regras.sort_values(

        by=[

            "lift",

            "confidence",

            "support"

        ],

        ascending=False

    )

    print("\n")
    print("=" * 70)
    print("MELHORES REGRAS")
    print("=" * 70)

    print(regras.head(30))

    print("\n")
    print(f"Quantidade total de regras: {len(regras)}")

    top10_regras = regras.head(10).copy()

    top10_regras_relatorio = pd.DataFrame({

        "Regra": top10_regras.apply(

            lambda linha: f"{', '.join(sorted(linha['antecedents']))} -> {', '.join(sorted(linha['consequents']))}",

            axis=1

        ),

        "Suporte": top10_regras["support"],

        "Confiança": top10_regras["confidence"],

        "Lift": top10_regras["lift"]

    }).reset_index(drop=True)

    print("\n")
    print("=" * 70)
    print("TOP 10 REGRAS PARA O RELATÓRIO")
    print("=" * 70)

    print(top10_regras_relatorio.to_string(index=False))

    # ======================================================
    # EXPORTAÇÃO
    # ======================================================

    regras_exportacao = regras.copy()

    regras_exportacao["antecedents"] = regras_exportacao["antecedents"].astype(str)

    regras_exportacao["consequents"] = regras_exportacao["consequents"].astype(str)

    regras_exportacao.to_csv(

        RESULTADOS_DIR / "regras_associacao_geral.csv",

        index=False,

        sep=";",

        decimal=","

    )

    itemsets_exportacao = itemsets.copy()

    itemsets_exportacao["itemsets"] = itemsets_exportacao["itemsets"].astype(str)

    itemsets_exportacao.to_csv(

        RESULTADOS_DIR / "itemsets_frequentes_geral.csv",

        index=False,

        sep=";",

        decimal=","

    )

    top10_regras_relatorio.to_csv(

        RESULTADOS_DIR / "top10_regras_geral.csv",

        index=False,

        sep=";",

        decimal=","

    )

    print("\n")
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)

    print(f"\nQuantidade total de regras: {len(regras)}")

    print(f"\nQuantidade de regras apresentadas no relatório: {len(top10_regras_relatorio)}")

    print("\nArquivos gerados:")

    print("✔ itemsets_frequentes_geral.csv")

    print("✔ regras_associacao_geral.csv")

    print("✔ top10_regras_geral.csv")

con.close()
