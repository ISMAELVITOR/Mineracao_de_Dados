"""Constrói transações F1 com grid, resultado e equipe."""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"


def equipes_principais(con: duckdb.DuckDBPyConnection) -> set[str]:
    linhas = con.execute("""SELECT c.name FROM results r JOIN constructors c
        ON r.constructorId=c.constructorId GROUP BY c.name HAVING COUNT(*) >= 500""").fetchall()
    return {linha[0] for linha in linhas}


def categoria_grid(grid: int) -> str:
    if grid <= 6: return "Grid_Front"
    if grid <= 12: return "Grid_Middle"
    return "Grid_Back"


def categoria_resultado(position: float, points: float) -> str:
    if pd.isna(position): return "Abandono"
    if position == 1: return "Venceu"
    if position in (2, 3): return "Podio"
    if points > 0 and position > 3: return "Pontuou"
    return "Nao_Pontuou"


def gerar_transacoes(ano_inicial: int, ano_final: int, saida: Path) -> pd.DataFrame:
    with duckdb.connect(str(BASES_DIR / "f1.duckdb"), read_only=True) as con:
        equipes = equipes_principais(con)
        dados = con.execute("""SELECT r.grid, r.position, r.points, c.name AS equipe
            FROM results r JOIN races ra ON r.raceId=ra.raceId
            JOIN constructors c ON r.constructorId=c.constructorId
            WHERE r.grid > 0 AND ra.year BETWEEN ? AND ?""", [ano_inicial, ano_final]).df()
    transacoes = pd.DataFrame({
        "grid": dados["grid"].map(categoria_grid),
        "resultado": [categoria_resultado(p, pts) for p, pts in zip(dados["position"], dados["points"])],
        "equipe": dados["equipe"].map(lambda e: f"Equipe_{e}" if e in equipes else "Equipe_Outras"),
    })
    if not (transacoes.notna().all().all() and (transacoes.nunique(axis=1) == 3).all()):
        raise ValueError("Toda transação F1 deve conter exatamente três itens distintos.")
    saida.parent.mkdir(parents=True, exist_ok=True); transacoes.to_csv(saida, index=False)
    return transacoes


def argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(); p.add_argument("--ano-inicial", type=int); p.add_argument("--ano-final", type=int)
    p.add_argument("--saida", type=Path); return p.parse_args()


def main() -> None:
    args = argumentos()
    periodos = [(args.ano_inicial, args.ano_final)] if args.ano_inicial and args.ano_final else [(1950, 2024), (1950, 1959), (2014, 2024)]
    for inicio, fim in periodos:
        saida = args.saida or RESULTADOS_DIR / f"transacoes_f1_{inicio}_{fim}.csv"
        df = gerar_transacoes(inicio, fim, saida); print(f"F1 {inicio}–{fim}: {len(df)} transações, {pd.unique(df.values.ravel()).size} itens.")


if __name__ == "__main__": main()
