"""Executa Apriori para um período F1; também é reutilizado pelos demais períodos."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTADOS_DIR = PROJECT_ROOT / "resultados" / "f1"


def executar(inicio: int, fim: int) -> None:
    entrada = RESULTADOS_DIR / f"transacoes_f1_{inicio}_{fim}.csv"
    preparador_path = Path(__file__).with_name("03_preparacao_transacoes_f1.py")
    spec = importlib.util.spec_from_file_location("preparacao_transacoes_f1", preparador_path)
    preparador = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparador)
    preparador.gerar_transacoes(inicio, fim, entrada)
    dados = pd.read_csv(entrada); transacoes = dados.astype(str).values.tolist()
    encoder = TransactionEncoder(); matriz = encoder.fit(transacoes).transform(transacoes)
    binaria = pd.DataFrame(matriz, columns=encoder.columns_)
    itemsets = apriori(binaria, min_support=0.02, use_colnames=True)
    regras = association_rules(itemsets, metric="confidence", min_threshold=0.60)
    itemsets_saida = itemsets.rename(columns={"support": "suporte"}).copy()
    itemsets_saida["itemsets"] = itemsets_saida["itemsets"].map(lambda x: " | ".join(sorted(x)))
    regras_saida = regras[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
    regras_saida.columns = ["antecedente", "consequente", "suporte", "confianca", "lift"]
    for coluna in ["antecedente", "consequente"]:
        regras_saida[coluna] = regras_saida[coluna].map(lambda x: " | ".join(sorted(x)))
    itemsets_saida.to_csv(RESULTADOS_DIR / f"itemsets_f1_{inicio}_{fim}.csv", index=False)
    regras_saida.sort_values(["lift", "confianca"], ascending=False).to_csv(RESULTADOS_DIR / f"regras_f1_{inicio}_{fim}.csv", index=False)
    print(f"F1 {inicio}–{fim}: {len(transacoes)} transações, {len(encoder.columns_)} itens, {len(itemsets)} itemsets, {len(regras_saida)} regras.")


if __name__ == "__main__": executar(1950, 2024)
