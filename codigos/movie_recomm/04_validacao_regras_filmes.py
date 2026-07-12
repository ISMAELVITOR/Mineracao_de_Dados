"""Valida, filtra e documenta as regras finais da base movie_recomm.

Esta etapa é executada após 03_regras_associacao_filmes.py. Ela:
- elimina associações finais de lift fraco;
- separa regras semanticamente óbvias;
- remove direções alternativas da mesma combinação de itens;
- valida suporte, confiança e lift diretamente nas transações;
- seleciona 30 regras diversas;
- gera perguntas, respostas e discussões críticas específicas;
- salva a lista final e o arquivo de auditoria dos descartes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "movie_recomm"
LIFT_RELEVANCIA = 1.30

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

REGRAS_OBVIAS = {
    (frozenset(["genero_animacao"]), frozenset(["genero_infantil"])):
        "Associação direta entre rótulos editoriais fortemente sobrepostos; correta, mas pouco informativa.",
    (frozenset(["genero_misterio"]), frozenset(["genero_suspense"])):
        "Proximidade temática muito conhecida entre os gêneros; útil como validação, mas pouco nova.",
    (frozenset(["genero_guerra"]), frozenset(["genero_drama"])):
        "Combinação convencional de classificação cinematográfica, com baixo ganho interpretativo.",
    (frozenset(["genero_romance"]), frozenset(["genero_comedia"])):
        "A categoria comédia romântica torna a associação previsível e pouco específica.",
    (frozenset(["genero_romance"]), frozenset(["genero_drama"])):
        "Sobreposição temática comum; a regra é esperada e pouco discriminante.",
    (frozenset(["genero_infantil"]), frozenset(["genero_comedia"])):
        "Coocorrência editorial frequente e ampla, com baixa novidade para a análise.",
}

# Avaliações específicas para as 30 regras geradas pelo conjunto atual.
# Quando uma regra não estiver no dicionário, o código usa uma análise genérica conservadora.
ANALISES = {
    ("{avaliacao_media, genero_infantil}", "{genero_animacao}"):
        ("parcialmente esperada", "Dentro dos filmes infantis com avaliação intermediária, a animação é muito mais comum do que no catálogo geral. O lift elevado também reflete a baixa frequência global de animação; a regra descreve a estrutura de classificação, não um efeito da avaliação."),
    ("{genero_aventura, genero_infantil}", "{genero_animacao}"):
        ("parcialmente esperada", "Filmes que combinam aventura e conteúdo infantil frequentemente são animações. Parte da força decorre da sobreposição editorial dos gêneros, portanto o resultado é um padrão de catálogo, não causal."),
    ("{genero_imax}", "{periodo_2010_2018}"):
        ("interessante", "A concentração de títulos IMAX no período mais recente é coerente com a expansão comercial do formato. O padrão pode ser influenciado pelo recorte temporal e por relançamentos catalogados."),
    ("{genero_acao, genero_fantasia}", "{genero_aventura}"):
        ("interessante, embora plausível", "A combinação ação-fantasia associa-se a aventura muito acima do esperado. Isso caracteriza filmes de espetáculo, mas os rótulos podem ter sido atribuídos em conjunto."),
    ("{genero_aventura, genero_suspense}", "{genero_acao}"):
        ("interessante", "A confiança acima de 85% torna o antecedente muito informativo para ação. O suporte é baixo, porém ainda representa mais de cem filmes, sendo útil para descrever híbridos de gênero."),
    ("{avaliacao_media, genero_infantil}", "{genero_aventura}"):
        ("interessante", "Entre filmes infantis com avaliação intermediária, aventura aparece mais de três vezes acima de sua frequência geral. A avaliação apenas delimita o subconjunto e não deve ser tratada como causa."),
    ("{genero_ficcao_cientifica, periodo_2010_2018}", "{genero_acao}"):
        ("interessante", "Filmes recentes de ficção científica estão fortemente associados à ação, compatível com grandes produções e franquias do período. O recorte até 2018 e o perfil dos usuários podem amplificar o padrão."),
    ("{genero_aventura, genero_ficcao_cientifica}", "{genero_acao}"):
        ("interessante, embora plausível", "A combinação aventura-ficção científica costuma assumir estrutura de ação. O lift confirma concentração acima da frequência-base, embora a proximidade temática reduza a novidade."),
    ("{genero_acao, genero_crime}", "{genero_suspense}"):
        ("interessante", "A presença conjunta de ação e crime aumenta substancialmente suspense. O padrão faz sentido em narrativas criminais tensas, mas não implica que um gênero produza o outro."),
    ("{genero_aventura, periodo_2010_2018}", "{genero_acao}"):
        ("interessante", "Aventura no período recente aparece ligada à ação, possivelmente pelo predomínio de blockbusters. A interpretação deve considerar o tamanho menor do período 2010–2018."),
    ("{genero_ficcao_cientifica, genero_suspense}", "{genero_acao}"):
        ("interessante", "Ficção científica combinada com suspense apresenta ação muito acima da frequência geral. É um padrão de hibridização parcialmente dependente da rotulagem editorial."),
    ("{avaliacao_baixa, genero_aventura}", "{genero_acao}"):
        ("potencialmente surpreendente", "Mesmo entre aventuras de avaliação baixa, ação permanece frequente. Isso pode refletir concentração de títulos de ação-aventura mal avaliados, sem indicar que ação reduza a nota."),
    ("{genero_terror, popularidade_media}", "{genero_suspense}"):
        ("interessante", "Terror com popularidade intermediária apresenta suspense 2,5 vezes acima do esperado. A proximidade temática explica parte do resultado; popularidade apenas define o subconjunto."),
    ("{genero_imax}", "{genero_acao}"):
        ("interessante", "IMAX aparece associado a ação, coerente com produções de grande espetáculo. O suporte é baixo porque IMAX é raro, mas o lift confirma concentração acima da frequência-base."),
    ("{avaliacao_baixa, genero_ficcao_cientifica}", "{genero_acao}"):
        ("potencialmente surpreendente", "Ficção científica com avaliação baixa continua associada à ação. Pode representar títulos de ação e ficção científica menos bem recebidos, não um efeito causal do gênero."),
    ("{genero_aventura, popularidade_alta}", "{genero_acao}"):
        ("interessante", "Entre aventuras muito avaliadas, ação é mais de duas vezes mais frequente que no catálogo geral. A maior visibilidade de franquias pode contribuir para o padrão."),
    ("{genero_suspense, popularidade_alta}", "{genero_acao}"):
        ("interessante", "Suspenses muito avaliados concentram ação. Isso pode refletir maior exposição de thrillers de ação em comparação com suspenses de nicho."),
    ("{genero_crime, periodo_2000_2009}", "{genero_suspense}"):
        ("interessante", "Crime nos anos 2000 associa-se a suspense acima da frequência-base. A regra descreve o catálogo da década e não deve ser generalizada para toda a produção cinematográfica."),
    ("{avaliacao_media, genero_terror}", "{genero_suspense}"):
        ("interessante, embora plausível", "Terror com avaliação intermediária associa-se fortemente a suspense. A proximidade dos gêneros explica parte do resultado; o valor está em quantificar a sobreposição."),
    ("{genero_crime, periodo_1990_1999}", "{genero_suspense}"):
        ("interessante", "A associação crime-suspense também aparece nos anos 1990, sugerindo persistência temporal. Ela reflete a composição dos filmes incluídos no MovieLens."),
    ("{avaliacao_media, genero_crime}", "{genero_suspense}"):
        ("interessante", "Crime com avaliação intermediária apresenta suspense mais de duas vezes acima do esperado. Como avaliação intermediária é dominante, o lift é mais informativo que a confiança isolada."),
    ("{genero_crime, genero_drama}", "{genero_suspense}"):
        ("interessante", "A combinação crime-drama associa-se a suspense, caracterizando narrativas híbridas. Parte do padrão pode resultar de práticas de catalogação múltipla."),
    ("{genero_ficcao_cientifica}", "{genero_acao}"):
        ("interessante, mas ampla", "Ação é mais de duas vezes mais frequente entre filmes de ficção científica que no catálogo geral. O suporte relativamente alto torna a regra útil como síntese, embora menos específica."),
    ("{avaliacao_baixa, genero_romance}", "{genero_comedia}"):
        ("potencialmente surpreendente", "Romances de avaliação baixa aparecem frequentemente como comédias, sugerindo concentração de comédias românticas nesse subconjunto. Pode refletir preferências dos usuários."),
    ("{avaliacao_alta, popularidade_media}", "{genero_drama}"):
        ("interessante", "Filmes muito bem avaliados, mas de popularidade intermediária, concentram drama. Pode representar dramas reconhecidos por um público menor, embora a popularidade dependa da atividade dos usuários."),
    ("{avaliacao_alta}", "{genero_drama}"):
        ("interessante, embora esperada", "Drama está sobre-representado entre filmes com média alta. O padrão pode refletir preferências da comunidade MovieLens e a composição do catálogo."),
    ("{avaliacao_baixa, genero_drama}", "{popularidade_baixa}"):
        ("interessante", "Dramas de avaliação baixa tendem a ter poucas avaliações acima da frequência-base. Pode haver menor interesse, mas filmes pouco vistos também têm médias mais instáveis."),
    ("{avaliacao_baixa, periodo_1970_1989}", "{popularidade_baixa}"):
        ("interessante", "Filmes antigos e mal avaliados concentram-se na baixa popularidade. Idade, disponibilidade e preferência dos usuários podem explicar a associação."),
    ("{avaliacao_baixa, genero_comedia}", "{popularidade_baixa}"):
        ("interessante", "Comédias de avaliação baixa têm maior probabilidade de poucas avaliações. Nota e popularidade são ambas influenciadas pela seleção dos usuários."),
    ("{genero_ficcao_cientifica, periodo_2010_2018}", "{popularidade_media}"):
        ("interessante", "Ficção científica recente concentra-se na popularidade intermediária. Isso mostra que nem todo título recente alcança alta exposição e pode refletir a janela de coleta."),
}


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida e filtra as regras finais de filmes.")
    parser.add_argument("--regras", type=Path, required=True)
    parser.add_argument("--transacoes", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--lift-relevancia", type=float, default=LIFT_RELEVANCIA)
    return parser.parse_args()


def ler_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig")


def salvar_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep=";", decimal=",", index=False, encoding="utf-8-sig")


def interpretar_conjunto(texto: str) -> frozenset[str]:
    return frozenset(item.strip() for item in texto.strip("{}").split(",") if item.strip())


def descrever(itens: frozenset[str]) -> str:
    nomes = [ROTULOS.get(item, item.replace("_", " ")) for item in sorted(itens)]
    if len(nomes) == 1:
        return nomes[0]
    if len(nomes) == 2:
        return f"{nomes[0]} e {nomes[1]}"
    return ", ".join(nomes[:-1]) + f" e {nomes[-1]}"


def main() -> int:
    args = argumentos()
    for path in (args.regras, args.transacoes):
        if not path.exists():
            print(f"Erro: arquivo não encontrado: {path}", file=sys.stderr)
            return 1
    args.saida.mkdir(parents=True, exist_ok=True)

    regras = ler_csv(args.regras)
    transacoes_df = ler_csv(args.transacoes)
    transacoes = [set(json.loads(valor)) for valor in transacoes_df["transacao_json"]]

    regras["_ant"] = regras["Antecedente"].map(interpretar_conjunto)
    regras["_con"] = regras["Consequente"].map(interpretar_conjunto)
    regras["_uniao"] = regras.apply(lambda x: tuple(sorted(x["_ant"] | x["_con"])), axis=1)

    descartadas: list[dict[str, object]] = []
    for _, regra in regras.loc[regras["Lift"] < args.lift_relevancia].iterrows():
        descartadas.append({
            "Antecedente": regra["Antecedente"], "Consequente": regra["Consequente"],
            "Suporte": regra["Suporte"], "Confianca": regra["Confianca"], "Lift": regra["Lift"],
            "Motivo_descarte": f"Lift inferior a {args.lift_relevancia:.2f}; associação apenas modestamente acima da frequência-base.",
        })

    candidatas = regras.loc[regras["Lift"] >= args.lift_relevancia].copy()
    remover = []
    for indice, regra in candidatas.iterrows():
        chave = (regra["_ant"], regra["_con"])
        if chave in REGRAS_OBVIAS:
            remover.append(indice)
            descartadas.append({
                "Antecedente": regra["Antecedente"], "Consequente": regra["Consequente"],
                "Suporte": regra["Suporte"], "Confianca": regra["Confianca"], "Lift": regra["Lift"],
                "Motivo_descarte": REGRAS_OBVIAS[chave],
            })
    candidatas = candidatas.drop(index=remover).sort_values(
        ["Lift", "Confianca", "Suporte"], ascending=False
    )

    mantidas: list[int] = []
    unioes: dict[tuple[str, ...], str] = {}
    for indice, regra in candidatas.iterrows():
        uniao = regra["_uniao"]
        if uniao in unioes:
            descartadas.append({
                "Antecedente": regra["Antecedente"], "Consequente": regra["Consequente"],
                "Suporte": regra["Suporte"], "Confianca": regra["Confianca"], "Lift": regra["Lift"],
                "Motivo_descarte": f"Mesma combinação total de itens da regra mantida {unioes[uniao]}; direção alternativa removida.",
            })
        else:
            mantidas.append(indice)
            unioes[uniao] = f"{regra['Antecedente']} -> {regra['Consequente']}"

    relevantes = candidatas.loc[mantidas]
    finais = relevantes.head(30).copy()
    for _, regra in relevantes.iloc[30:].iterrows():
        descartadas.append({
            "Antecedente": regra["Antecedente"], "Consequente": regra["Consequente"],
            "Suporte": regra["Suporte"], "Confianca": regra["Confianca"], "Lift": regra["Lift"],
            "Motivo_descarte": "Regra válida, mas ficou fora das 30 por menor lift após os filtros de relevância e diversidade.",
        })

    if len(finais) < 30:
        print(f"Erro: somente {len(finais)} regras relevantes permaneceram; revise os parâmetros.", file=sys.stderr)
        return 1

    saida: list[dict[str, object]] = []
    for numero, (_, regra) in enumerate(finais.iterrows(), start=1):
        antecedente = regra["_ant"]
        consequente = regra["_con"]
        ocorrencias_antecedente = sum(antecedente.issubset(t) for t in transacoes)
        ocorrencias_conjuntas = sum((antecedente | consequente).issubset(t) for t in transacoes)

        suporte = ocorrencias_conjuntas / len(transacoes)
        confianca = ocorrencias_conjuntas / ocorrencias_antecedente
        frequencia_consequente = sum(consequente.issubset(t) for t in transacoes) / len(transacoes)
        lift = confianca / frequencia_consequente

        # Verificação independente das métricas exportadas pelo mlxtend.
        if max(abs(suporte - regra["Suporte"]), abs(confianca - regra["Confianca"]), abs(lift - regra["Lift"])) > 1e-10:
            raise ValueError(f"Divergência de métricas na regra {regra['Antecedente']} -> {regra['Consequente']}")

        descricao_ant = descrever(antecedente)
        descricao_con = descrever(consequente)
        pergunta = f"Que padrão foi encontrado entre {descricao_ant} e {descricao_con}?"
        resposta = (
            f"Entre os {ocorrencias_antecedente} filmes com {descricao_ant}, {ocorrencias_conjuntas} também apresentam "
            f"{descricao_con} ({confianca:.2%}). A combinação representa {suporte:.2%} da amostra e possui lift "
            f"{lift:.2f}, logo ocorre acima do que seria esperado pela frequência geral do consequente."
        )
        classificacao, discussao = ANALISES.get(
            (regra["Antecedente"], regra["Consequente"]),
            ("interessante", "A regra apresenta associação acima da frequência-base. A interpretação deve considerar a composição do catálogo, a rotulagem editorial e o viés de seleção dos usuários."),
        )
        saida.append({
            "Numero": numero,
            "Antecedente": regra["Antecedente"],
            "Consequente": regra["Consequente"],
            "Suporte": suporte,
            "Confianca": confianca,
            "Lift": lift,
            "Ocorrencias_antecedente": ocorrencias_antecedente,
            "Ocorrencias_conjuntas": ocorrencias_conjuntas,
            "Classificacao": classificacao,
            "Pergunta": pergunta,
            "Resposta": resposta,
            "Discussao_critica": discussao,
            "Utilidade": "Descrever padrões do catálogo e apoiar segmentação exploratória; não usar isoladamente como recomendação nem como evidência causal.",
        })

    finais_saida = pd.DataFrame(saida)
    descartadas_saida = pd.DataFrame(descartadas).sort_values(
        ["Lift", "Confianca"], ascending=False
    )
    salvar_csv(finais_saida, args.saida / "top_30_regras_filtradas.csv")
    finais_saida.to_csv(args.saida.parent / "regras_movie_recomm_selecionadas.csv", index=False, encoding="utf-8")
    salvar_csv(descartadas_saida, args.saida / "regras_descartadas_auditoria.csv")

    resumo = pd.DataFrame([
        ("Regras não redundantes recebidas", len(regras)),
        (f"Regras com lift >= {args.lift_relevancia:.2f}", int((regras["Lift"] >= args.lift_relevancia).sum())),
        ("Regras após exclusão das associações óbvias", len(candidatas)),
        ("Regras após controle de direções equivalentes", len(relevantes)),
        ("Regras selecionadas", len(finais_saida)),
        ("Regras registradas no arquivo de auditoria", len(descartadas_saida)),
    ], columns=["Etapa", "Quantidade"])
    salvar_csv(resumo, args.saida / "resumo_filtragem_regras.csv")

    print(resumo.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
