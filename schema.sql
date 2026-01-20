
-- ReturnImpact database schema
-- This schema was designed based on the project requirements and
-- CS50’s introduction to SQL concepts (https://cs50.harvard.edu/x/2023/sql/).

CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE TABLE product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,         -- e.g., "Red / Large"
    sku TEXT,                   -- optional stock keeping unit
    FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE transport_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_value TEXT
);
CREATE TABLE returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    order_number TEXT,
    return_date DATE NOT NULL,

    -- Transport + distance + CO₂ (manual input in V1)
    transport_mode_id INTEGER,
    departure_location TEXT,
    destination_location TEXT,
    weight_kg REAL,
    co2_kg REAL,

    -- Cost breakdown (all optional in V1)
    cost_refund REAL,
    cost_shipping REAL,
    cost_handling REAL,
    cost_restocking REAL,

    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, transport_summary TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (transport_mode_id) REFERENCES transport_modes(id)
);
CREATE TABLE return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    variant_id INTEGER, 

    quantity INTEGER NOT NULL DEFAULT 1,
    weight REAL,
    dimensions TEXT,
    condition TEXT,

    -- Flags (0/1)
    restockable INTEGER DEFAULT 0,
    hazardous INTEGER DEFAULT 0,
    temperature_sensitive INTEGER DEFAULT 0,

    FOREIGN KEY (return_id) REFERENCES returns(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    order_number TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE content_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

INSERT INTO roles (name) VALUES ('admin');

