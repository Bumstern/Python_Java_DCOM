
INSERT INTO categories (name) VALUES ('General'), ('Anime'), ('People');
INSERT INTO tags (name) VALUES ('nature'), ('space'), ('cars');
INSERT INTO resolutions (resolution) VALUES ('1920x1080'), ('2560x1440'), ('3840x2160');

SELECT * FROM category WHERE name = "";
INSERT INTO user_categories (user_login, category_id) VALUES ('rus', (SELECT id FROM categories WHERE name = 'Anime'));
