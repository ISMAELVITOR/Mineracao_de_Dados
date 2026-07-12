"""Audita e prepara os atributos da F1 usados nas etapas seguintes."""
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"


def main() -> None:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    consulta = """
        SELECT ra.year, r.grid, r.position, r.points, c.name AS equipe,
               ci.country AS pais, s.status
        FROM results r
        JOIN races ra ON r.raceId = ra.raceId
        JOIN constructors c ON r.constructorId = c.constructorId
        JOIN circuits ci ON ra.circuitId = ci.circuitId
        JOIN status s ON r.statusId = s.statusId
    """
    with duckdb.connect(str(BASES_DIR / "f1.duckdb"), read_only=True) as con:
        dados = con.execute(consulta).df()
    dados["categoria_grid"] = pd.cut(
        dados["grid"], bins=[0, 6, 12, float("inf")],
        labels=["Grid_Front", "Grid_Middle", "Grid_Back"]
    ).astype("string")
    dados.loc[dados["grid"] <= 0, "categoria_grid"] = pd.NA
    dados["categoria_resultado"] = "Nao_Pontuou"
    dados.loc[dados["points"] > 0, "categoria_resultado"] = "Pontuou"
    dados.loc[dados["position"].isin([2, 3]), "categoria_resultado"] = "Podio"
    dados.loc[dados["position"] == 1, "categoria_resultado"] = "Venceu"
    dados.loc[dados["position"].isna(), "categoria_resultado"] = "Abandono"
    dados.to_csv(RESULTADOS_DIR / "dados_f1_preparados.csv", index=False)
    print(f"Preparação F1: {len(dados)} resultados; outliers válidos preservados.")


if __name__ == "__main__":
    main()
