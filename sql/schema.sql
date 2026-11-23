-- Synthetic CI-only database. No BULKGRAM schema or data.
CREATE TABLE IF NOT EXISTS ci_synthetic_items (
 id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
 label VARCHAR(80) NOT NULL,
 stock INT UNSIGNED NOT NULL,
 CONSTRAINT ck_ci_stock CHECK (stock <= 1000000)
) ENGINE=InnoDB;
