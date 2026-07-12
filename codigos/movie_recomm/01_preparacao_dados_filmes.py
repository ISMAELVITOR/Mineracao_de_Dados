"""Etapa 2 e início da Etapa 4: preparação do banco movie_recomm.

O script usa as tabelas movielens_movies e movielens_ratings, agrega as
avaliações por filme, cria variáveis discretizadas e gera uma transação por filme.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASES_DIR = PROJECT_ROOT / "BasesDeDados"
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "movie_recomm"

GENEROS_TRADUZIDOS = {
    "Action": "acao",
    "Adventure": "aventura",
    "Animation": "animacao",
    "Children": "infantil",
    "Comedy": "comedia",
    "Crime": "crime",
    "Documentary": "documentario",
    "Drama": "drama",
    "Fantasy": "fantasia",
    "Film-Noir": "film_noir",
    "Horror": "terror",
    "IMAX": "imax",
    "Musical": "musical",
    "Mystery": "misterio",
    "Romance": "romance",
    "Sci-Fi": "ficcao_cientifica",
    "Thriller": "suspense",
    "War": "guerra",
    "Western": "faroeste",
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepara os dados de filmes para mineração.")
    parser.add_argument("--db", type=Path, required=True, help="Caminho para movie_recomm.duckdb")
    parser.add_argument("--saida", type=Path, default=RESULTADOS_DIR)
    parser.add_argument(
        "--min-avaliacoes",
        type=int,
        default=5,
        help="Quantidade mínima de avaliações por filme (padrão: 5).",
    )
    return parser.parse_args()


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    """Salva em formato amigável ao Excel em português."""
    df.to_csv(caminho, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def normalizar_texto(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


def extrair_ano(titulo: pd.Series) -> pd.Series:
    return pd.to_numeric(titulo.str.extract(r"\((\d{4})\)\s*$", expand=False), errors="coerce")


def classificar_periodo(ano: float) -> str:
    if pd.isna(ano):
        return "periodo_desconhecido"
    ano_int = int(ano)
    if ano_int < 1950:
        return "periodo_antes_1950"
    if ano_int <= 1969:
        return "periodo_1950_1969"
    if ano_int <= 1989:
        return "periodo_1970_1989"
    if ano_int <= 1999:
        return "periodo_1990_1999"
    if ano_int <= 2009:
        return "periodo_2000_2009"
    return "periodo_2010_2018"


def genero_para_item(genero: str) -> str:
    nome = GENEROS_TRADUZIDOS.get(genero, genero.lower())
    nome = re.sub(r"[^a-z0-9_]+", "_", nome).strip("_")
    return f"genero_{nome}"


def criar_transacao(linha: pd.Series) -> list[str]:
    itens = [genero_para_item(g) for g in linha["lista_generos"]]
    itens.extend(
        [
            linha["periodo_lancamento"],
            linha["faixa_avaliacao"],
            linha["faixa_popularidade"],
        ]
    )
    return sorted(set(itens))


def main() -> int:
    args = argumentos()
    if not args.db.exists():
        print(f"Erro: banco não encontrado: {args.db}", file=sys.stderr)
        return 1
    if args.min_avaliacoes < 1:
        print("Erro: --min-avaliacoes deve ser maior que zero.", file=sys.stderr)
        return 1

    args.saida.mkdir(parents=True, exist_ok=True)

    try:
        con = duckdb.connect(str(args.db), read_only=True)
        tabelas = {linha[0] for linha in con.execute("SHOW TABLES").fetchall()}
        obrigatorias = {"movielens_movies", "movielens_ratings"}
        faltantes = obrigatorias - tabelas
        if faltantes:
            raise RuntimeError(f"Tabelas ausentes: {', '.join(sorted(faltantes))}")

        filmes = con.execute(
            'SELECT movieId, title, genres FROM movielens_movies ORDER BY movieId'
        ).df()
        avaliacoes = con.execute(
            'SELECT userId, movieId, rating, timestamp FROM movielens_ratings'
        ).df()
    except Exception as exc:
        print(f"Erro ao ler o banco: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            con.close()
        except Exception:
            pass

    # Conversão e normalização de tipos.
    filmes["movieId"] = pd.to_numeric(filmes["movieId"], errors="raise").astype("int64")
    filmes["title"] = normalizar_texto(filmes["title"])
    filmes["genres"] = normalizar_texto(filmes["genres"])

    avaliacoes["userId"] = pd.to_numeric(avaliacoes["userId"], errors="raise").astype("int64")
    avaliacoes["movieId"] = pd.to_numeric(avaliacoes["movieId"], errors="raise").astype("int64")
    avaliacoes["rating"] = pd.to_numeric(avaliacoes["rating"], errors="raise").astype("float64")
    avaliacoes["timestamp"] = pd.to_numeric(avaliacoes["timestamp"], errors="raise").astype("int64")
    avaliacoes["data_avaliacao"] = pd.to_datetime(
        avaliacoes["timestamp"], unit="s", utc=True, errors="coerce"
    )

    ids_filmes = set(filmes["movieId"])
    avaliacoes_orfas = int((~avaliacoes["movieId"].isin(ids_filmes)).sum())
    duplicatas_usuario_filme = int(avaliacoes.duplicated(["userId", "movieId"]).sum())

    filmes["ano_lancamento"] = extrair_ano(filmes["title"])
    filmes["lista_generos"] = filmes["genres"].str.split("|")

    agregadas = (
        avaliacoes.groupby("movieId", as_index=False)
        .agg(
            quantidade_avaliacoes=("rating", "size"),
            media_avaliacoes=("rating", "mean"),
            mediana_avaliacoes=("rating", "median"),
            desvio_padrao_avaliacoes=("rating", "std"),
            primeira_avaliacao=("data_avaliacao", "min"),
            ultima_avaliacao=("data_avaliacao", "max"),
        )
    )

    base_completa = filmes.merge(agregadas, on="movieId", how="left", validate="one_to_one")
    base_completa["quantidade_generos"] = base_completa["lista_generos"].str.len()

    preparados = base_completa.loc[
        (base_completa["quantidade_avaliacoes"] >= args.min_avaliacoes)
        & (base_completa["genres"] != "(no genres listed)")
    ].copy()

    preparados["quantidade_avaliacoes"] = preparados["quantidade_avaliacoes"].astype("int64")
    preparados["periodo_lancamento"] = preparados["ano_lancamento"].map(classificar_periodo)
    preparados["faixa_avaliacao"] = pd.cut(
        preparados["media_avaliacoes"],
        bins=[-np.inf, 3.0, 4.0, np.inf],
        right=False,
        labels=["avaliacao_baixa", "avaliacao_media", "avaliacao_alta"],
    ).astype("string")
    preparados["faixa_popularidade"] = pd.cut(
        preparados["quantidade_avaliacoes"],
        bins=[args.min_avaliacoes - 1, 9, 49, np.inf],
        right=True,
        labels=["popularidade_baixa", "popularidade_media", "popularidade_alta"],
    ).astype("string")
    preparados["generos_normalizados"] = preparados["lista_generos"].map(
        lambda generos: "|".join(genero_para_item(g) for g in generos)
    )

    transacoes = preparados[["movieId", "title"]].copy()
    transacoes["itens"] = preparados.apply(criar_transacao, axis=1)
    transacoes["transacao_json"] = transacoes["itens"].map(
        lambda itens: json.dumps(itens, ensure_ascii=False)
    )
    transacoes["quantidade_itens"] = transacoes["itens"].str.len()
    transacoes = transacoes.drop(columns="itens")

    relatorio = pd.DataFrame(
        [
            ("Filmes cadastrados", len(filmes), ""),
            ("Avaliações", len(avaliacoes), ""),
            ("Usuários distintos", avaliacoes["userId"].nunique(), ""),
            ("Filmes avaliados", avaliacoes["movieId"].nunique(), ""),
            ("Filmes sem avaliação", int(base_completa["quantidade_avaliacoes"].isna().sum()), "mantidos na auditoria"),
            ("Filmes sem gênero informado", int((filmes["genres"] == "(no genres listed)").sum()), "excluídos das transações"),
            ("Títulos sem ano final padrão", int(filmes["ano_lancamento"].isna().sum()), "nenhum permaneceu após o filtro"),
            ("Avaliações órfãs", avaliacoes_orfas, "esperado: 0"),
            ("Duplicatas usuário-filme", duplicatas_usuario_filme, "esperado: 0"),
            ("Títulos repetidos com IDs distintos", int(filmes.duplicated("title", keep=False).sum() / 2), "não removidos"),
            ("Filmes nas transações", len(preparados), f"mínimo de {args.min_avaliacoes} avaliações"),
            ("Itens médios por transação", round(transacoes["quantidade_itens"].mean(), 3), ""),
        ],
        columns=["Indicador", "Valor", "Observacao"],
    )

    # Versão tabular sem objetos Python.
    colunas_saida = [
        "movieId",
        "title",
        "genres",
        "ano_lancamento",
        "quantidade_avaliacoes",
        "media_avaliacoes",
        "mediana_avaliacoes",
        "desvio_padrao_avaliacoes",
        "primeira_avaliacao",
        "ultima_avaliacao",
        "quantidade_generos",
        "periodo_lancamento",
        "faixa_avaliacao",
        "faixa_popularidade",
        "generos_normalizados",
    ]
    filmes_saida = preparados[colunas_saida].sort_values("movieId")

    salvar_csv(filmes_saida, args.saida / "filmes_preparados.csv")
    salvar_csv(transacoes, args.saida / "transacoes_filmes.csv")
    salvar_csv(relatorio, args.saida / "relatorio_qualidade_dados.csv")

    resumo = {
        "banco": str(args.db),
        "tabelas_utilizadas": ["movielens_movies", "movielens_ratings"],
        "minimo_avaliacoes": args.min_avaliacoes,
        "filmes_cadastrados": int(len(filmes)),
        "avaliacoes": int(len(avaliacoes)),
        "usuarios": int(avaliacoes["userId"].nunique()),
        "filmes_preparados": int(len(preparados)),
        "transacoes": int(len(transacoes)),
    }
    (args.saida / "resumo_preparacao.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=" * 72)
    print("PREPARAÇÃO DO BANCO MOVIE_RECOMM CONCLUÍDA")
    print("=" * 72)
    print(relatorio.to_string(index=False))
    print(f"\nArquivos salvos em: {args.saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
