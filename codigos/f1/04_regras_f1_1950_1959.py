"""Executa o experimento Apriori F1 de 1950 a 1959."""
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
arquivo = Path(__file__).with_name("04_regras_f1_1950_2024.py")
spec = importlib.util.spec_from_file_location("regras_f1_comum", arquivo)
modulo = importlib.util.module_from_spec(spec); spec.loader.exec_module(modulo)
if __name__ == "__main__": modulo.executar(1950, 1959)
