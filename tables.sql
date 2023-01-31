CREATE SCHEMA IF NOT EXISTS books_to_scrape;

CREATE TABLE IF NOT EXISTS books
(
    name text,
    category VARCHAR(25),
    price DECIMAL(4,2),
    description text,
    upc text,
    product_type VARCHAR(30),
    availability VARCHAR(25),
    reviews text,
    PRIMARY KEY(upc)
);