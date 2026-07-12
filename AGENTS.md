# Repository Guidelines

## Project Structure & Module Organization

This repository compares association rules from Formula 1 and MovieLens data. Read-only DuckDB sources are in `BasesDeDados/`; never rewrite them. Final Python stages live in `codigos/f1/` and `codigos/movie_recomm/`, numbered in execution order. Generated tables and plots belong in `resultados/f1/` and `resultados/movie_recomm/`. The cross-dataset deliverable is `resultados/regras_finais_trabalho.csv`, while `Relatorio.pdf` is the immutable final report.

Both pipelines follow comprehension, preparation, exploratory analysis, rule extraction, and validation. F1 additionally centralizes transaction construction in `03_preparacao_transacoes_f1.py` and runs three time periods through the shared implementation in `04_regras_f1_1950_2024.py`.

## Build, Test, and Development Commands

Use Python 3.11 or 3.12 from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python executar_projeto.py
```

The executor runs all stages, reports duration, checks expected experiment counts, and stops on divergence. For a quick syntax check, run `python -m compileall -q codigos executar_projeto.py`. Individual scripts may also be run from the root; use `python <script> --help` where CLI arguments are available.

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation, UTF-8 text, type hints for reusable functions, and `snake_case` identifiers. Use `pathlib.Path` exclusively for paths. Scripts below `codigos/` must derive `PROJECT_ROOT` with `Path(__file__).resolve().parents[2]`; do not add machine-specific paths. Preserve two-digit stage prefixes, such as `05_validacao_regras_f1.py`. Centralize discretization and filtering rules instead of copying them across experiments.

## Testing Guidelines

There is no separate unit-test suite. The required integration test is `python executar_projeto.py`. Review its count assertions and inspect generated CSVs for missing text, duplicates, and invalid lift values. New isolated logic should receive `pytest` tests under `tests/`, named `test_<module>.py`.

## Commit & Pull Request Guidelines

History uses short Portuguese summaries. Prefer an imperative, scoped subject such as `Centraliza transações da F1`. Keep generated-result changes with the code that produced them. Pull requests must identify affected datasets and stages, list commands run, report count or metric changes, and include updated plots when visual outputs change. Never adjust metrics merely to match the report; document any divergence explicitly.
