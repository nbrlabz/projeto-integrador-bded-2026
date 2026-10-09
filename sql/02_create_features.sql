
-- ============================================================
-- PROJETO INTEGRADOR BDED 2026.1
-- BASE ANALITICA PARA MACHINE LEARNING
-- Previsao de atrasos em entregas - Olist + Feriados
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;

DROP TABLE IF EXISTS analytics.delivery_features;

CREATE TABLE analytics.delivery_features AS

WITH itens AS (
    SELECT
        oi.order_id,
        COUNT(*) AS quantidade_itens,
        COUNT(DISTINCT oi.product_id) AS produtos_distintos,
        COUNT(DISTINCT oi.seller_id) AS vendedores_distintos,
        SUM(oi.price) AS valor_produtos,
        SUM(oi.freight_value) AS valor_frete,
        AVG(p.product_weight_g) AS peso_medio_produtos,
        AVG(
            p.product_length_cm *
            p.product_height_cm *
            p.product_width_cm
        ) AS volume_medio_produtos,
        MAX(
            CASE
                WHEN s.seller_state <> c.customer_state
                THEN 1 ELSE 0
            END
        ) AS vendedor_outro_estado
    FROM raw.order_items oi
    INNER JOIN raw.orders o
        ON oi.order_id = o.order_id
    INNER JOIN raw.customers c
        ON o.customer_id = c.customer_id
    LEFT JOIN raw.products p
        ON oi.product_id = p.product_id
    LEFT JOIN raw.sellers s
        ON oi.seller_id = s.seller_id
    GROUP BY oi.order_id
),

pagamentos AS (
    SELECT
        order_id,
        SUM(payment_value) AS valor_pagamento,
        MAX(payment_installments) AS parcelas_maximas,
        COUNT(*) AS quantidade_pagamentos,
        MAX(
            CASE
                WHEN payment_type = 'credit_card'
                THEN 1 ELSE 0
            END
        ) AS pagamento_cartao
    FROM raw.order_payments
    GROUP BY order_id
)

SELECT
    o.order_id,

    -- Informacoes da compra
    EXTRACT(YEAR FROM o.order_purchase_timestamp)::INTEGER
        AS ano_compra,

    EXTRACT(MONTH FROM o.order_purchase_timestamp)::INTEGER
        AS mes_compra,

    EXTRACT(DOW FROM o.order_purchase_timestamp)::INTEGER
        AS dia_semana_compra,

    EXTRACT(HOUR FROM o.order_purchase_timestamp)::INTEGER
        AS hora_compra,

    CASE
        WHEN EXTRACT(DOW FROM o.order_purchase_timestamp)
             IN (0, 6)
        THEN 1 ELSE 0
    END AS compra_fim_semana,

    -- Informacoes geograficas
    c.customer_state AS estado_cliente,

    -- Caracteristicas dos produtos e vendedores
    COALESCE(i.quantidade_itens, 0)
        AS quantidade_itens,

    COALESCE(i.produtos_distintos, 0)
        AS produtos_distintos,

    COALESCE(i.vendedores_distintos, 0)
        AS vendedores_distintos,

    COALESCE(i.valor_produtos, 0)
        AS valor_produtos,

    COALESCE(i.valor_frete, 0)
        AS valor_frete,

    COALESCE(i.peso_medio_produtos, 0)
        AS peso_medio_produtos,

    COALESCE(i.volume_medio_produtos, 0)
        AS volume_medio_produtos,

    COALESCE(i.vendedor_outro_estado, 0)
        AS vendedor_outro_estado,

    -- Informacoes de pagamento
    COALESCE(pg.valor_pagamento, 0)
        AS valor_pagamento,

    COALESCE(pg.parcelas_maximas, 0)
        AS parcelas_maximas,

    COALESCE(pg.quantidade_pagamentos, 0)
        AS quantidade_pagamentos,

    COALESCE(pg.pagamento_cartao, 0)
        AS pagamento_cartao,

    -- Integracao com a segunda fonte: feriados
    CASE
        WHEN h.data_feriado IS NOT NULL
        THEN 1 ELSE 0
    END AS compra_em_feriado,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM raw.holidays h2
            WHERE h2.data_feriado BETWEEN
                o.order_purchase_timestamp::DATE
                    - INTERVAL '3 days'
                AND
                o.order_purchase_timestamp::DATE
                    + INTERVAL '3 days'
        )
        THEN 1 ELSE 0
    END AS compra_proxima_feriado,

    -- Prazo prometido ao cliente, conhecido na compra
    (
        o.order_estimated_delivery_date::DATE
        - o.order_purchase_timestamp::DATE
    ) AS prazo_estimado_dias,

    -- Data da compra para divisao temporal treino/teste
    o.order_purchase_timestamp AS data_compra,

    -- Variavel alvo: 1 = atrasou, 0 = no prazo
    CASE
        WHEN o.order_delivered_customer_date >
             o.order_estimated_delivery_date
        THEN 1 ELSE 0
    END AS atrasou

FROM raw.orders o

INNER JOIN raw.customers c
    ON o.customer_id = c.customer_id

INNER JOIN itens i
    ON o.order_id = i.order_id

LEFT JOIN pagamentos pg
    ON o.order_id = pg.order_id

LEFT JOIN raw.holidays h
    ON o.order_purchase_timestamp::DATE = h.data_feriado

WHERE
    o.order_status = 'delivered'
    AND o.order_purchase_timestamp IS NOT NULL
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_estimated_delivery_date IS NOT NULL;

-- Chave unica por pedido
ALTER TABLE analytics.delivery_features
    ADD PRIMARY KEY (order_id);

-- Indice para divisao temporal dos dados
CREATE INDEX idx_delivery_features_data_compra
    ON analytics.delivery_features (data_compra);

-- Estatisticas para otimizar consultas
ANALYZE analytics.delivery_features;

-- Validacao inicial
SELECT
    COUNT(*) AS total_pedidos,
    SUM(atrasou) AS pedidos_atrasados,
    ROUND(AVG(atrasou) * 100, 2) AS percentual_atrasos
FROM analytics.delivery_features;

