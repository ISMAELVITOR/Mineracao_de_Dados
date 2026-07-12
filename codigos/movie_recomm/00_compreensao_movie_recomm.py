"""Documenta estrutura, nulidade e relacionamentos da base MovieLens."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "movie_recomm"
ESCOLHIDAS = ["movielens_movies", "movielens_ratings"]


def main() -> None:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    linhas = []
    with duckdb.connect(str(BASES_DIR / "movie_recomm.duckdb"), read_only=True) as con:
        tabelas = [x[0] for x in con.execute("SHOW TABLES").fetchall()]
        for tabela in tabelas:
            esquema = con.execute(f"DESCRIBE {tabela}").df(); total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            for _, coluna in esquema.iterrows():
                nome = coluna["column_name"]
                nulos = con.execute(f'SELECT COUNT(*) FROM {tabela} WHERE "{nome}" IS NULL').fetchone()[0]
                linhas.append({"tabela": tabela, "registros": total, "quantidade_atributos": len(esquema),
                               "atributo": nome, "tipo": coluna["column_type"], "nulos": nulos})
    pd.DataFrame(linhas).to_csv(RESULTADOS_DIR / "compreensao_movie_recomm.csv", index=False)
    resumo = {"tabelas": tabelas, "tabelas_escolhidas": ESCOLHIDAS,
              "possiveis_relacionamentos": ["movielens_ratings.movieId -> movielens_movies.movieId"]}
    (RESULTADOS_DIR / "compreensao_movie_recomm.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Compreensão MovieLens: {len(tabelas)} tabelas catalogadas.")


if __name__ == "__main__": main()
