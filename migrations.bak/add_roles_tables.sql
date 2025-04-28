-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create role_permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

-- Add role_id column to users table
ALTER TABLE users ADD COLUMN role_id INTEGER;

-- Insert default roles
INSERT INTO roles (name, description) VALUES ('super_admin', 'Super Administrator with full access');
INSERT INTO roles (name, description) VALUES ('office_admin', 'Office Administrator with access to manage office resources');
INSERT INTO roles (name, description) VALUES ('standard_user', 'Standard user with basic access');
INSERT INTO roles (name, description) VALUES ('limited_user', 'Limited user with restricted access'); 