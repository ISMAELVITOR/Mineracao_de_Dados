"""Audita os três experimentos e seleciona 15 regras F1 positivas."""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"
PERIODOS = ["1950_2024", "1950_1959", "2014_2024"]


def main() -> None:
    grupos = []
    for periodo in PERIODOS:
        caminho = RESULTADOS_DIR / f"regras_f1_{periodo}.csv"
        regras = pd.read_csv(caminho)
        regras["experimento"] = periodo.replace("_", "–", 1)
        grupos.append(regras)
    regras = pd.concat(grupos, ignore_index=True)
    regras = regras.query("suporte >= 0.02 and confianca >= 0.60 and lift >= 1.10").copy()
    regras["uniao"] = regras.apply(
        lambda r: " | ".join(sorted(set((r["antecedente"] + " | " + r["consequente"]).split(" | ")))), axis=1
    )
    regras = regras.sort_values(["lift", "confianca", "suporte"], ascending=False)
    regras = regras.drop_duplicates(["experimento", "antecedente", "consequente"])
    # Direções equivalentes dentro do mesmo período são redundantes para a síntese.
    regras = regras.drop_duplicates(["experimento", "uniao"]).head(15).copy()
    if len(regras) != 15:
        raise ValueError(f"Esperadas 15 regras F1 selecionáveis; obtidas {len(regras)}.")
    regras.insert(0, "numero", range(1, 16))
    regras["pergunta"] = regras.apply(
        lambda r: f"No período {r.experimento}, o que ocorre quando há {r.antecedente}?", axis=1
    )
    regras["resposta"] = regras.apply(
        lambda r: f"Aparece {r.consequente} com confiança de {r.confianca:.2%}, suporte de {r.suporte:.2%} e lift {r.lift:.2f}.", axis=1
    )
    regras["analise_critica"] = regras.apply(
        lambda r: "A associação é positiva, mas descreve coocorrência histórica; não demonstra causalidade e pode refletir regras esportivas e composição das equipes.", axis=1
    )
    regras.drop(columns="uniao").to_csv(RESULTADOS_DIR / "regras_f1_selecionadas.csv", index=False)
    print("Validação F1: 15 regras positivas, não redundantes, selecionadas.")


if __name__ == "__main__": main()
