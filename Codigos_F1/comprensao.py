import duckdb
import pandas as pd
from pathlib import Path

# ==========================================================
# ETAPA 1 - COMPREENSÃO DA BASE
# ==========================================================

# Escolha o banco:
# "F1" ou "MOVIE"
BANCO = "MOVIE"

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "BasesDeDados"

# ==========================================================
# CONFIGURAÇÃO DOS BANCOS
# ==========================================================

if BANCO == "F1":

    con = duckdb.connect(str(DB_DIR / "f1.duckdb"))

    tabelas = [
        "circuits",
        "constructor_results",
        "constructor_standings",
        "constructors",
        "driver_standings",
        "drivers",
        "lap_times",
        "pit_stops",
        "position_descriptions",
        "qualifying",
        "races",
        "results",
        "seasons",
        "sprint_results",
        "status"
    ]

else:

    con = duckdb.connect(str(DB_DIR / "movie_recomm.duckdb"))

    tabelas = [
        "all_casts",
        "all_categories",
        "all_characters",
        "all_movie_aliases_iso",
        "all_people",
        "category_names",
        "job_names",
        "movie_categories",
        "movie_keywords",
        "movielens_movies",
        "movielens_ratings"
    ]

# ==========================================================
# RESUMO DAS TABELAS
# ==========================================================

print("=" * 70)
print(f"BANCO: {BANCO}")
print("=" * 70)

print("\nRESUMO DAS TABELAS")
print("=" * 70)

resumo = []

for tabela in tabelas:

    registros = con.sql(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]

    descricao = con.sql(f"DESCRIBE {tabela}").df()

    resumo.append({
        "Tabela": tabela,
        "Registros": registros,
        "Colunas": len(descricao)
    })

resumo_df = pd.DataFrame(resumo)

print(resumo_df)

# ==========================================================
# COLUNAS E TIPOS
# ==========================================================

print("\n")
print("=" * 70)
print("COLUNAS DAS TABELAS")
print("=" * 70)

relacionamentos = []

for tabela in tabelas:

    descricao = con.sql(f"DESCRIBE {tabela}").df()

    print(f"\nTabela: {tabela}")

    print(descricao[["column_name", "column_type"]])

    for coluna in descricao["column_name"]:

        if coluna.lower().endswith("id"):

            relacionamentos.append({
                "Coluna": coluna,
                "Tabela": tabela
            })

# ==========================================================
# POSSÍVEIS RELACIONAMENTOS
# ==========================================================

print("\n")
print("=" * 70)
print("POSSÍVEIS RELACIONAMENTOS")
print("=" * 70)

rel = pd.DataFrame(relacionamentos)

for coluna in sorted(rel["Coluna"].unique()):

    tabelas_rel = rel.loc[
        rel["Coluna"] == coluna,
        "Tabela"
    ].tolist()

    if len(tabelas_rel) > 1:

        print(f"\n{coluna}")

        for tabela in tabelas_rel:

            print(f"   -> {tabela}")

con.close()
