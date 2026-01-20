
-- ReturnImpact V1 database schema
-- This schema was designed based on the project requirements and
-- CS50’s introduction to SQL concepts (https://cs50.harvard.edu/x/2023/sql/).

-- ------------------------------------------------------------
-- Companies table
-- Each company using the platform has its own isolated data.
-- Multi‑tenant design: every user and every product belongs to a company.
-- ------------------------------------------------------------
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Users table
-- Each user belongs to exactly one company.
-- Passwords are stored as hashes (never plain text).
-- Password hashing follows Flask/Werkzeug docs:
-- https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
-- ------------------------------------------------------------
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ------------------------------------------------------------
-- Roles table
-- Simple role system: admin, manager, viewer.
-- Based on common RBAC patterns (Role-Based Access Control).
-- ------------------------------------------------------------
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- User_roles table
-- Many-to-many relationship between users and roles.
-- ------------------------------------------------------------
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Seed default roles
INSERT INTO roles (name) VALUES ('admin');
INSERT INTO roles (name) VALUES ('manager');
INSERT INTO roles (name) VALUES ('viewer');

-----------------------------------------------------------------
-- exending database after initial checks 
--------------------------------------------------------------------
-- PRODUCTS TABLE
-- Each company can define its own products.
-- This table stores the base product (e.g., "T-Shirt").
-- Multi-tenant rule: every product belongs to exactly one company.
--------------------------------------------------------------------
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

--------------------------------------------------------------------
-- PRODUCT VARIANTS TABLE
-- Each product can have multiple variants (e.g., size, color).
-- This supports real-world return scenarios where variants matter.
-- Multi-tenant rule: variants inherit company_id from the product.
--------------------------------------------------------------------
CREATE TABLE product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,         -- e.g., "Red / Large"
    sku TEXT,                   -- optional stock keeping unit
    FOREIGN KEY (product_id) REFERENCES products(id)
);

--------------------------------------------------------------------
-- TRANSPORT MODES TABLE
-- Global list shared by all companies.
-- Used when creating a return to classify transport type.
-- Reference: SQLite CREATE TABLE docs
-- https://www.sqlite.org/lang_createtable.html
--------------------------------------------------------------------
CREATE TABLE transport_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_value TEXT
);

-- Updated Climatiq activity IDs (data_version 29 compatible)
INSERT INTO transport_modes (name, api_value) VALUES ('Road', 'road');
INSERT INTO transport_modes (name, api_value) VALUES ('Air', 'air');
INSERT INTO transport_modes (name, api_value) VALUES ('Sea', 'sea');
INSERT INTO transport_modes (name, api_value) VALUES ('Rail', 'rail');


--------------------------------------------------------------------
-- RETURNS TABLE
-- Stores each return event.
-- Multi-tenant rule: each return belongs to exactly one company.
-- Includes manual CO₂ and cost fields for V1.
-- Reference: CS50 SQL (multiple numeric fields, NULL handling)
-- https://cs50.harvard.edu/x/2023/sql/
--------------------------------------------------------------------
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (transport_mode_id) REFERENCES transport_modes(id)
);

--------------------------------------------------------------------
-- RETURN ITEMS TABLE
-- Each return can contain multiple items.
-- Supports partial returns and detailed item attributes.
-- Reference: SQLite foreign keys and JOIN patterns
-- https://www.sqlite.org/foreignkeys.html
--------------------------------------------------------------------
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

--------------------------------------------------------------------
-- ORDERS TABLE 
-- Exists mainly to support linking returns to an order.
-- Reference: CS50 SQL table relationships
--------------------------------------------------------------------
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    order_number TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

--------------------------------------------------------------------
-- ORDER ITEMS TABLE (MINIMAL V1)
-- Optional for V1, but included for ERD completeness.
--------------------------------------------------------------------
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

--------------------------------------------------------------------
-- CONTENT POSTS TABLE
-- Admins can publish posts that appear on the public landing page.
-- Multi-tenant rule: each post belongs to a company.
--
-- References:
-- - SQLite text storage: https://www.sqlite.org/datatype3.html
-- - CS50 SQL table design: https://cs50.harvard.edu/x/2023/sql/
--------------------------------------------------------------------
CREATE TABLE content_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
