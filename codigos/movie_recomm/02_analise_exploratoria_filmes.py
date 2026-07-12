"""Etapa 3: caracterização exploratória do banco movie_recomm."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "movie_recomm"

ROTULOS_GENEROS = {
    "genero_acao": "Ação",
    "genero_aventura": "Aventura",
    "genero_animacao": "Animação",
    "genero_infantil": "Infantil",
    "genero_comedia": "Comédia",
    "genero_crime": "Crime",
    "genero_documentario": "Documentário",
    "genero_drama": "Drama",
    "genero_fantasia": "Fantasia",
    "genero_film_noir": "Film noir",
    "genero_terror": "Terror",
    "genero_imax": "IMAX",
    "genero_musical": "Musical",
    "genero_misterio": "Mistério",
    "genero_romance": "Romance",
    "genero_ficcao_cientifica": "Ficção científica",
    "genero_suspense": "Suspense",
    "genero_guerra": "Guerra",
    "genero_faroeste": "Faroeste",
}

ROTULOS_PERIODOS = {
    "periodo_antes_1950": "Antes de 1950",
    "periodo_1950_1969": "1950–1969",
    "periodo_1970_1989": "1970–1989",
    "periodo_1990_1999": "1990–1999",
    "periodo_2000_2009": "2000–2009",
    "periodo_2010_2018": "2010–2018",
    "periodo_desconhecido": "Desconhecido",
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera a análise exploratória de filmes.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--dados", type=Path, required=True, help="filmes_preparados.csv")
    parser.add_argument("--saida", type=Path, default=RESULTADOS_DIR / "graficos")
    return parser.parse_args()


def ler_csv(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    df.to_csv(caminho, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def salvar_figura(caminho: Path) -> None:
    plt.tight_layout()
    plt.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close()


def main() -> int:
    args = argumentos()
    if not args.db.exists() or not args.dados.exists():
        print("Erro: banco ou arquivo de dados não encontrado.", file=sys.stderr)
        return 1
    args.saida.mkdir(parents=True, exist_ok=True)

    dados = ler_csv(args.dados)
    for coluna in [
        "ano_lancamento",
        "quantidade_avaliacoes",
        "media_avaliacoes",
        "mediana_avaliacoes",
        "desvio_padrao_avaliacoes",
        "quantidade_generos",
    ]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    con = duckdb.connect(str(args.db), read_only=True)
    avaliacoes = con.execute("SELECT rating FROM movielens_ratings").df()
    con.close()

    estatisticas_avaliacoes = avaliacoes["rating"].describe().rename("Valor").reset_index()
    estatisticas_avaliacoes.columns = ["Estatistica", "Valor"]
    salvar_csv(estatisticas_avaliacoes, args.saida / "estatisticas_avaliacoes.csv")

    numericas = [
        "ano_lancamento",
        "quantidade_avaliacoes",
        "media_avaliacoes",
        "mediana_avaliacoes",
        "desvio_padrao_avaliacoes",
        "quantidade_generos",
    ]
    estatisticas_filmes = dados[numericas].describe().T.reset_index().rename(columns={"index": "Variavel"})
    salvar_csv(estatisticas_filmes, args.saida / "estatisticas_filmes_preparados.csv")

    # Valores ausentes.
    ausentes = pd.DataFrame(
        {
            "Atributo": dados.columns,
            "Valores_ausentes": [int(dados[c].isna().sum()) for c in dados.columns],
            "Percentual": [round(100 * dados[c].isna().mean(), 4) for c in dados.columns],
        }
    ).sort_values(["Valores_ausentes", "Atributo"], ascending=[False, True])
    salvar_csv(ausentes, args.saida / "valores_ausentes.csv")

    # Frequência das notas.
    freq_notas = (
        avaliacoes["rating"].value_counts().sort_index().rename_axis("Nota").reset_index(name="Frequencia")
    )
    freq_notas["Percentual"] = 100 * freq_notas["Frequencia"] / freq_notas["Frequencia"].sum()
    salvar_csv(freq_notas, args.saida / "frequencia_notas.csv")

    plt.figure(figsize=(9, 5))
    plt.bar(freq_notas["Nota"].astype(str), freq_notas["Frequencia"])
    plt.title("Distribuição das avaliações do MovieLens")
    plt.xlabel("Nota")
    plt.ylabel("Frequência")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "01_distribuicao_notas.png")

    plt.figure(figsize=(9, 5))
    plt.hist(dados["media_avaliacoes"].dropna(), bins=20, edgecolor="black")
    plt.title("Distribuição da avaliação média por filme")
    plt.xlabel("Avaliação média")
    plt.ylabel("Quantidade de filmes")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "02_histograma_media_avaliacoes.png")

    plt.figure(figsize=(9, 5))
    plt.hist(dados["quantidade_avaliacoes"].dropna(), bins=35, edgecolor="black")
    plt.title("Distribuição da popularidade dos filmes")
    plt.xlabel("Quantidade de avaliações")
    plt.ylabel("Quantidade de filmes")
    plt.yscale("log")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "03_histograma_quantidade_avaliacoes.png")

    plt.figure(figsize=(7, 5))
    plt.boxplot(dados["media_avaliacoes"].dropna(), orientation="vertical")
    plt.xticks([])
    plt.title("Boxplot da avaliação média por filme")
    plt.ylabel("Avaliação média")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "04_boxplot_media_avaliacoes.png")

    plt.figure(figsize=(7, 5))
    plt.boxplot(dados["quantidade_avaliacoes"].dropna(), orientation="vertical")
    plt.xticks([])
    plt.title("Boxplot da quantidade de avaliações por filme")
    plt.ylabel("Quantidade de avaliações")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "05_boxplot_quantidade_avaliacoes.png")

    # Gêneros.
    contador = Counter()
    for valor in dados["generos_normalizados"].dropna():
        contador.update(str(valor).split("|"))
    frequencia_generos = pd.DataFrame(contador.items(), columns=["Genero", "Quantidade"]).sort_values(
        "Quantidade", ascending=False
    )
    frequencia_generos["Percentual_filmes"] = 100 * frequencia_generos["Quantidade"] / len(dados)
    frequencia_generos["Rotulo"] = frequencia_generos["Genero"].map(ROTULOS_GENEROS).fillna(
        frequencia_generos["Genero"]
    )
    salvar_csv(frequencia_generos, args.saida / "frequencia_generos.csv")

    top_generos = frequencia_generos.head(15).sort_values("Quantidade")
    plt.figure(figsize=(10, 7))
    plt.barh(top_generos["Rotulo"], top_generos["Quantidade"])
    plt.title("Gêneros mais frequentes entre os filmes preparados")
    plt.xlabel("Quantidade de filmes")
    plt.grid(axis="x", alpha=0.25)
    salvar_figura(args.saida / "06_generos_mais_frequentes.png")

    # Períodos.
    ordem_periodos = list(ROTULOS_PERIODOS)
    freq_periodos = dados["periodo_lancamento"].value_counts().reindex(ordem_periodos, fill_value=0)
    freq_periodos_df = freq_periodos.rename_axis("Periodo").reset_index(name="Quantidade")
    freq_periodos_df["Rotulo"] = freq_periodos_df["Periodo"].map(ROTULOS_PERIODOS)
    freq_periodos_df["Percentual"] = 100 * freq_periodos_df["Quantidade"] / len(dados)
    salvar_csv(freq_periodos_df, args.saida / "frequencia_periodos.csv")

    plt.figure(figsize=(10, 5))
    plt.bar(freq_periodos_df["Rotulo"], freq_periodos_df["Quantidade"])
    plt.title("Filmes preparados por período de lançamento")
    plt.xlabel("Período")
    plt.ylabel("Quantidade de filmes")
    plt.xticks(rotation=25, ha="right")
    plt.grid(axis="y", alpha=0.25)
    salvar_figura(args.saida / "07_filmes_por_periodo.png")

    # Faixas de avaliação e popularidade.
    configuracoes_faixas = [
        (
            "faixa_avaliacao",
            ["avaliacao_baixa", "avaliacao_media", "avaliacao_alta"],
            {
                "avaliacao_baixa": "Baixa (< 3,0)",
                "avaliacao_media": "Intermediária (3,0–3,99)",
                "avaliacao_alta": "Alta (≥ 4,0)",
            },
            "Filmes por faixa de avaliação média",
            "08_faixas_avaliacao.png",
        ),
        (
            "faixa_popularidade",
            ["popularidade_baixa", "popularidade_media", "popularidade_alta"],
            {
                "popularidade_baixa": "Baixa (5–9)",
                "popularidade_media": "Intermediária (10–49)",
                "popularidade_alta": "Alta (≥ 50)",
            },
            "Filmes por faixa de popularidade",
            "09_faixas_popularidade.png",
        ),
    ]
    for coluna, ordem, rotulos, titulo, arquivo in configuracoes_faixas:
        freq = dados[coluna].value_counts().reindex(ordem, fill_value=0)
        tabela = freq.rename_axis("Faixa").reset_index(name="Quantidade")
        tabela["Rotulo"] = tabela["Faixa"].map(rotulos)
        tabela["Percentual"] = 100 * tabela["Quantidade"] / len(dados)
        salvar_csv(tabela, args.saida / f"frequencia_{coluna}.csv")
        # As frequências alimentam a análise, mas estes dois gráficos foram
        # descartados da versão final do relatório.

    # Correlação.
    correlacao = dados[numericas].corr(numeric_only=True)
    correlacao_saida = correlacao.reset_index().rename(columns={"index": "Variavel"})
    salvar_csv(correlacao_saida, args.saida / "matriz_correlacao.csv")

    rotulos_numericas = [
        "Ano de lançamento",
        "Quantidade de avaliações",
        "Média",
        "Mediana",
        "Desvio-padrão",
        "Quantidade de gêneros",
    ]
    plt.figure(figsize=(10, 8))
    imagem = plt.imshow(correlacao, vmin=-1, vmax=1)
    plt.colorbar(imagem, label="Correlação")
    plt.xticks(range(len(numericas)), rotulos_numericas, rotation=45, ha="right")
    plt.yticks(range(len(numericas)), rotulos_numericas)
    for i in range(len(numericas)):
        for j in range(len(numericas)):
            plt.text(j, i, f"{correlacao.iloc[i, j]:.2f}", ha="center", va="center")
    plt.title("Matriz de correlação das variáveis numéricas")
    salvar_figura(args.saida / "10_matriz_correlacao.png")

    # Outliers pelo intervalo interquartil.
    linhas_outliers = []
    for coluna in ["quantidade_avaliacoes", "media_avaliacoes", "desvio_padrao_avaliacoes"]:
        serie = dados[coluna].dropna()
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        quantidade = int(((serie < limite_inferior) | (serie > limite_superior)).sum())
        linhas_outliers.append(
            {
                "Variavel": coluna,
                "Q1": q1,
                "Q3": q3,
                "IQR": iqr,
                "Limite_inferior": limite_inferior,
                "Limite_superior": limite_superior,
                "Quantidade_outliers": quantidade,
                "Percentual": 100 * quantidade / len(serie),
            }
        )
    outliers = pd.DataFrame(linhas_outliers)
    salvar_csv(outliers, args.saida / "relatorio_outliers.csv")

    resumo = {
        "filmes_preparados": int(len(dados)),
        "media_geral_avaliacoes_individuais": float(avaliacoes["rating"].mean()),
        "mediana_avaliacoes_individuais": float(avaliacoes["rating"].median()),
        "desvio_padrao_avaliacoes_individuais": float(avaliacoes["rating"].std()),
        "generos_mais_frequentes": frequencia_generos.head(5)[["Rotulo", "Quantidade"]].to_dict("records"),
        "outliers": outliers[["Variavel", "Quantidade_outliers"]].to_dict("records"),
    }
    (args.saida / "resumo_eda.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=" * 72)
    print("ANÁLISE EXPLORATÓRIA CONCLUÍDA")
    print("=" * 72)
    print(estatisticas_avaliacoes.to_string(index=False))
    print("\nGêneros mais frequentes:")
    print(frequencia_generos.head(10)[["Rotulo", "Quantidade", "Percentual_filmes"]].to_string(index=False))
    print("\nOutliers pelo IQR:")
    print(outliers.to_string(index=False))
    print(f"\nArquivos salvos em: {args.saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
