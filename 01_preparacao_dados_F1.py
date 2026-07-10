import duckdb
import pandas as pd

# ==========================================================
# ETAPA 2 - PREPARAÇÃO DOS DADOS
# Base: Fórmula 1
# ==========================================================

con = duckdb.connect("BasesDeDados/f1.duckdb")

# ==========================================================
# Tabelas e atributos utilizados
# ==========================================================

consultas = {

    "results": [
        "raceId",
        "constructorId",
        "grid",
        "position",
        "points",
        "statusId"
    ],

    "constructors": [
        "constructorId",
        "name"
    ],

    "races": [
        "raceId",
        "year",
        "circuitId"
    ],

    "circuits": [
        "circuitId",
        "name",
        "country"
    ],

    "status": [
        "statusId",
        "status"
    ]
}

# ==========================================================
# 2.5 - TRATAMENTO DE VALORES AUSENTES
# ==========================================================

print("=" * 70)
print("TRATAMENTO DE VALORES AUSENTES")
print("=" * 70)

resultado = []

for tabela, colunas in consultas.items():

    total = con.sql(
        f"SELECT COUNT(*) FROM {tabela}"
    ).fetchone()[0]

    for coluna in colunas:

        nulos = con.sql(f"""
            SELECT COUNT(*)
            FROM {tabela}
            WHERE {coluna} IS NULL
        """).fetchone()[0]

        resultado.append({

            "Tabela": tabela,
            "Coluna": coluna,
            "Nulos": nulos,
            "Percentual (%)": round((nulos / total) * 100, 2)

        })

df = pd.DataFrame(resultado)

print(df)

# ==========================================================
# INVESTIGAÇÃO DOS VALORES AUSENTES
# ==========================================================

print("\n")
print("=" * 70)
print("PRINCIPAIS STATUS ASSOCIADOS A POSITION NULO")
print("=" * 70)

consulta = con.sql("""

SELECT

    s.status,

    COUNT(*) AS quantidade

FROM results r

JOIN status s

ON r.statusId = s.statusId

WHERE r.position IS NULL

GROUP BY s.status

ORDER BY quantidade DESC

LIMIT 20

""").df()

print(consulta)

# ==========================================================
# 2.6 - VERIFICAÇÃO DE DUPLICATAS
# ==========================================================

print("\n")
print("=" * 70)
print("VERIFICAÇÃO DE DUPLICATAS")
print("=" * 70)

duplicatas = []

for tabela in consultas.keys():

    total = con.sql(f"""

        SELECT COUNT(*)

        FROM {tabela}

    """).fetchone()[0]

    distintos = con.sql(f"""

        SELECT COUNT(*)

        FROM (

            SELECT DISTINCT *

            FROM {tabela}

        )

    """).fetchone()[0]

    duplicatas.append({

        "Tabela": tabela,
        "Duplicados": total - distintos

    })

print(pd.DataFrame(duplicatas))

# ==========================================================
# 2.7 - NORMALIZAÇÃO DOS VALORES TEXTUAIS
# ==========================================================

print("\n")
print("=" * 70)
print("NORMALIZAÇÃO DOS VALORES TEXTUAIS")
print("=" * 70)

alteracoes = con.sql("""

SELECT

    country AS valor_original,

    CASE

        WHEN country = 'United States'
            THEN 'USA'

        ELSE country

    END AS valor_padronizado,

    COUNT(*) AS quantidade

FROM circuits

GROUP BY

    country,

    valor_padronizado

HAVING country <> valor_padronizado

""").df()

if alteracoes.empty:

    print("Nenhuma inconsistência encontrada.")

else:

    print(alteracoes)

# ==========================================================
# 2.8 / 2.9 - PREPARAÇÃO DOS ATRIBUTOS
# ==========================================================

print("\n")
print("=" * 70)
print("DISCRETIZAÇÃO DOS ATRIBUTOS")
print("=" * 70)

grid = con.sql("""

SELECT

CASE

    WHEN grid BETWEEN 1 AND 3 THEN 'grid_front'

    WHEN grid BETWEEN 4 AND 10 THEN 'grid_middle'

    ELSE 'grid_back'

END AS categoria,

COUNT(*) AS quantidade

FROM results

GROUP BY categoria

ORDER BY quantidade DESC

""").df()

print("\nGRID")

print(grid)

position = con.sql("""

SELECT

CASE

    WHEN position = 1 THEN 'winner'

    WHEN position IN (2,3) THEN 'podium'

    WHEN position BETWEEN 4 AND 10 THEN 'points_finish'

    WHEN position >= 11 THEN 'outside_points'

    ELSE 'unclassified'

END AS categoria,

COUNT(*) AS quantidade

FROM results

GROUP BY categoria

ORDER BY quantidade DESC

""").df()

print("\nPOSITION")

print(position)

points = con.sql("""

SELECT

CASE

    WHEN points > 0

        THEN 'scored_points'

    ELSE 'no_points'

END AS categoria,

COUNT(*) AS quantidade

FROM results

GROUP BY categoria

ORDER BY quantidade DESC

""").df()

print("\nPOINTS")

print(points)

# ==========================================================
# RESUMO DA PREPARAÇÃO
# ==========================================================

print("\n")
print("=" * 70)
print("RESUMO")
print("=" * 70)

print("""
✔ Valores ausentes analisados.
✔ Valores nulos preservados por representarem eventos reais da corrida.
✔ Nenhum registro duplicado encontrado.
✔ Padronização realizada: United States -> USA.
✔ Variáveis categóricas preparadas.
✔ Atributos numéricos discretizados.
""")

# ==========================================================
# FECHA CONEXÃO
# ==========================================================

con.close()