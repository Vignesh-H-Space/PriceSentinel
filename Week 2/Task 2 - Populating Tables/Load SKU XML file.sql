USE map_project;

LOAD XML LOCAL INFILE 'D:/Github/MAP/Week 2/Resources/SKU.xml'
INTO TABLE sku
ROWS IDENTIFIED BY '<item>'
(@PN, @Sku)
SET
    PN = @PN,
    SKU = @Sku;