"""Gera a análise exploratória e os gráficos consolidados da F1."""
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"
GRAFICOS_DIR = RESULTADOS_DIR / "graficos"


def salvar(figura: plt.Figure, nome: str) -> None:
    figura.tight_layout()
    figura.savefig(GRAFICOS_DIR / nome, dpi=300)
    plt.close(figura)


def main() -> None:
    GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(BASES_DIR / "f1.duckdb"), read_only=True) as con:
        dados = con.execute("""
            SELECT ra.year, ra.name AS corrida, ci.country, r.grid, r.position, r.points,
                   c.name AS equipe, d.nationality
            FROM results r JOIN races ra ON r.raceId=ra.raceId
            JOIN circuits ci ON ra.circuitId=ci.circuitId
            JOIN constructors c ON r.constructorId=c.constructorId
            JOIN drivers d ON r.driverId=d.driverId
        """).df()
    temporada = dados.groupby("year").agg(corridas=("corrida", "nunique"), paises=("country", "nunique"))
    ax = temporada.plot(figsize=(10, 5)); salvar(ax.figure, "01_evolucao_corridas_paises.png")
    gp_equipe = dados.groupby("equipe")["corrida"].nunique().nlargest(20)
    ax = gp_equipe.sort_values().plot.barh(figsize=(9, 7)); salvar(ax.figure, "02_grandes_premios_por_equipe.png")
    equipes = dados.groupby("equipe").agg(resultados=("position", "size"), vitorias=("position", lambda s: (s == 1).sum()))
    equipes["taxa_vitoria"] = equipes["vitorias"] / equipes["resultados"]
    ax = equipes.query("resultados >= 500")["taxa_vitoria"].sort_values().plot.barh(figsize=(9, 7))
    salvar(ax.figure, "03_taxa_vitoria_por_equipe.png")
    ax = dados.loc[dados["position"] == 1, "nationality"].value_counts().head(20).sort_values().plot.barh(figsize=(9, 7))
    salvar(ax.figure, "04_nacionalidade_vencedores.png")
    vencedores = dados[dados["position"] == 1].assign(decada=lambda d: d["year"] // 10 * 10)
    dominio = vencedores.groupby(["decada", "equipe"]).size().rename("vitorias").reset_index()
    dominio = dominio.loc[dominio.groupby("decada")["vitorias"].idxmax()]
    ax = dominio.set_index("decada")["vitorias"].plot.bar(figsize=(10, 5)); salvar(ax.figure, "05_equipe_dominante_decada.png")
    fig, ax = plt.subplots(); dados["points"].plot.hist(bins=40, ax=ax); salvar(fig, "06_histograma_pontuacao.png")
    fig, ax = plt.subplots(); dados.boxplot(column="grid", ax=ax); salvar(fig, "07_boxplot_grid.png")
    fig, ax = plt.subplots(); dados.boxplot(column="points", ax=ax); salvar(fig, "08_boxplot_pontuacao.png")
    correlacao = dados[["grid", "position", "points"]].corr()
    fig, ax = plt.subplots(); imagem = ax.imshow(correlacao, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(3), correlacao.columns, rotation=30); ax.set_yticks(range(3), correlacao.index)
    fig.colorbar(imagem); salvar(fig, "09_matriz_correlacao.png")
    outliers = []
    for coluna in ["grid", "points"]:
        serie = dados[coluna].dropna(); q1, q3 = serie.quantile([0.25, 0.75]); iqr = q3 - q1
        quantidade = int(((serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)).sum())
        outliers.append({"atributo": coluna, "q1": q1, "q3": q3, "iqr": iqr, "valores_extremos": quantidade})
    pd.DataFrame(outliers).to_csv(RESULTADOS_DIR / "outliers_f1.csv", index=False)
    correlacao.to_csv(RESULTADOS_DIR / "correlacao_f1.csv")
    print("Análise exploratória F1 concluída; outliers contabilizados e preservados.")


if __name__ == "__main__":
    main()
