"""Executa todas as etapas do pipeline movie_recomm na ordem correta."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa o pipeline completo de filmes.")
    parser.add_argument("--db", type=Path, required=True, help="Caminho para movie_recomm.duckdb")
    parser.add_argument("--saida", type=Path, default=Path("saida_movie_recomm"))
    parser.add_argument("--min-avaliacoes", type=int, default=5)
    return parser.parse_args()


def executar(comando: list[str], etapa: str) -> None:
    print("\n" + "=" * 72)
    print(etapa)
    print("=" * 72)
    resultado = subprocess.run(comando, check=False)
    if resultado.returncode != 0:
        raise RuntimeError(f"A etapa falhou com código {resultado.returncode}: {etapa}")


def main() -> int:
    args = argumentos()
    if not args.db.exists():
        print(f"Erro: banco não encontrado: {args.db}", file=sys.stderr)
        return 1
    if args.min_avaliacoes < 1:
        print("Erro: --min-avaliacoes deve ser maior que zero.", file=sys.stderr)
        return 1

    pasta_scripts = Path(__file__).resolve().parent
    saida = args.saida.resolve()
    db = args.db.resolve()

    comandos = [
        (
            [
                sys.executable,
                str(pasta_scripts / "00_compreensao_base_filmes.py"),
                "--db",
                str(db),
                "--saida",
                str(saida / "compreensao"),
            ],
            "ETAPA 1 — COMPREENSÃO DA BASE",
        ),
        (
            [
                sys.executable,
                str(pasta_scripts / "01_preparacao_dados_filmes.py"),
                "--db",
                str(db),
                "--saida",
                str(saida),
                "--min-avaliacoes",
                str(args.min_avaliacoes),
            ],
            "ETAPA 2 E INÍCIO DA ETAPA 4 — PREPARAÇÃO E TRANSAÇÕES",
        ),
        (
            [
                sys.executable,
                str(pasta_scripts / "02_eda_filmes.py"),
                "--db",
                str(db),
                "--dados",
                str(saida / "filmes_preparados.csv"),
                "--saida",
                str(saida / "eda"),
            ],
            "ETAPA 3 — ANÁLISE EXPLORATÓRIA",
        ),
        (
            [
                sys.executable,
                str(pasta_scripts / "03_regras_associacao_filmes.py"),
                "--transacoes",
                str(saida / "transacoes_filmes.csv"),
                "--saida",
                str(saida / "regras"),
            ],
            "ETAPAS 4, 5 E 6 — REGRAS E ANÁLISE",
        ),
        (
            [
                sys.executable,
                str(pasta_scripts / "04_validacao_regras_filmes.py"),
                "--regras",
                str(saida / "regras" / "regras_nao_redundantes.csv"),
                "--transacoes",
                str(saida / "transacoes_filmes.csv"),
                "--saida",
                str(saida / "regras"),
            ],
            "ETAPA 6 — FILTRAGEM DE REGRAS ÓBVIAS E VALIDAÇÃO FINAL",
        ),
    ]

    try:
        for comando, etapa in comandos:
            executar(comando, etapa)
    except RuntimeError as exc:
        print(f"\nErro: {exc}", file=sys.stderr)
        return 1

    print("\n" + "=" * 72)
    print("PIPELINE COMPLETO FINALIZADO")
    print("=" * 72)
    print(f"Resultados: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
