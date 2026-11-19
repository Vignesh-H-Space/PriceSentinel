USE map_project;

CREATE TABLE category_mapping (
    SKU VARCHAR(100) NOT NULL,
    PL VARCHAR(100) NOT NULL,
    Category VARCHAR(100),
    sub_category VARCHAR(100),

    PRIMARY KEY (SKU),

    FOREIGN KEY (SKU) REFERENCES sku(SKU)
);