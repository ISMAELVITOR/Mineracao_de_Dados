"""Etapas 4, 5 e 6: modelagem, extração e análise de regras de associação."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "movie_recomm"

ROTULOS = {
    "genero_acao": "gênero ação",
    "genero_aventura": "gênero aventura",
    "genero_animacao": "gênero animação",
    "genero_infantil": "gênero infantil",
    "genero_comedia": "gênero comédia",
    "genero_crime": "gênero crime",
    "genero_documentario": "gênero documentário",
    "genero_drama": "gênero drama",
    "genero_fantasia": "gênero fantasia",
    "genero_film_noir": "gênero film noir",
    "genero_terror": "gênero terror",
    "genero_imax": "formato IMAX",
    "genero_musical": "gênero musical",
    "genero_misterio": "gênero mistério",
    "genero_romance": "gênero romance",
    "genero_ficcao_cientifica": "gênero ficção científica",
    "genero_suspense": "gênero suspense",
    "genero_guerra": "gênero guerra",
    "genero_faroeste": "gênero faroeste",
    "periodo_antes_1950": "lançamento antes de 1950",
    "periodo_1950_1969": "lançamento entre 1950 e 1969",
    "periodo_1970_1989": "lançamento entre 1970 e 1989",
    "periodo_1990_1999": "lançamento entre 1990 e 1999",
    "periodo_2000_2009": "lançamento entre 2000 e 2009",
    "periodo_2010_2018": "lançamento entre 2010 e 2018",
    "avaliacao_baixa": "avaliação média baixa (menor que 3,0)",
    "avaliacao_media": "avaliação média intermediária (de 3,0 a menos de 4,0)",
    "avaliacao_alta": "avaliação média alta (igual ou superior a 4,0)",
    "popularidade_baixa": "popularidade baixa (5 a 9 avaliações)",
    "popularidade_media": "popularidade intermediária (10 a 49 avaliações)",
    "popularidade_alta": "popularidade alta (50 ou mais avaliações)",
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrai regras de associação entre filmes.")
    parser.add_argument("--transacoes", type=Path, required=True)
    parser.add_argument("--saida", type=Path, default=RESULTADOS_DIR / "regras")
    parser.add_argument("--suporte", type=float, default=0.02)
    parser.add_argument("--confianca", type=float, default=0.55)
    parser.add_argument("--lift", type=float, default=1.10)
    parser.add_argument("--max-len", type=int, default=4)
    parser.add_argument("--max-antecedente", type=int, default=2)
    parser.add_argument("--ganho-redundancia", type=float, default=0.05)
    return parser.parse_args()


def ler_csv(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    df.to_csv(caminho, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def formatar_conjunto(conjunto: frozenset[str]) -> str:
    return "{" + ", ".join(sorted(conjunto)) + "}"


def descrever_itens(conjunto: frozenset[str]) -> str:
    descricoes = [ROTULOS.get(item, item.replace("_", " ")) for item in sorted(conjunto)]
    if len(descricoes) == 1:
        return descricoes[0]
    if len(descricoes) == 2:
        return f"{descricoes[0]} e {descricoes[1]}"
    return ", ".join(descricoes[:-1]) + f" e {descricoes[-1]}"


def classificar_forca(lift: float) -> str:
    if lift >= 3:
        return "forte"
    if lift >= 1.5:
        return "moderada"
    return "positiva, porém modesta"


def classificar_suporte(suporte: float) -> str:
    if suporte >= 0.10:
        return "alto"
    if suporte >= 0.04:
        return "intermediário"
    return "baixo"


def criar_textos(linha: pd.Series) -> pd.Series:
    antecedente = descrever_itens(linha["antecedents"])
    consequente = descrever_itens(linha["consequents"])
    suporte = float(linha["support"])
    confianca = float(linha["confidence"])
    lift = float(linha["lift"])
    forca = classificar_forca(lift)
    suporte_classe = classificar_suporte(suporte)

    pergunta = (
        f"Quando um filme apresenta {antecedente}, com que frequência ele também apresenta {consequente}?"
    )
    resposta = (
        f"Na amostra, {confianca:.2%} dos filmes com {antecedente} também apresentam {consequente}. "
        f"A regra ocorre em {suporte:.2%} de todos os filmes e possui lift {lift:.2f}, "
        f"indicando uma associação {forca}."
    )
    analise = (
        f"O suporte é {suporte_classe} para esta base. A confiança mostra a proporção condicional, "
        "enquanto o lift compara a coocorrência com o que seria esperado pelas frequências individuais. "
        "A regra descreve associação, não causalidade, e pode refletir convenções de classificação de gêneros, "
        "o recorte temporal e o filtro de filmes com pelo menos cinco avaliações."
    )
    esperada = "esperada" if lift < 2 else "interessante ou parcialmente surpreendente"
    utilidade = (
        "útil para descrever combinações recorrentes e apoiar análises de catálogo; não deve ser usada isoladamente para recomendar filmes"
    )
    return pd.Series(
        {
            "Pergunta": pergunta,
            "Resposta": resposta,
            "Classificacao": esperada,
            "Analise_critica": analise,
            "Utilidade": utilidade,
        }
    )


def remover_regras_redundantes(regras: pd.DataFrame, ganho_minimo: float) -> pd.DataFrame:
    """Remove extensões de antecedente que quase não aumentam a confiança.

    Uma regra com dois itens no antecedente é redundante quando existe uma regra
    com um único item, mesmo consequente, e o ganho de confiança é menor que o
    limite informado.
    """
    remover: list[int] = []
    for indice, regra in regras.iterrows():
        antecedente = regra["antecedents"]
        if len(antecedente) != 2:
            continue
        confiancas_subconjuntos: list[float] = []
        for item in antecedente:
            correspondentes = regras.loc[
                (regras["antecedents"] == frozenset([item]))
                & (regras["consequents"] == regra["consequents"]),
                "confidence",
            ]
            confiancas_subconjuntos.extend(correspondentes.tolist())
        if confiancas_subconjuntos:
            ganho = float(regra["confidence"]) - max(confiancas_subconjuntos)
            if ganho < ganho_minimo:
                remover.append(indice)
    return regras.drop(index=remover).copy()


def selecionar_top_30(regras: pd.DataFrame) -> pd.DataFrame:
    """Seleciona regras fortes, preservando alguma diversidade de consequentes."""
    regras = regras.copy()
    regras["pontuacao"] = (
        regras["lift"].clip(upper=8) * 0.45
        + regras["confidence"] * 3.0
        + regras["support"] * 5.0
    )
    regras = regras.sort_values(
        ["pontuacao", "lift", "confidence", "support"], ascending=False
    )

    escolhidas: list[int] = []
    por_consequente: dict[str, int] = {}
    # Primeira passagem: no máximo quatro regras por consequente.
    for indice, linha in regras.iterrows():
        consequente = formatar_conjunto(linha["consequents"])
        if por_consequente.get(consequente, 0) >= 4:
            continue
        escolhidas.append(indice)
        por_consequente[consequente] = por_consequente.get(consequente, 0) + 1
        if len(escolhidas) == 30:
            break
    # Completa caso a limitação de diversidade seja restritiva demais.
    if len(escolhidas) < 30:
        for indice in regras.index:
            if indice not in escolhidas:
                escolhidas.append(indice)
            if len(escolhidas) == 30:
                break
    return regras.loc[escolhidas].drop(columns="pontuacao")


def main() -> int:
    args = argumentos()
    if not args.transacoes.exists():
        print(f"Erro: arquivo não encontrado: {args.transacoes}", file=sys.stderr)
        return 1
    if not (0 < args.suporte <= 1 and 0 < args.confianca <= 1 and args.lift > 0):
        print("Erro: parâmetros inválidos.", file=sys.stderr)
        return 1
    args.saida.mkdir(parents=True, exist_ok=True)

    tabela = ler_csv(args.transacoes)
    try:
        transacoes = [json.loads(valor) for valor in tabela["transacao_json"]]
    except (KeyError, json.JSONDecodeError, TypeError) as exc:
        print(f"Erro ao interpretar as transações: {exc}", file=sys.stderr)
        return 1

    encoder = TransactionEncoder()
    matriz = encoder.fit(transacoes).transform(transacoes)
    matriz_binaria = pd.DataFrame(matriz, columns=encoder.columns_)

    testes = []
    for suporte in [0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005]:
        itemsets_teste = fpgrowth(
            matriz_binaria, min_support=suporte, use_colnames=True, max_len=args.max_len
        )
        if itemsets_teste.empty:
            quantidade_regras = 0
        else:
            regras_teste = association_rules(
                itemsets_teste, metric="confidence", min_threshold=args.confianca
            )
            regras_teste = regras_teste.loc[
                (regras_teste["lift"] >= args.lift)
                & (regras_teste["antecedents"].map(len) <= args.max_antecedente)
                & (regras_teste["consequents"].map(len) == 1)
            ]
            quantidade_regras = len(regras_teste)
        testes.append(
            {
                "Suporte_minimo": suporte,
                "Itemsets_frequentes": len(itemsets_teste),
                "Regras_filtradas": quantidade_regras,
            }
        )
    salvar_csv(pd.DataFrame(testes), args.saida / "teste_parametros.csv")

    itemsets = fpgrowth(
        matriz_binaria,
        min_support=args.suporte,
        use_colnames=True,
        max_len=args.max_len,
    ).sort_values(["support"], ascending=False)

    regras = association_rules(itemsets, metric="confidence", min_threshold=args.confianca)
    regras = regras.loc[
        (regras["lift"] >= args.lift)
        & (regras["antecedents"].map(len) <= args.max_antecedente)
        & (regras["consequents"].map(len) == 1)
    ].copy()
    regras = regras.sort_values(["lift", "confidence", "support"], ascending=False)
    regras_nao_redundantes = remover_regras_redundantes(regras, args.ganho_redundancia)
    regras_nao_redundantes = regras_nao_redundantes.sort_values(
        ["lift", "confidence", "support"], ascending=False
    )
    top_30 = selecionar_top_30(regras_nao_redundantes)

    # Colunas legíveis.
    def preparar_saida(df: pd.DataFrame, incluir_textos: bool = True) -> pd.DataFrame:
        saida = df.copy()
        saida["Antecedente"] = saida["antecedents"].map(formatar_conjunto)
        saida["Consequente"] = saida["consequents"].map(formatar_conjunto)
        saida["Suporte"] = saida["support"]
        saida["Confianca"] = saida["confidence"]
        saida["Lift"] = saida["lift"]
        saida["Quantidade_antecedente"] = saida["antecedents"].map(len)
        if incluir_textos:
            textos = saida.apply(criar_textos, axis=1)
            saida = pd.concat([saida, textos], axis=1)
        colunas = [
            "Antecedente",
            "Consequente",
            "Suporte",
            "Confianca",
            "Lift",
            "Quantidade_antecedente",
        ]
        if incluir_textos:
            colunas += ["Pergunta", "Resposta", "Classificacao", "Analise_critica", "Utilidade"]
        return saida[colunas]

    itemsets_saida = itemsets.copy()
    itemsets_saida["Itemsets"] = itemsets_saida["itemsets"].map(formatar_conjunto)
    itemsets_saida["Quantidade_itens"] = itemsets_saida["itemsets"].map(len)
    itemsets_saida = itemsets_saida.rename(columns={"support": "Suporte"})[
        ["Itemsets", "Suporte", "Quantidade_itens"]
    ]

    completas_saida = preparar_saida(regras)
    nao_redundantes_saida = preparar_saida(regras_nao_redundantes)
    top_30_saida = preparar_saida(top_30).reset_index(drop=True)
    top_30_saida.insert(0, "Numero", range(1, len(top_30_saida) + 1))

    salvar_csv(itemsets_saida, args.saida / "itemsets_frequentes.csv")
    salvar_csv(completas_saida, args.saida / "regras_associacao_completas.csv")
    completas_saida.to_csv(args.saida.parent / "regras_movie_recomm.csv", index=False, encoding="utf-8")
    salvar_csv(nao_redundantes_saida, args.saida / "regras_nao_redundantes.csv")
    salvar_csv(top_30_saida, args.saida / "top_30_perguntas_respostas.csv")

    resumo = pd.DataFrame(
        [
            ("Algoritmo", "FP-Growth"),
            ("Transações", len(transacoes)),
            ("Itens distintos", len(matriz_binaria.columns)),
            ("Suporte mínimo", args.suporte),
            ("Confiança mínima", args.confianca),
            ("Lift mínimo", args.lift),
            ("Tamanho máximo do itemset", args.max_len),
            ("Máximo de itens no antecedente", args.max_antecedente),
            ("Itemsets frequentes", len(itemsets)),
            ("Regras após filtros", len(regras)),
            ("Regras não redundantes", len(regras_nao_redundantes)),
            ("Regras selecionadas", len(top_30_saida)),
            ("Ocorrências mínimas aproximadas", math.ceil(args.suporte * len(transacoes))),
        ],
        columns=["Parametro", "Valor"],
    )
    salvar_csv(resumo, args.saida / "parametros_e_resumo.csv")

    # Texto-base para inserir no relatório.
    linhas = [
        "# Resultados das regras de associação — movie_recomm",
        "",
        f"Foram utilizadas {len(transacoes)} transações, uma por filme.",
        f"O FP-Growth encontrou {len(itemsets)} itemsets frequentes.",
        f"Após os filtros de suporte, confiança, lift, tamanho de antecedente e consequente unitário, permaneceram {len(regras)} regras.",
        f"A remoção de extensões redundantes resultou em {len(regras_nao_redundantes)} regras, das quais 30 foram selecionadas para perguntas e respostas.",
        "",
        "## Trinta perguntas e respostas",
        "",
    ]
    for _, linha in top_30_saida.iterrows():
        linhas.extend(
            [
                f"### {int(linha['Numero'])}. {linha['Antecedente']} → {linha['Consequente']}",
                "",
                f"**Pergunta:** {linha['Pergunta']}",
                "",
                f"**Resposta:** {linha['Resposta']}",
                "",
                f"**Análise crítica:** {linha['Analise_critica']}",
                "",
            ]
        )
    (args.saida / "texto_resultados_regras.md").write_text("\n".join(linhas), encoding="utf-8")

    print("=" * 72)
    print("REGRAS DE ASSOCIAÇÃO CONCLUÍDAS")
    print("=" * 72)
    print(resumo.to_string(index=False))
    print("\nCinco primeiras regras selecionadas:")
    print(
        top_30_saida[["Numero", "Antecedente", "Consequente", "Suporte", "Confianca", "Lift"]]
        .head()
        .to_string(index=False)
    )
    print(f"\nArquivos salvos em: {args.saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
