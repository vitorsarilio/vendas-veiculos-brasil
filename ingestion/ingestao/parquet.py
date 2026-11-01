"""Gravação dos registros extraídos como Parquet (tudo texto; os tipos ficam no staging do dbt)."""

from pathlib import Path

import duckdb


def _sql_texto(caminho: Path) -> str:
    """Caminho como literal SQL (barras normais funcionam no Windows e no Linux)."""
    return "'" + caminho.as_posix().replace("'", "''") + "'"


def _sql_coluna(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def registros_para_parquet(registros: list[dict[str, str]], colunas: list[str], caminho_parquet: Path) -> int:
    """Grava os registros como Parquet de texto, na ordem recebida. Retorna o número de linhas."""
    caminho_parquet.parent.mkdir(parents=True, exist_ok=True)
    definicao = ", ".join(f"{_sql_coluna(c)} VARCHAR" for c in colunas)
    with duckdb.connect() as con:
        con.execute(f"CREATE TABLE registros ({definicao})")
        con.executemany(
            f"INSERT INTO registros VALUES ({', '.join('?' for _ in colunas)})",
            [[None if r.get(c) is None else str(r[c]) for c in colunas] for r in registros],
        )
        con.execute(f"COPY registros TO {_sql_texto(caminho_parquet)} (FORMAT parquet, COMPRESSION zstd)")
    return len(registros)
