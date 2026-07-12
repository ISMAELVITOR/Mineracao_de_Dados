import duckdb
import pandas as pd

from pathlib import Path
from collections import Counter

# ==========================================================
# ETAPA 5 - PREPARAÇÃO DAS TRANSAÇÕES
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_DIR = BASE_DIR / "BasesDeDados"

con = duckdb.connect(str(DB_DIR / "f1.duckdb"))

# ==========================================================
# Leitura da base
# ==========================================================

consulta = con.sql("""

SELECT

    r.grid,
    r.position,
    r.points,

    s.status,

    c.name AS equipe,

    ci.country

FROM results r

JOIN constructors c

ON r.constructorId = c.constructorId

JOIN races ra

ON r.raceId = ra.raceId

JOIN circuits ci

ON ra.circuitId = ci.circuitId

JOIN status s

ON r.statusId = s.statusId

WHERE r.grid > 0

""").df()

print("="*70)
print("BASE")
print("="*70)

print(consulta.head())

# ==========================================================
# Informações gerais
# ==========================================================

print("\n")
print("="*70)
print("INFORMAÇÕES GERAIS")
print("="*70)

print(f"Registros : {len(consulta)}")

print(f"Equipes   : {consulta['equipe'].nunique()}")

print(f"Países    : {consulta['country'].nunique()}")

# ==========================================================
# Construção das transações
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

    # ---------------- STATUS ----------------

    if linha["status"] == "Finished":

        itens.append("Finished")

    else:

        itens.append("Abandono_Status")

    # ---------------- EQUIPE ----------------

    itens.append("Equipe_" + linha["equipe"])

    # ---------------- PAÍS ----------------

    itens.append("Pais_" + linha["country"])

    transacoes.append(itens)

print("\n")
print("="*70)
print("TRANSAÇÕES")
print("="*70)

print(f"Quantidade de transações: {len(transacoes)}")

print("\nPrimeiras 5 transações:\n")

for t in transacoes[:5]:

    print(t)

# ==========================================================
# Frequência dos itens
# ==========================================================

contador = Counter()

for t in transacoes:

    contador.update(t)

freq = (

    pd.DataFrame(

        contador.items(),

        columns=["Item","Frequencia"]

    )

    .sort_values(

        by="Frequencia",

        ascending=False

    )

)

print("\n")
print("="*70)
print("ITENS MAIS FREQUENTES")
print("="*70)

print(freq.head(40))

# ==========================================================
# Quantidade de itens distintos
# ==========================================================

print("\n")
print("="*70)
print("RESUMO")
print("="*70)

print(f"Itens distintos : {len(freq)}")

print(f"Transações      : {len(transacoes)}")

print(f"Média de itens por transação : {sum(len(t) for t in transacoes)/len(transacoes):.2f}")

con.close()