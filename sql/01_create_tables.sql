
-- PROJETO INTEGRADOR BDED 2026.1
-- Previsão de atrasos em entregas com Machine Learning
-- Estrutura das tabelas de dados brutos

CREATE SCHEMA IF NOT EXISTS raw;

-- 1. Clientes
CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32),
    customer_zip_code_prefix VARCHAR(5),
    customer_city TEXT,
    customer_state VARCHAR(2)
);

-- 2. Pedidos
CREATE TABLE IF NOT EXISTS raw.orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) REFERENCES raw.customers(customer_id),
    order_status VARCHAR(30),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

-- 3. Vendedores
CREATE TABLE IF NOT EXISTS raw.sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(5),
    seller_city TEXT,
    seller_state VARCHAR(2)
);

-- 4. Produtos
CREATE TABLE IF NOT EXISTS raw.products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC,
    product_length_cm NUMERIC,
    product_height_cm NUMERIC,
    product_width_cm NUMERIC
);

-- 5. Itens dos pedidos
CREATE TABLE IF NOT EXISTS raw.order_items (
    order_id VARCHAR(32) REFERENCES raw.orders(order_id),
    order_item_id INTEGER,
    product_id VARCHAR(32) REFERENCES raw.products(product_id),
    seller_id VARCHAR(32) REFERENCES raw.sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price NUMERIC(12,2),
    freight_value NUMERIC(12,2),
    PRIMARY KEY (order_id, order_item_id)
);

-- 6. Pagamentos
CREATE TABLE IF NOT EXISTS raw.order_payments (
    order_id VARCHAR(32) REFERENCES raw.orders(order_id),
    payment_sequential INTEGER,
    payment_type VARCHAR(30),
    payment_installments INTEGER,
    payment_value NUMERIC(12,2),
    PRIMARY KEY (order_id, payment_sequential)
);

-- 7. Avaliações
CREATE TABLE IF NOT EXISTS raw.order_reviews (
    review_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id VARCHAR(32),
    order_id VARCHAR(32) REFERENCES raw.orders(order_id),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

-- 8. Geolocalização
CREATE TABLE IF NOT EXISTS raw.geolocation (
    geolocation_zip_code_prefix VARCHAR(5),
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city TEXT,
    geolocation_state VARCHAR(2)
);

-- 9. Tradução das categorias
CREATE TABLE IF NOT EXISTS raw.category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

-- 10. Segunda fonte: feriados brasileiros
CREATE TABLE IF NOT EXISTS raw.holidays (
    data_feriado DATE PRIMARY KEY,
    nome_feriado TEXT
);

-- Índices para otimizar consultas e relacionamentos
CREATE INDEX IF NOT EXISTS idx_orders_customer
    ON raw.orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_purchase
    ON raw.orders(order_purchase_timestamp);

CREATE INDEX IF NOT EXISTS idx_geolocation_zip
    ON raw.geolocation(geolocation_zip_code_prefix);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON raw.order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_seller
    ON raw.order_items(seller_id);
