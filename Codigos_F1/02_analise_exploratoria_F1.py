import duckdb
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import MaxNLocator

# ==========================================================
# ETAPA 3 - CARACTERIZAÇÃO EXPLORATÓRIA DOS DADOS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "BasesDeDados"
GRAFICOS_DIR = BASE_DIR / "graficos"

con = duckdb.connect(str(DB_DIR / "f1.duckdb"))

GRAFICOS_DIR.mkdir(exist_ok=True)

# ==========================================================
# 3.1 - Evolução da Fórmula 1 ao longo das temporadas
# ==========================================================

consulta = con.sql("""

SELECT

    r.year,

    COUNT(DISTINCT r.raceId) AS corridas,

    COUNT(DISTINCT c.country) AS paises

FROM races r

JOIN circuits c
ON r.circuitId = c.circuitId

GROUP BY r.year

ORDER BY r.year

""").df()

print("\n")
print("="*70)
print("EVOLUÇÃO DA FÓRMULA 1")
print("="*70)
print(consulta)

plt.figure(figsize=(13,6))

plt.plot(
    consulta["year"],
    consulta["corridas"],
    marker="o",
    markersize=5,
    linewidth=2,
    label="Corridas"
)

plt.plot(
    consulta["year"],
    consulta["paises"],
    marker="s",
    markersize=5,
    linewidth=2,
    label="Países"
)

plt.title("Evolução da Fórmula 1 ao longo das temporadas")

plt.xlabel("Temporada")

plt.ylabel("Quantidade")

plt.ylim(bottom=0)

plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

plt.grid(alpha=0.3)

plt.legend()

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "01_evolucao_formula1.png", dpi=300)

plt.close()

print("\nResumo")
print(f"Primeira temporada : {consulta['year'].min()}")
print(f"Última temporada   : {consulta['year'].max()}")
print(f"Máx. corridas      : {consulta['corridas'].max()}")
print(f"Máx. países        : {consulta['paises'].max()}")

# ==========================================================
# 3.2 - Grandes Prêmios disputados por equipe
# ==========================================================

consulta = con.sql("""

SELECT

    c.name,

    COUNT(DISTINCT r.raceId) AS grandes_premios

FROM results r

JOIN constructors c

ON r.constructorId = c.constructorId

GROUP BY c.name

ORDER BY grandes_premios DESC

LIMIT 20

""").df()

print("\n")
print("="*70)
print("GRANDES PRÊMIOS POR EQUIPE")
print("="*70)
print(consulta)

plt.figure(figsize=(11,7))

plt.barh(

    consulta["name"],

    consulta["grandes_premios"]

)

plt.title("Grandes Prêmios disputados por equipe")

plt.xlabel("Grandes Prêmios")

plt.grid(axis="x", alpha=0.3)

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "02_grandes_premios_equipes.png")

plt.close()

print("\nGráfico 2 gerado.")


# ==========================================================
# 3.3 - Taxa de vitória por equipe
# ==========================================================

consulta = con.sql("""

SELECT

    c.name,

    COUNT(DISTINCT r.raceId) AS grandes_premios,

    SUM(

        CASE

            WHEN r.position = 1

            THEN 1

            ELSE 0

        END

    ) AS vitorias,

    ROUND(

        100.0 *

        SUM(

            CASE

                WHEN r.position = 1

                THEN 1

                ELSE 0

            END

        )

        /

        COUNT(DISTINCT r.raceId),

        2

    ) AS taxa

FROM results r

JOIN constructors c

ON r.constructorId = c.constructorId

GROUP BY c.name

HAVING COUNT(DISTINCT r.raceId) >= 100

ORDER BY taxa DESC

LIMIT 20

""").df()

print("\n")
print("="*70)
print("TAXA DE VITÓRIA POR EQUIPE")
print("="*70)
print(consulta)

plt.figure(figsize=(11,7))

plt.barh(

    consulta["name"],

    consulta["taxa"]

)

plt.xlim(0,100)

plt.title("Taxa de vitória por equipe")

plt.xlabel("Vitórias (%)")

plt.grid(axis="x", alpha=0.3)

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "03_taxa_vitorias.png")

plt.close()

print("\nGráfico 3 gerado.")

# ==========================================================
# 3.4 - Nacionalidade dos pilotos vencedores
# ==========================================================

