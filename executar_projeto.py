"""Executa e valida todo o projeto a partir da raiz do repositório."""
from __future__ import annotations

import subprocess
import sys
import time
import shutil
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
F1 = PROJECT_ROOT / "codigos" / "f1"
MOVIE = PROJECT_ROOT / "codigos" / "movie_recomm"
RESULTADOS = PROJECT_ROOT / "resultados"
DB_F1 = PROJECT_ROOT / "BasesDeDados" / "f1.duckdb"
DB_MOVIE = PROJECT_ROOT / "BasesDeDados" / "movie_recomm.duckdb"


def executar(numero: int, titulo: str, script: Path, *argumentos: object) -> None:
    comando = [sys.executable, str(script), *(str(x) for x in argumentos)]
    inicio = time.perf_counter()
    print(f"\n[{numero:02d}] INICIADA: {titulo}", flush=True)
    try:
        subprocess.run(comando, cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as erro:
        print(f"[{numero:02d}] ERRO: {titulo}\nComando: {comando}\nCódigo: {erro.returncode}", file=sys.stderr)
        raise
    print(f"[{numero:02d}] CONCLUÍDA: {titulo} ({time.perf_counter() - inicio:.2f}s)")


def conferir_f1() -> None:
    esperados = {"1950_2024": (24966, 27, 61, 9), "1950_1959": (1939, 13, 48, 17), "2014_2024": (4392, 17, 73, 21)}
    for periodo, esperado in esperados.items():
        transacoes = pd.read_csv(RESULTADOS / "f1" / f"transacoes_f1_{periodo}.csv")
        itemsets = pd.read_csv(RESULTADOS / "f1" / f"itemsets_f1_{periodo}.csv")
        regras = pd.read_csv(RESULTADOS / "f1" / f"regras_f1_{periodo}.csv")
        obtido = (len(transacoes), pd.unique(transacoes.values.ravel()).size, len(itemsets), len(regras))
        if obtido != esperado:
            raise ValueError(f"Divergência F1 {periodo}: esperado {esperado}; obtido {obtido}; etapas 03/04.")
    antigas = pd.read_csv(RESULTADOS / "f1" / "regras_f1_1950_1959.csv")
    positivas = len(antigas.query("lift >= 1.10"))
    if positivas != 9:
        raise ValueError(f"Divergência F1 1950_1959: esperado 9 regras com lift >= 1.10; obtido {positivas}; etapa 05.")


def conferir_movie() -> None:
    pasta = RESULTADOS / "movie_recomm"; regras = pasta / "regras"
    transacoes = pd.read_csv(pasta / "transacoes_filmes.csv", sep=";", decimal=",")
    itemsets = pd.read_csv(regras / "itemsets_frequentes.csv", sep=";", decimal=",")
    completas = pd.read_csv(regras / "regras_associacao_completas.csv", sep=";", decimal=",")
    nao_redundantes = pd.read_csv(regras / "regras_nao_redundantes.csv", sep=";", decimal=",")
    itens = set().union(*(set(__import__("json").loads(x)) for x in transacoes["transacao_json"]))
    obtido = (len(transacoes), len(itens), len(itemsets), len(completas), len(nao_redundantes))
    esperado = (3649, 31, 501, 121, 85)
    if obtido != esperado:
        raise ValueError(f"Divergência movie_recomm: esperado {esperado}; obtido {obtido}; etapas 09–11.")


def consolidar() -> None:
    f1 = pd.read_csv(RESULTADOS / "f1" / "regras_f1_selecionadas.csv")
    movie = pd.read_csv(RESULTADOS / "movie_recomm" / "regras_movie_recomm_selecionadas.csv")
    f1_final = pd.DataFrame({"banco": "f1", "experimento": f1["experimento"], "numero": f1["numero"],
        "antecedente": f1["antecedente"], "consequente": f1["consequente"], "suporte": f1["suporte"],
        "confianca": f1["confianca"], "lift": f1["lift"], "pergunta": f1["pergunta"],
        "resposta": f1["resposta"], "analise_critica": f1["analise_critica"]})
    movie_final = pd.DataFrame({"banco": "movie_recomm", "experimento": "catalogo_completo",
        "numero": movie["Numero"], "antecedente": movie["Antecedente"], "consequente": movie["Consequente"],
        "suporte": movie["Suporte"], "confianca": movie["Confianca"], "lift": movie["Lift"],
        "pergunta": movie["Pergunta"], "resposta": movie["Resposta"], "analise_critica": movie["Discussao_critica"]})
    final = pd.concat([f1_final, movie_final], ignore_index=True)
    obrigatorias = ["banco", "experimento", "numero", "antecedente", "consequente", "suporte", "confianca", "lift", "pergunta", "resposta", "analise_critica"]
    duplicadas = final.duplicated(["banco", "experimento", "antecedente", "consequente"]).sum()
    if len(f1_final) != 15 or len(movie_final) != 30 or len(final) != 45 or final[obrigatorias].isna().any().any() or duplicadas:
        raise ValueError(f"Consolidado inválido: F1={len(f1_final)}, movie={len(movie_final)}, total={len(final)}, duplicadas={duplicadas}.")
    final[obrigatorias].to_csv(RESULTADOS / "regras_finais_trabalho.csv", index=False, encoding="utf-8", float_format="%.10g")


def limpar_intermediarios() -> None:
    """Mantém na entrega apenas gráficos e CSVs finais reproduzíveis."""
    f1_manter = {
        *(f"itemsets_f1_{p}.csv" for p in ("1950_2024", "1950_1959", "2014_2024")),
        *(f"regras_f1_{p}.csv" for p in ("1950_2024", "1950_1959", "2014_2024")),
        "regras_f1_selecionadas.csv",
    }
    for caminho in (RESULTADOS / "f1").iterdir():
        if caminho.is_file() and caminho.name not in f1_manter:
            caminho.unlink()
    movie = RESULTADOS / "movie_recomm"
    movie_manter = {"regras_movie_recomm.csv", "regras_movie_recomm_selecionadas.csv"}
    for caminho in movie.iterdir():
        if caminho.is_dir() and caminho.name != "graficos":
            shutil.rmtree(caminho)
        elif caminho.is_file() and caminho.name not in movie_manter:
            caminho.unlink()


def main() -> None:
    (RESULTADOS / "f1" / "graficos").mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "movie_recomm" / "graficos").mkdir(parents=True, exist_ok=True)
    etapas = [
        ("Compreensão da F1", F1 / "00_compreensao_f1.py", []),
        ("Preparação da F1", F1 / "01_preparacao_dados_f1.py", []),
        ("Análise exploratória da F1", F1 / "02_analise_exploratoria_f1.py", []),
        ("Regras F1 1950–2024", F1 / "04_regras_f1_1950_2024.py", []),
        ("Regras F1 1950–1959", F1 / "04_regras_f1_1950_1959.py", []),
        ("Regras F1 2014–2024", F1 / "04_regras_f1_2014_2024.py", []),
    ]
    for numero, (titulo, script, args) in enumerate(etapas, 1): executar(numero, titulo, script, *args)
    conferir_f1()
    executar(7, "Validação final da F1", F1 / "05_validacao_regras_f1.py")
    pasta_movie = RESULTADOS / "movie_recomm"; regras_movie = pasta_movie / "regras"
    executar(8, "Compreensão de movie_recomm", MOVIE / "00_compreensao_movie_recomm.py")
    executar(9, "Preparação dos filmes", MOVIE / "01_preparacao_dados_filmes.py", "--db", DB_MOVIE, "--saida", pasta_movie)
    executar(10, "Análise exploratória dos filmes", MOVIE / "02_analise_exploratoria_filmes.py", "--db", DB_MOVIE, "--dados", pasta_movie / "filmes_preparados.csv", "--saida", pasta_movie / "graficos")
    executar(11, "Regras de movie_recomm", MOVIE / "03_regras_associacao_filmes.py", "--transacoes", pasta_movie / "transacoes_filmes.csv", "--saida", regras_movie)
    conferir_movie()
    executar(12, "Validação final de movie_recomm", MOVIE / "04_validacao_regras_filmes.py", "--regras", regras_movie / "regras_nao_redundantes.csv", "--transacoes", pasta_movie / "transacoes_filmes.csv", "--saida", regras_movie)
    inicio = time.perf_counter(); print("\n[13] INICIADA: consolidação das 45 regras"); consolidar()
    print(f"[13] CONCLUÍDA: consolidação das 45 regras ({time.perf_counter() - inicio:.2f}s)")
    limpar_intermediarios()


if __name__ == "__main__": main()
