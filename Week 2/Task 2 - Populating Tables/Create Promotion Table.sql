USE map_project;

CREATE TABLE promotion (
    SKU VARCHAR(100) NOT NULL,
    PL VARCHAR(100),
    Season VARCHAR(100),
    Promotion VARCHAR(255),
    FOREIGN KEY (SKU) REFERENCES sku(SKU)
);