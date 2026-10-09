
"""
Projeto Integrador BDED 2026.1
Treinamento e avaliacao de modelos de classificacao
Objetivo: prever atrasos nas entregas da Olist.
"""

from pathlib import Path
import json
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import psycopg

from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    ConfusionMatrixDisplay,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "projeto_integrador_bded"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER") or os.getenv("USER"),
}

if os.getenv("DB_PASSWORD"):
    DB_CONFIG["password"] = os.getenv("DB_PASSWORD")


def load_data():
    """Consulta a base analitica do PostgreSQL."""
    query = """
        SELECT *
        FROM analytics.delivery_features
        ORDER BY data_compra, order_id
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [col.name for col in cur.description]
            rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=columns)
    print(f"Pedidos carregados: {len(df):,}")
    return df


def prepare_data(df):
    """Prepara os atributos sem utilizar informacoes futuras."""
    df = df.sort_values(
        ["data_compra", "order_id"]
    ).reset_index(drop=True)

    # A data da compra e usada somente para dividir
    # treino e teste. O ID nao e atributo preditivo.
    excluded = ["order_id", "data_compra", "atrasou"]

    X = df.drop(columns=excluded)
    y = df["atrasou"].astype(int)

    split = int(len(df) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    numeric_columns = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        exclude=["number"]
    ).columns.tolist()

    # Converte colunas numericas do PostgreSQL
    # para tipos compativeis com scikit-learn.
    for col in numeric_columns:
        X_train = X_train.copy()
        X_test = X_test.copy()
        X_train[col] = pd.to_numeric(
            X_train[col], errors="coerce"
        )
        X_test[col] = pd.to_numeric(
            X_test[col], errors="coerce"
        )

    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(
            handle_unknown="ignore"
        )),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_transformer, numeric_columns),
        ("cat", categorical_transformer, categorical_columns),
    ])

    print(f"Treinamento: {len(X_train):,} pedidos")
    print(f"Teste: {len(X_test):,} pedidos")
    print(
        f"Atrasos no treino: {y_train.mean() * 100:.2f}%"
    )
    print(
        f"Atrasos no teste: {y_test.mean() * 100:.2f}%"
    )

    return (
        X_train, X_test,
        y_train, y_test,
        preprocessor,
    )


def evaluate_model(name, model, X_test, y_test):
    """Calcula metricas e salva matriz de confusao."""
    predictions = model.predict(X_test)

    metrics = {
        "modelo": name,
        "accuracy": accuracy_score(
            y_test, predictions
        ),
        "precision": precision_score(
            y_test, predictions, zero_division=0
        ),
        "recall": recall_score(
            y_test, predictions, zero_division=0
        ),
        "f1_score": f1_score(
            y_test, predictions, zero_division=0
        ),
    }

    print(f"\nResultados - {name}")
    print(classification_report(
        y_test, predictions, zero_division=0
    ))

    cm = confusion_matrix(
        y_test, predictions, labels=[0, 1]
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["No prazo", "Atrasado"],
    )

    display.plot(cmap="Blues", values_format="d")
    plt.title(f"Matriz de confusao - {name}")
    plt.tight_layout()

    filename = name.lower().replace(" ", "_")
    plt.savefig(
        RESULTS_DIR / f"matriz_{filename}.png",
        dpi=160,
    )
    plt.close()

    return metrics


def main():
    print("=" * 60)
    print("PROJETO INTEGRADOR - MACHINE LEARNING")
    print("Previsao de atrasos nas entregas")
    print("=" * 60)

    df = load_data()

    (
        X_train, X_test,
        y_train, y_test,
        preprocessor,
    ) = prepare_data(df)

    models = {
        "Regressao Logistica": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = []

    for name, estimator in models.items():
        print(f"\nTreinando: {name}")

        # Cada modelo recebe seu proprio pipeline.
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ])

        pipeline.fit(X_train, y_train)

        metrics = evaluate_model(
            name, pipeline, X_test, y_test
        )
        results.append(metrics)

    results_df = pd.DataFrame(results)
    results_df.to_csv(
        RESULTS_DIR / "metricas_modelos.csv",
        index=False,
    )

    with open(
        RESULTS_DIR / "metricas_modelos.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results, file, indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)
    print("COMPARACAO DOS MODELOS")
    print("=" * 60)
    print(results_df.to_string(index=False))

    best = results_df.loc[
        results_df["f1_score"].idxmax()
    ]

    print(
        f"\nMelhor modelo por F1-score: "
        f"{best['modelo']}"
    )
    print("\nResultados salvos na pasta results/")


if __name__ == "__main__":
    main()

