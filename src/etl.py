
"""
Projeto Integrador BDED 2026.1
ETL - Olist + Feriados Brasileiros

Extração, transformação e carregamento de dados
no PostgreSQL, esquema raw.
"""

from pathlib import Path
from io import StringIO
import os
import time

import pandas as pd
import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "projeto_integrador_bded"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER") or os.getenv("USER"),
}

if os.getenv("DB_PASSWORD"):
    DB_CONFIG["password"] = os.getenv("DB_PASSWORD")


# Ordem respeita as dependências entre tabelas.
# A geolocalização é carregada sem deduplicação,
# preservando os registros originais.
DATASETS = [
    ("customers", "olist_customers_dataset.csv", ["customer_id"]),
    ("sellers", "olist_sellers_dataset.csv", ["seller_id"]),
    ("products", "olist_products_dataset.csv", ["product_id"]),
    ("category_translation", "product_category_name_translation.csv",
     ["product_category_name"]),
    ("geolocation", "olist_geolocation_dataset.csv", []),
    ("holidays", "feriados_brasil.csv", ["data_feriado"]),
    ("orders", "olist_orders_dataset.csv", ["order_id"]),
    ("order_items", "olist_order_items_dataset.csv",
     ["order_id", "order_item_id"]),
    ("order_payments", "olist_order_payments_dataset.csv",
     ["order_id", "payment_sequential"]),
    ("order_reviews", "olist_order_reviews_dataset.csv", []),
]


def extract(filename):
    """Extrai os dados de um arquivo CSV."""
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    df = pd.read_csv(path, dtype=str, low_memory=False)
    print(f"  Extraídos: {len(df):,} registros")

    return df


def transform(df, table, keys):
    """Padroniza dados e remove duplicações de chave."""
    df = df.copy()

    # Padroniza valores vazios como NULL.
    df = df.replace(r"^\s*$", None, regex=True)

    # Remove espaços em identificadores e categorias.
    for col in keys:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # Remove registros sem chave primária.
    if keys:
        before = len(df)
        df = df.dropna(subset=keys)
        df = df.drop_duplicates(subset=keys, keep="first")
        removed = before - len(df)

        if removed:
            print(f"  Duplicados/inválidos removidos: {removed}")

    # A tabela possui uma chave interna gerada pelo banco.
    if table == "order_reviews":
        df = df.drop(columns=["review_row_id"], errors="ignore")

    print(f"  Transformados: {len(df):,} registros")
    return df


def load(conn, df, table):
    """Carrega os registros utilizando COPY do PostgreSQL."""
    columns = list(df.columns)
    quoted_columns = ", ".join(f'"{c}"' for c in columns)

    # A exportação CSV preserva aspas, vírgulas,
    # textos e valores nulos.
    buffer = StringIO()
    df.to_csv(buffer, index=False, na_rep="")
    buffer.seek(0)

    sql = (
        f'COPY raw."{table}" ({quoted_columns}) '
        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')"
    )

    with conn.cursor() as cur:
        with cur.copy(sql) as copy:
            while chunk := buffer.read(1024 * 1024):
                copy.write(chunk)

    print(f"  Carregados: {len(df):,} registros")


def clear_tables(conn):
    """Limpa as tabelas para permitir reexecução do ETL."""
    tables = ", ".join(
        f'raw."{table}"' for table, _, _ in DATASETS
    )

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")

    print("Tabelas preparadas para nova importação.")


def run_etl():
    start = time.time()

    print("=" * 60)
    print("PROJETO INTEGRADOR - PIPELINE ETL")
    print("Fonte 1: Olist | Fonte 2: Feriados brasileiros")
    print("=" * 60)

    total = 0

    # A transação só será confirmada quando todas
    # as tabelas forem carregadas com sucesso.
    with psycopg.connect(**DB_CONFIG) as conn:
        clear_tables(conn)

        for table, filename, keys in DATASETS:
            print(f"\nTabela: raw.{table}")

            df = extract(filename)
            df = transform(df, table, keys)
            load(conn, df, table)

            total += len(df)

        conn.commit()

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print("ETL FINALIZADO COM SUCESSO!")
    print(f"Total de registros carregados: {total:,}")
    print(f"Tempo de execução: {elapsed:.2f} segundos")
    print("=" * 60)


if __name__ == "__main__":
    run_etl()

