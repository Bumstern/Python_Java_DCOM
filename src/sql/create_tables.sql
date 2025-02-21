--drop table if exists users;
--drop table if exists user_resolutions, resolutions;

CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) UNIQUE PRIMARY KEY NOT NULL,
    password VARCHAR(512) NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS resolutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE
);

-- Связь многие ко многим между пользователями и категориями
CREATE TABLE IF NOT EXISTS user_categories (
    user_login VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (user_login, category_id)
);

-- Связь многие ко многим между пользователями и тэгами
CREATE TABLE IF NOT EXISTS user_tags (
    user_login VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (user_login, tag_id)
);

-- Связь многие ко многим между пользователями и разрешениями
CREATE TABLE IF NOT EXISTS user_resolutions (
    user_login VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
    resolution_id INT REFERENCES resolutions(id) ON DELETE CASCADE,
    PRIMARY KEY (user_login, resolution_id)
);