consulta = con.sql("""

SELECT

    d.nationality,

    COUNT(*) AS vitorias

FROM results r

JOIN drivers d

ON r.driverId = d.driverId

WHERE r.position = 1

GROUP BY d.nationality

ORDER BY vitorias DESC

LIMIT 15

""").df()

print("\n")
print("="*70)
print("NACIONALIDADE DOS PILOTOS VENCEDORES")
print("="*70)
print(consulta)

plt.figure(figsize=(10,7))

plt.barh(

    consulta["nationality"],

    consulta["vitorias"]

)

plt.title("Nacionalidade dos pilotos vencedores")

plt.xlabel("Vitórias")

plt.grid(axis="x", alpha=0.3)

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "04_nacionalidade_vencedores.png")

plt.close()

print("\nGráfico 4 gerado.")

# ==========================================================
# 3.4 - Nacionalidade dos pilotos vencedores
# ==========================================================

consulta = con.sql("""

SELECT

    d.nationality,

    COUNT(*) AS vitorias

FROM results r

JOIN drivers d

ON r.driverId = d.driverId

WHERE r.position = 1

GROUP BY d.nationality

ORDER BY vitorias DESC

LIMIT 15

""").df()

print("\n")
print("="*70)
print("NACIONALIDADE DOS PILOTOS VENCEDORES")
print("="*70)
print(consulta)

plt.figure(figsize=(10,7))

plt.barh(

    consulta["nationality"],

    consulta["vitorias"]

)

plt.title("Nacionalidade dos pilotos vencedores")

plt.xlabel("Vitórias")

plt.grid(axis="x", alpha=0.3)

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "04_nacionalidade_vencedores.png")

plt.close()

print("\nGráfico 4 gerado.")

# ==========================================================
# 3.6 - Equipe dominante por década
# ==========================================================

consulta = con.sql("""

SELECT

    FLOOR(ra.year/10)*10 AS decada,

    c.name,

    COUNT(*) AS vitorias

FROM results r

JOIN races ra

ON r.raceId = ra.raceId

JOIN constructors c

ON r.constructorId = c.constructorId

WHERE r.position = 1

GROUP BY

    decada,

    c.name

QUALIFY

ROW_NUMBER()

OVER(

PARTITION BY decada

ORDER BY vitorias DESC

)=1

ORDER BY decada

""").df()

print("\n")
print("="*70)
print("EQUIPE DOMINANTE POR DÉCADA")
print("="*70)
print(consulta)

labels = [

    f"{int(d)}\n{e}"

    for d,e in zip(

        consulta["decada"],

        consulta["name"]

    )

]

plt.figure(figsize=(12,6))

plt.bar(

    labels,

    consulta["vitorias"]

)

plt.title("Equipe com maior número de vitórias em cada década")

plt.xlabel("Década")

plt.ylabel("Vitórias")

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(GRAFICOS_DIR / "06_dominio_decadas.png")

plt.close()

print("\nGráfico 6 gerado.")

# ==========================================================
# 3.7 - Matriz de Correlação das Variáveis Numéricas
# ==========================================================

consulta = con.sql("""

SELECT

    grid,
    position,
    points

FROM results

WHERE position IS NOT NULL

""").df()

correlacao = consulta.corr(numeric_only=True)

print("\n")
print("=" * 70)
print("MATRIZ DE CORRELAÇÃO")
print("=" * 70)
print(correlacao)

plt.figure(figsize=(6,5))

plt.imshow(
    correlacao,
    cmap="Blues",
    vmin=-1,
    vmax=1
)

plt.xticks(
    range(len(correlacao.columns)),
    correlacao.columns,
    fontsize=10
)

plt.yticks(
    range(len(correlacao.columns)),
    correlacao.columns,
    fontsize=10
)

for i in range(len(correlacao.columns)):
    for j in range(len(correlacao.columns)):
        plt.text(
            j,
            i,
            f"{correlacao.iloc[i, j]:.2f}",
            ha="center",
            va="center",
            color="black",
            fontsize=11
        )

plt.colorbar(label="Correlação")

plt.title("Matriz de Correlação das Variáveis Numéricas")

plt.tight_layout()

plt.savefig(
    GRAFICOS_DIR / "07_matriz_correlacao.png",
    dpi=300
)

plt.close()

print("\nGráfico 7 gerado.")