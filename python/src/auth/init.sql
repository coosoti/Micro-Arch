-- 1. Create a dedicated user
CREATE USER IF NOT EXISTS 'auth_user'@'localhost' IDENTIFIED BY 'Auth123!';

-- 2. Create the database
CREATE DATABASE IF NOT EXISTS auth;

-- 3. Grant permissions to the user
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';

-- 4. Switch to the new database
USE auth;

-- 5. Create the user table
CREATE TABLE IF NOT EXISTS user (
                                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                    email VARCHAR(255) NOT NULL UNIQUE,
    password CHAR(64) NOT NULL, -- SHA-256 hash is 64 hex characters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- 6. Insert a test user with SHA-256 hashed password
-- WARNING: This is just for testing. For real security, hash passwords in your app using bcrypt or similar.
INSERT INTO user (email, password) VALUES (
                                              'charles@email.com',
                                              SHA2('admin123', 256)
                                          );