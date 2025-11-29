"""
Database initialization script for Meal-Sharing Web Application
Creates SQLite database with all required tables and initial data
"""

import sqlite3
import os

def init_database():
    """Initialize the SQLite database with schema and sample data"""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'meal_sharing.db')
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # COMPLETELY CLEAR ALL EXISTING DATA
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DROP TABLE IF EXISTS favorites")
    cursor.execute("DROP TABLE IF EXISTS reviews") 
    cursor.execute("DROP TABLE IF EXISTS images")
    cursor.execute("DROP TABLE IF EXISTS recipe_tags")
    cursor.execute("DROP TABLE IF EXISTS recipe_ingredients")
    cursor.execute("DROP TABLE IF EXISTS dietary_tags")
    cursor.execute("DROP TABLE IF EXISTS ingredients")
    cursor.execute("DROP TABLE IF EXISTS recipes")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create Users table
    cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create Recipes table
    cursor.execute("""
    CREATE TABLE recipes (
        recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        instructions TEXT NOT NULL,
        prep_time_minutes INTEGER,
        cost_estimate REAL,
        author_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)
    
    # Create Ingredients table
    cursor.execute("""
    CREATE TABLE ingredients (
        ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    
    # Create RecipeIngredients join table
    cursor.execute("""
    CREATE TABLE recipe_ingredients (
        recipe_id INTEGER NOT NULL,
        ingredient_id INTEGER NOT NULL,
        quantity TEXT,
        PRIMARY KEY (recipe_id, ingredient_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE
    );
    """)
    
    # Create Dietary Tags table
    cursor.execute("""
    CREATE TABLE dietary_tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT UNIQUE NOT NULL
    );
    """)
    
    # Create RecipeTags join table
    cursor.execute("""
    CREATE TABLE recipe_tags (
        recipe_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (recipe_id, tag_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES dietary_tags(tag_id) ON DELETE CASCADE
    );
    """)
    
    # Create Images table
    cursor.execute("""
    CREATE TABLE images (
        image_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        alt_text TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
    );
    """)
    
    # Create Reviews table
    cursor.execute("""
    CREATE TABLE reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        user_id INTEGER,
        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)
    
    # Create Favorites table
    cursor.execute("""
    CREATE TABLE favorites (
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        date_saved DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, recipe_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
    );
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipes_prep_time ON recipes(prep_time_minutes);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_tags_tag ON recipe_tags(tag_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ing ON recipe_ingredients(ingredient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorites_recipe ON favorites(recipe_id);")
    
    # Insert dietary tags
    dietary_tags = [
        ('vegetarian',),
        ('vegan',),
        ('gluten-free',),
        ('halal',),
        ('keto',),
        ('dairy-free',),
        ('spicy',),
        ('healthy',),
        ('protein-rich',),
        ('low-carb',),
        ('comfort-food',),
        ('asian',),
        ('mediterranean',),
        ('mexican',),
        ('italian',),
        ('american',)
    ]
    cursor.executemany("INSERT OR IGNORE INTO dietary_tags (tag_name) VALUES (?)", dietary_tags)
    
    # Insert sample users
    sample_users = [
        ('Alice Johnson', 'alice@campus.edu'),
        ('Bob Smith', 'bob@campus.edu'),
        ('Charlie Davis', 'charlie@campus.edu'),
        ('Diana Martinez', 'diana@campus.edu')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)", sample_users)
    
    # Insert sample ingredients
    sample_ingredients = [
        ('Chicken Breast',), ('Rice',), ('Broccoli',), ('Olive Oil',), ('Garlic',),
        ('Soy Sauce',), ('Tofu',), ('Bell Peppers',), ('Onions',), ('Tomatoes',),
        ('Pasta',), ('Cheese',), ('Spinach',), ('Black Beans',), ('Avocado',),
        ('Lime',), ('Cilantro',), ('Tortillas',), ('Ground Beef',), ('Lettuce',),
        ('Sourdough Bread',), ('Feta Cheese',), ('Cherry Tomatoes',), ('Balsamic Glaze',),
        ('Jasmine Rice',), ('Mixed Vegetables',), ('Sesame Oil',), ('Eggs',),
        ('Peas',), ('Carrots',), ('Green Onions',), ('Quinoa',), ('Chickpeas',),
        ('Tahini',), ('Corn Tortillas',), ('Cabbage',), ('Spicy Mayo',),
        ('Mozzarella Cheese',), ('Basil',), ('San Marzano Tomatoes',), ('Mushrooms',),
        ('Red Onions',), ('Olives',), ('Pepperoni',), ('Sausage',), ('Ham',), ('Bacon',),
        ('Teriyaki Sauce',), ('Beef Bulgogi',), ('Kimchi',), ('Sesame Seeds',),
        ('Sweet Potato',), ('Kale',), ('Lemon',), ('Rice Noodles',), ('Shrimp',),
        ('Bean Sprouts',), ('Peanuts',), ('Tamarind Sauce',), ('Miso',), ('Soft-boiled Egg',),
        ('Corn',), ('Romaine Lettuce',), ('Parmesan',), ('Croutons',), ('Caesar Dressing',),
        ('Mixed Greens',), ('Cucumber',), ('Greek Vinaigrette',), ('Mandarin Oranges',),
        ('Sesame Dressing',), ('Dried Cranberries',), ('Almonds',), ('Blue Cheese',),
        ('Ranch Dressing',), ('Sweet Potatoes',), ('Chipotle Aioli',), ('Tortilla Chips',),
        ('Jalapeños',), ('Sour Cream',), ('Guacamole',), ('Cauliflower',), ('Buffalo Sauce',)
    ]
    cursor.executemany("INSERT OR IGNORE INTO ingredients (name) VALUES (?)", sample_ingredients)
    
    # Insert only your 9 specified recipes - completely fresh start
    sample_recipes = [
        ('Margherita Pizza', 'Classic pizza with fresh mozzarella, basil, and San Marzano tomato sauce.', 35, 18.95, 1),
        ('Caesar Salad', 'Crisp romaine lettuce with parmesan, croutons, and classic Caesar dressing.', 10, 11.95, 1),
        ('Grilled Chicken Sandwich', 'Juicy grilled chicken breast with fresh lettuce and tomato on brioche bun.', 20, 14.95, 1),
        ('Vegetarian Bowl', 'Nutritious bowl with quinoa, roasted vegetables, chickpeas, and tahini dressing.', 30, 15.00, 2),
        ('Sweet Potato Fries', 'Crispy sweet potato fries served with chipotle aioli.', 15, 7.95, 2),
        ('Grilled Fish Tacos', 'Fresh grilled fish with cabbage slaw and lime crema in soft tortillas.', 25, 17.50, 1),
        ('Chicken Protein Bowl', 'High-protein bowl with grilled chicken, quinoa, and fresh vegetables.', 28, 16.95, 1),
        ('Crispy Fries', 'Golden crispy french fries seasoned to perfection.', 12, 6.95, 2),
        ('Veggie Pizza', 'Delicious vegetarian pizza loaded with fresh vegetables and cheese.', 32, 19.95, 2)
    ]
    cursor.executemany(
        "INSERT INTO recipes (name, instructions, prep_time_minutes, cost_estimate, author_id) VALUES (?, ?, ?, ?, ?)",
        sample_recipes
    )
    
    # Add your exact image URLs to each recipe
    recipe_images = [
        (1, 'https://ooni.com/cdn/shop/articles/20220211142347-margherita-9920_ba86be55-674e-4f35-8094-2067ab41a671.jpg?v=1737104576&width=400', 'Margherita Pizza'),
        (2, 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=300&fit=crop&auto=format', 'Caesar Salad'),
        (3, 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop&auto=format', 'Grilled Chicken Sandwich'),
        (4, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop&auto=format', 'Vegetarian Bowl'),
        (5, 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=400&h=300&fit=crop&auto=format', 'Sweet Potato Fries'),
        (6, 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop&auto=format', 'Grilled Fish Tacos'),
        (7, 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&h=300&fit=crop&auto=format', 'Chicken Protein Bowl'),
        (8, 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=300&fit=crop&auto=format', 'Crispy Fries'),
        (9, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop&auto=format', 'Veggie Pizza')
    ]
    cursor.executemany("INSERT INTO images (recipe_id, file_path, alt_text) VALUES (?, ?, ?)", recipe_images)
    
    # Insert sample recipe-ingredient relationships
    # Chicken Stir Fry (recipe_id: 1)
    recipe_ingredients_data = [
        (1, 1, '2 breasts'),
        (1, 2, '2 cups'),
        (1, 3, '1 cup'),
        (1, 4, '2 tbsp'),
        (1, 5, '3 cloves'),
        (1, 6, '3 tbsp'),
        # Vegetarian Buddha Bowl (recipe_id: 2)
        (2, 2, '1 cup'),
        (2, 3, '1 cup'),
        (2, 8, '2 peppers'),
        (2, 15, '1 avocado'),
        (2, 4, '2 tbsp'),
        # Spicy Tofu Tacos (recipe_id: 3)
        (3, 7, '1 block'),
        (3, 18, '8 tortillas'),
        (3, 20, '2 cups'),
        (3, 10, '2 tomatoes'),
        (3, 17, '1/4 cup'),
        # Classic Pasta Primavera (recipe_id: 4)
        (4, 11, '1 lb'),
        (4, 3, '1 cup'),
        (4, 10, '2 tomatoes'),
        (4, 13, '2 cups'),
        (4, 12, '1/2 cup'),
        # Beef Burrito Bowl (recipe_id: 5)
        (5, 19, '1 lb'),
        (5, 2, '2 cups'),
        (5, 14, '1 can'),
        (5, 20, '2 cups'),
        (5, 15, '1 avocado')
    ]
    # Skip recipe ingredients for clean setup
    pass
    
    # Insert sample recipe tags (updated for 9 recipes)
    recipe_tags_data = [
        # Margherita Pizza (1)
        (1, 1), (1, 15),  # vegetarian, italian
        # Caesar Salad (2)
        (2, 1), (2, 10),  # vegetarian, low-carb
        # Grilled Chicken Sandwich (3)
        (3, 9),  # protein-rich
        # Vegetarian Bowl (4)
        (4, 1), (4, 8), (4, 3),  # vegetarian, healthy, gluten-free
        # Sweet Potato Fries (5)
        (5, 1), (5, 8),  # vegetarian, healthy
        # Grilled Fish Tacos (6)
        (6, 14), (6, 9),  # mexican, protein-rich
        # Chicken Protein Bowl (7)
        (7, 9), (7, 8),  # protein-rich, healthy
        # Crispy Fries (8)
        (8, 1),  # vegetarian
        # Veggie Pizza (9)
        (9, 1), (9, 15)  # vegetarian, italian
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)",
        recipe_tags_data
    )
    
    # Insert sample reviews
    sample_reviews = [
        (1, 1, 5, 'Amazing flavor! Quick and easy to make.'),
        (1, 2, 4, 'Good recipe, but I added more vegetables.'),
        (2, 3, 5, 'Perfect meal prep option. Healthy and delicious!'),
        (3, 2, 4, 'Love the crispy tofu. Will make again!'),
        (4, 4, 5, 'Classic comfort food. My go-to pasta recipe.')
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO reviews (recipe_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
        sample_reviews
    )
    
    # Insert sample images with real food URLs
    sample_images = [
        (1, 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&h=300&fit=crop', 'Delicious avocado toast with cherry tomatoes'),
        (2, 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop', 'Colorful vegetable fried rice'),
        (3, 'https://images.unsplash.com/photo-1603064752734-4c48eff53d05?w=400&h=300&fit=crop', 'Traditional chicken fried rice'),
        (4, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop', 'Nutritious vegetarian Buddha bowl'),
        (5, 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'Spicy tofu tacos with fresh toppings'),
        (6, 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&h=300&fit=crop', 'Classic Margherita pizza'),
        (7, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop', 'Loaded meat lovers pizza'),
        (8, 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=300&fit=crop', 'Teriyaki chicken rice bowl'),
        (9, 'https://images.unsplash.com/photo-1559314809-0f31657def5e?w=400&h=300&fit=crop', 'Traditional pad thai noodles'),
        (10, 'https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=400&h=300&fit=crop', 'Rich vegetarian ramen bowl'),
        (11, 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=300&fit=crop', 'Fresh Caesar salad with croutons'),
        (12, 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop', 'Mediterranean Greek salad'),
        (13, 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop', 'Nutritious kale superfood salad'),
        (14, 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=400&h=300&fit=crop', 'Crispy sweet potato fries'),
        (15, 'https://images.unsplash.com/photo-1576402794548-c805923dd4e1?w=400&h=300&fit=crop', 'Spicy buffalo cauliflower')
    ]
    # cursor.executemany(
    #     "INSERT OR IGNORE INTO images (recipe_id, file_path, alt_text) VALUES (?, ?, ?)",
    #     sample_images
    # )

    # Minimal favorites for clean setup
    sample_favorites = [
        (1, 1), (1, 2), (2, 4), (2, 5)
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO favorites (user_id, recipe_id) VALUES (?, ?)",
        sample_favorites
    )
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at: {db_path}")
    return db_path

if __name__ == "__main__":
    init_database()
