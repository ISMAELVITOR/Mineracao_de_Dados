from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent

ARQUIVOS = {
    "F1 selecionadas": {
        "caminho": ROOT / "resultados" / "f1" / "regras_f1_selecionadas.csv",
        "quantidade": 15,
        "banco": "f1",
    },
    "Filmes selecionadas": {
        "caminho": (
            ROOT
            / "resultados"
            / "movie_recomm"
            / "regras_movie_recomm_selecionadas.csv"
        ),
        "quantidade": 30,
        "banco": "movie_recomm",
    },
    "Consolidado": {
        "caminho": ROOT / "resultados" / "regras_finais_trabalho.csv",
        "quantidade": 45,
        "banco": None,
    },
}

COLUNAS_OBRIGATORIAS = {
    "banco",
    "experimento",
    "numero",
    "antecedente",
    "consequente",
    "suporte",
    "confianca",
    "lift",
    "pergunta",
    "resposta",
    "analise_critica",
}


def ler_csv(caminho: Path) -> pd.DataFrame:
    """
    Detecta automaticamente vírgula ou ponto e vírgula como separador.
    """
    try:
        return pd.read_csv(
            caminho,
            encoding="utf-8-sig",
            sep=None,
            engine="python",
        )
    except UnicodeDecodeError:
        return pd.read_csv(
            caminho,
            encoding="latin-1",
            sep=None,
            engine="python",
        )


def verificar_vazios(df: pd.DataFrame, coluna: str) -> int:
    if coluna not in df.columns:
        return 0

    serie = df[coluna]

    return int(
        (
            serie.isna()
            | serie.astype(str).str.strip().eq("")
            | serie.astype(str).str.lower().eq("nan")
        ).sum()
    )


def main() -> None:
    print("=" * 72)
    print("VALIDAÇÃO DA ENTREGA")
    print("=" * 72)
    print(f"Raiz do projeto: {ROOT}")

    houve_erro = False
    dataframes: dict[str, pd.DataFrame] = {}

    for nome, configuracao in ARQUIVOS.items():
        caminho = configuracao["caminho"]
        esperado = configuracao["quantidade"]

        print("\n" + "-" * 72)
        print(nome)
        print("-" * 72)
        print(f"Arquivo: {caminho}")

        if not caminho.exists():
            print("[ERRO] Arquivo não encontrado.")
            houve_erro = True
            continue

        try:
            df = ler_csv(caminho)
            dataframes[nome] = df
        except Exception as erro:
            print(f"[ERRO] Não foi possível ler o CSV: {erro}")
            houve_erro = True
            continue

        print(f"Linhas encontradas: {len(df)}")
        print(f"Linhas esperadas:   {esperado}")
        print(f"Colunas: {list(df.columns)}")

        if len(df) != esperado:
            print(
                f"[ERRO] Quantidade incorreta: esperado {esperado}, "
                f"obtido {len(df)}."
            )
            houve_erro = True
        else:
            print("[OK] Quantidade de linhas correta.")

    consolidado = dataframes.get("Consolidado")

    if consolidado is not None:
        print("\n" + "=" * 72)
        print("VALIDAÇÃO DO CSV CONSOLIDADO")
        print("=" * 72)

        colunas_ausentes = COLUNAS_OBRIGATORIAS - set(consolidado.columns)

        if colunas_ausentes:
            print(
                "[ERRO] Colunas obrigatórias ausentes: "
                f"{sorted(colunas_ausentes)}"
            )
            houve_erro = True
        else:
            print("[OK] Todas as colunas obrigatórias estão presentes.")

        colunas_textuais = [
            "banco",
            "experimento",
            "antecedente",
            "consequente",
            "pergunta",
            "resposta",
            "analise_critica",
        ]

        for coluna in colunas_textuais:
            vazios = verificar_vazios(consolidado, coluna)

            if vazios:
                print(f"[ERRO] Coluna '{coluna}': {vazios} valores vazios.")
                houve_erro = True
            elif coluna in consolidado.columns:
                print(f"[OK] Coluna '{coluna}' sem valores vazios.")

        if "banco" in consolidado.columns:
            distribuicao = (
                consolidado["banco"]
                .astype(str)
                .str.strip()
                .str.lower()
                .value_counts()
            )

            print("\nDistribuição por banco:")
            print(distribuicao.to_string())

            quantidade_f1 = int(
                distribuicao[
                    distribuicao.index.str.contains(
                        r"^f1$|formula|fórmula",
                        regex=True,
                    )
                ].sum()
            )

            quantidade_filmes = int(
                distribuicao[
                    distribuicao.index.str.contains(
                        r"movie|filme",
                        regex=True,
                    )
                ].sum()
            )

            if quantidade_f1 != 15:
                print(
                    f"[ERRO] Esperadas 15 regras da F1; "
                    f"encontradas {quantidade_f1}."
                )
                houve_erro = True
            else:
                print("[OK] Foram encontradas 15 regras da F1.")

            if quantidade_filmes != 30:
                print(
                    f"[ERRO] Esperadas 30 regras de filmes; "
                    f"encontradas {quantidade_filmes}."
                )
                houve_erro = True
            else:
                print("[OK] Foram encontradas 30 regras de filmes.")

        colunas_numericas = ["suporte", "confianca", "lift"]

        for coluna in colunas_numericas:
            if coluna not in consolidado.columns:
                continue

            valores = pd.to_numeric(
                consolidado[coluna],
                errors="coerce",
            )

            invalidos = int(valores.isna().sum())

            if invalidos:
                print(
                    f"[ERRO] Coluna '{coluna}': "
                    f"{invalidos} valores não numéricos."
                )
                houve_erro = True
            else:
                print(f"[OK] Coluna '{coluna}' contém valores numéricos.")

        chaves_duplicidade = [
            "banco",
            "experimento",
            "antecedente",
            "consequente",
        ]

        if all(coluna in consolidado.columns for coluna in chaves_duplicidade):
            duplicadas = int(
                consolidado.duplicated(
                    subset=chaves_duplicidade,
                    keep=False,
                ).sum()
            )

            if duplicadas:
                print(
                    f"[ERRO] Foram encontradas {duplicadas} linhas "
                    "envolvidas em regras duplicadas."
                )
                houve_erro = True
            else:
                print("[OK] Não foram encontradas regras duplicadas.")

    print("\n" + "=" * 72)

    if houve_erro:
        print("RESULTADO: VALIDAÇÃO CONCLUÍDA COM ERROS.")
        print("=" * 72)
        raise SystemExit(1)

    print("RESULTADO: VALIDAÇÃO CONCLUÍDA SEM ERROS.")
    print("=" * 72)


if __name__ == "__main__":
    main()