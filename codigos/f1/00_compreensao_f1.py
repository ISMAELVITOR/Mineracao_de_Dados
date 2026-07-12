"""Gera um inventário estrutural da base F1 sem alterar o DuckDB."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"
TABELAS_ESCOLHIDAS = ["results", "constructors", "races", "circuits", "status", "drivers"]


def main() -> None:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(BASES_DIR / "f1.duckdb"), read_only=True) as con:
        tabelas = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        linhas = []
        for tabela in tabelas:
            colunas = con.execute(f"DESCRIBE {tabela}").df()
            total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            for _, coluna in colunas.iterrows():
                nome = coluna["column_name"]
                nulos = con.execute(
                    f'SELECT COUNT(*) FROM {tabela} WHERE "{nome}" IS NULL'
                ).fetchone()[0]
                linhas.append({"tabela": tabela, "registros": total, "atributo": nome,
                               "tipo": coluna["column_type"], "nulos": nulos})
        pd.DataFrame(linhas).to_csv(RESULTADOS_DIR / "compreensao_f1.csv", index=False)
        resumo = {"tabelas": tabelas, "tabelas_escolhidas": TABELAS_ESCOLHIDAS,
                  "relacionamentos": ["results.raceId -> races.raceId",
                    "results.constructorId -> constructors.constructorId",
                    "results.statusId -> status.statusId", "races.circuitId -> circuits.circuitId"]}
        (RESULTADOS_DIR / "compreensao_f1.json").write_text(
            json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Compreensão F1: {len(tabelas)} tabelas catalogadas.")


if __name__ == "__main__":
    main()
