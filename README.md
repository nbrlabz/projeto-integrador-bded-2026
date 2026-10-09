# Projeto Integrador – BDED 2026.1

## Previsão de Atrasos em Entregas com Engenharia de Dados e Machine Learning

Projeto desenvolvido como atividade acadêmica da Especialização em Projetos de Inteligência Artificial.

**Aluno:** Rodrigo Nobre  
**Disciplina:** Banco de Dados e Engenharia de Dados  
**Ano:** 2026

---

## 1. Sobre o projeto

O objetivo deste projeto é desenvolver um pipeline de Engenharia de Dados que integre duas fontes independentes de informação e utilize algoritmos de Machine Learning para prever atrasos em entregas do comércio eletrônico brasileiro.

O projeto contempla extração, transformação, carregamento, integração de dados, engenharia de características, análise exploratória, treinamento de modelos e avaliação dos resultados.

## 2. Fontes de dados

### Fonte 1 – Olist

Brazilian E-Commerce Public Dataset by Olist, disponibilizado publicamente no Kaggle.

Contém informações sobre pedidos, clientes, vendedores, produtos, pagamentos, avaliações e entregas.

Fonte: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

### Fonte 2 – Feriados brasileiros

Calendário de feriados nacionais brasileiros entre 2016 e 2018, gerado com a biblioteca Python `holidays`.

Essa fonte permite identificar pedidos realizados em feriados e em datas próximas.

Documentação: https://holidays.readthedocs.io/

## 3. Tecnologias utilizadas

- Python 3.11
- PostgreSQL 16
- Pandas
- Psycopg
- Scikit-learn
- Matplotlib
- Seaborn
- JupyterLab
- Git e GitHub

## 4. Arquitetura da solução

```text
Fonte 1: Olist (CSV) -----------+
                                |
                                v
                         ETL em Python
                                |
                                v
Fonte 2: Feriados (CSV) --------+
                                |
                                v
                         PostgreSQL
                         Schema: raw
                                |
                                v
                     Integração com SQL
                                |
                                v
                         PostgreSQL
                       Schema: analytics
                                |
                                v
                      Machine Learning
                                |
                  +-------------+-------------+
                  |                           |
                  v                           v
          Regressão Logística           Random Forest
                  |                           |
                  +-------------+-------------+
                                |
                                v
                     Métricas e gráficos
                                |
                                v
                       Jupyter Notebook
```

## 5. Estrutura do projeto

```text
projeto-integrador-bded-2026/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   └── projeto_integrador_bded_2026.ipynb
├── results/
│   ├── matriz_random_forest.png
│   ├── matriz_regressao_logistica.png
│   ├── metricas_modelos.csv
│   └── metricas_modelos.json
├── sql/
│   ├── 01_create_tables.sql
│   └── 02_create_features.sql
├── src/
│   ├── etl.py
│   └── train_model.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Os arquivos CSV originais não são versionados no GitHub devido ao seu tamanho. Eles devem ser obtidos na fonte indicada.

## 6. Instalação e execução

### 6.1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd projeto-integrador-bded-2026
```

Substituir `URL_DO_REPOSITORIO` pelo endereço do repositório publicado.

### 6.2. Criar o ambiente virtual

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.3. Configurar o PostgreSQL

Criar um banco de dados chamado:

```text
projeto_integrador_bded
```

Copiar `.env.example` para `.env` e ajustar os dados de conexão, conforme o ambiente.

### 6.4. Preparar as fontes

Baixar os arquivos CSV da Olist e colocá-los em `data/raw/`.

Gerar o calendário de feriados com:

```bash
python -c "import holidays, pandas as pd; h=holidays.Brazil(years=range(2016,2019)); df=pd.DataFrame([{'data_feriado':str(d),'nome_feriado':n} for d,n in sorted(h.items())]); df.to_csv('data/raw/feriados_brasil.csv',index=False)"
```

### 6.5. Criar as tabelas

```bash
psql -d projeto_integrador_bded -f sql/01_create_tables.sql
```

### 6.6. Executar o ETL

```bash
python src/etl.py
```

### 6.7. Construir a base analítica

```bash
psql -d projeto_integrador_bded -f sql/02_create_features.sql
```

### 6.8. Treinar os modelos

```bash
python src/train_model.py
```

### 6.9. Abrir o notebook

```bash
jupyter lab
```

Abrir o arquivo `notebooks/projeto_integrador_bded_2026.ipynb`.

## 7. Resultados do processamento

O pipeline ETL carregou 1.550.949 registros em dez tabelas do PostgreSQL.

A base analítica resultante contém 96.470 pedidos entregues, dos quais:

- 88.644 foram entregues no prazo.
- 7.826 apresentaram atraso.
- 8,11% das entregas foram realizadas após a data estimada.

Foram construídas características relacionadas ao período da compra, localização do cliente, produtos, vendedores, pagamentos e feriados nacionais.

## 8. Modelos de Machine Learning

Foram treinados dois modelos de classificação:

- Regressão Logística
- Random Forest

Os dados foram separados cronologicamente, utilizando 80% dos pedidos mais antigos para treinamento e 20% dos mais recentes para teste.

### Comparação dos resultados

| Métrica | Regressão Logística | Random Forest |
|---|---:|---:|
| Accuracy | 57,14% | 60,08% |
| Precision (atrasos) | 8,09% | 4,25% |
| Recall (atrasos) | 68,56% | 30,36% |
| F1-score (atrasos) | 14,48% | 7,45% |

A Regressão Logística apresentou o maior F1-score para a classe de entregas atrasadas.

Apesar disso, a precisão dos modelos foi baixa, indicando a necessidade de melhorias antes de qualquer aplicação operacional.

## 9. Análise exploratória

A análise dos dados identificou diferenças regionais nas taxas de atraso.

Entre os estados analisados, Alagoas apresentou 23,93% de atrasos, Maranhão 19,67% e Piauí 15,97%.

Na análise dos feriados, os pedidos realizados próximos a feriados nacionais apresentaram taxa de atraso de 6,71%, enquanto os demais registraram 8,32%.

Esses resultados representam associações observadas na base de dados e não permitem estabelecer relações de causa e efeito.

## 10. Limitações e melhorias futuras

O principal desafio encontrado foi o desequilíbrio entre as classes, pois apenas 8,11% dos pedidos apresentaram atraso.

Mesmo com a utilização de pesos balanceados, os modelos produziram muitos falsos positivos.

Como melhorias futuras, destacam-se:

- Engenharia de novas características logísticas.
- Ajuste de hiperparâmetros e limiares de classificação.
- Testes com outros algoritmos.
- Validação em diferentes períodos.
- Análise dos custos de falsos positivos e falsos negativos.

## 11. Conclusão

O projeto demonstrou a construção de um pipeline completo de Engenharia de Dados e Machine Learning, desde a integração de fontes independentes até a avaliação de modelos preditivos.

A solução permitiu organizar e analisar dados reais de comércio eletrônico e documentar os resultados de maneira reproduzível.

Os modelos ainda apresentam limitações de desempenho, mas os experimentos oferecem uma base para futuras melhorias.

## 12. Referências

- [Olist – Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Python Holidays](https://holidays.readthedocs.io/)
```
