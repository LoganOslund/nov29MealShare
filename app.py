"""
Optimized Meal-Sharing Web Application
Flask backend with SQLite - MongoDB removed for performance
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'meal_sharing.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============= ROUTES =============

@app.route('/')
def index():
    """Home page showing all recipes"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use a subquery to pick one deterministic image per recipe
    recipes = cursor.execute("""
        SELECT
            r.recipe_id,
            r.name,
            r.instructions,
            r.prep_time_minutes,
            r.cost_estimate,
            r.created_at,
            img.file_path AS image_url,
            img.alt_text AS image_alt,
            4.5 AS avg_rating,
            0   AS review_count,
            COALESCE(GROUP_CONCAT(DISTINCT dt.tag_name), '') AS tags,
            u.name AS author_name
        FROM recipes r
        LEFT JOIN (
            SELECT recipe_id,
                   MIN(file_path) AS file_path,
                   MIN(alt_text) AS alt_text
            FROM images
            GROUP BY recipe_id
        ) AS img ON r.recipe_id = img.recipe_id
        LEFT JOIN users u ON r.author_id = u.user_id
        LEFT JOIN recipe_tags rt ON r.recipe_id = rt.recipe_id
        LEFT JOIN dietary_tags dt ON rt.tag_id = dt.tag_id
        GROUP BY
            r.recipe_id,
            r.name,
            r.instructions,
            r.prep_time_minutes,
            r.cost_estimate,
            r.created_at,
            img.file_path,
            img.alt_text,
            u.name
        ORDER BY r.name
    """).fetchall()

    conn.close()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Recipe detail page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get recipe details
    recipe = cursor.execute("""
        SELECT r.*, u.name AS author_name
        FROM recipes r
        LEFT JOIN users u ON r.author_id = u.user_id
        WHERE r.recipe_id = ?
    """, (recipe_id,)).fetchone()
    
    if not recipe:
        conn.close()
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    
    # Get images
    images = cursor.execute("""
        SELECT file_path, alt_text
        FROM images
        WHERE recipe_id = ?
        ORDER BY image_id
    """, (recipe_id,)).fetchall()
    
    # Get reviews
    reviews = cursor.execute("""
        SELECT r.*, u.name AS reviewer_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.user_id
        WHERE r.recipe_id = ?
        ORDER BY r.created_at DESC
    """, (recipe_id,)).fetchall()
    
    # Get ingredients
    ingredients = cursor.execute("""
        SELECT i.name, ri.quantity
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = ?
        ORDER BY i.name
    """, (recipe_id,)).fetchall()

    # Get all users for the "who is reviewing" dropdown
    users = cursor.execute("""
        SELECT user_id, name
        FROM users
        ORDER BY name
    """).fetchall()
    
    conn.close()
    
    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        images=images,
        reviews=reviews,
        ingredients=ingredients,
        users=users
    )

@app.route('/recipes')
def recipes():
    """All recipes page with filtering"""

    # These match the names in filter_recipes.html
    current_tag = request.args.get('tag', '').strip()
    current_max_prep_time = request.args.get('max_prep_time', type=int)
    current_ingredient = request.args.get('ingredient', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query with joins so we can filter by tag and ingredient,
    # and still get image + author + tags
    query = """
        SELECT 
            r.recipe_id,
            r.name,
            r.instructions,
            r.prep_time_minutes,
            r.cost_estimate,
            r.created_at,
            img.file_path AS image_url,
            img.alt_text AS image_alt,
            4.5 AS avg_rating,
            0   AS review_count,
            COALESCE(GROUP_CONCAT(DISTINCT dt.tag_name), '') AS tags,
            u.name AS author_name
        FROM recipes r
        LEFT JOIN (
            SELECT recipe_id,
                   MIN(file_path) AS file_path,
                   MIN(alt_text) AS alt_text
            FROM images
            GROUP BY recipe_id
        ) AS img ON r.recipe_id = img.recipe_id
        LEFT JOIN users u ON r.author_id = u.user_id
        LEFT JOIN recipe_tags rt ON r.recipe_id = rt.recipe_id
        LEFT JOIN dietary_tags dt ON rt.tag_id = dt.tag_id
        LEFT JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
        LEFT JOIN ingredients ing ON ri.ingredient_id = ing.ingredient_id
        WHERE 1 = 1
    """
    params = []

    # Tag filter (Dietary Preferences dropdown)
    if current_tag:
        query += " AND dt.tag_name = ?"
        params.append(current_tag)

    # Max prep time filter
    if current_max_prep_time is not None:
        query += " AND (r.prep_time_minutes IS NULL OR r.prep_time_minutes <= ?)"
        params.append(current_max_prep_time)

    # Ingredient text search
    if current_ingredient:
        query += " AND ing.name LIKE ?"
        params.append(f"%{current_ingredient}%")

    # Group + order (because of GROUP_CONCAT)
    query += """
        GROUP BY 
            r.recipe_id,
            r.name,
            r.instructions,
            r.prep_time_minutes,
            r.cost_estimate,
            r.created_at,
            img.file_path,
            img.alt_text,
            u.name
        ORDER BY r.name
    """

    recipes = cursor.execute(query, params).fetchall()

    # Tags for the dropdown
    all_tags = cursor.execute(
        "SELECT tag_name FROM dietary_tags ORDER BY tag_name"
    ).fetchall()

    conn.close()

    return render_template(
        'filter_recipes.html',
        recipes=recipes,
        all_tags=all_tags,
        current_tag=current_tag,
        current_max_prep_time=current_max_prep_time,
        current_ingredient=current_ingredient
    )

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    """Add new recipe, including tags, ingredients, and image"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # We need users + tags for both GET and POST (for redisplay on validation error)
    users = cursor.execute(
        "SELECT user_id, name FROM users ORDER BY name"
    ).fetchall()

    dietary_tags = cursor.execute(
        "SELECT tag_id, tag_name FROM dietary_tags ORDER BY tag_name"
    ).fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        instructions = request.form.get('instructions', '').strip()
        prep_time = request.form.get('prep_time', type=int)
        cost_estimate = request.form.get('cost_estimate', type=float)
        author_id = request.form.get('author_id', type=int) or None

        image_url = request.form.get('image_url', '').strip()
        image_alt = request.form.get('image_alt', '').strip()

        # Ingredients: one per line, format "name - quantity"
        ingredients_text = request.form.get('ingredients_text', '').strip()

        selected_tag_ids = request.form.getlist('tags')  # list of strings

        if not name or not instructions:
            flash('Name and instructions are required', 'error')
            conn.close()
            return render_template(
                'add_recipe.html',
                users=users,
                dietary_tags=dietary_tags
            )

        # Insert recipe
        cursor.execute("""
            INSERT INTO recipes (name, instructions, prep_time_minutes, cost_estimate, author_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, instructions, prep_time, cost_estimate, author_id))
        recipe_id = cursor.lastrowid

        # Insert image if provided
        if image_url:
            cursor.execute("""
                INSERT INTO images (recipe_id, file_path, alt_text)
                VALUES (?, ?, ?)
            """, (recipe_id, image_url, image_alt or name))

        # Insert tags (recipe_tags)
        for tag_id_str in selected_tag_ids:
            try:
                tag_id = int(tag_id_str)
            except ValueError:
                continue
            cursor.execute("""
                INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id)
                VALUES (?, ?)
            """, (recipe_id, tag_id))

        # Insert ingredients
        if ingredients_text:
            lines = [line.strip() for line in ingredients_text.splitlines() if line.strip()]
            for line in lines:
                # Expect "name - quantity", but be forgiving
                if '-' in line:
                    ing_name, quantity = [part.strip() for part in line.split('-', 1)]
                else:
                    ing_name, quantity = line.strip(), ''

                if not ing_name:
                    continue

                # Ensure ingredient exists in ingredients table
                cursor.execute("""
                    INSERT OR IGNORE INTO ingredients (name) VALUES (?)
                """, (ing_name,))
                
                cursor.execute("""
                    SELECT ingredient_id FROM ingredients WHERE name = ?
                """, (ing_name,))
                row = cursor.fetchone()
                if not row:
                    continue
                ingredient_id = row['ingredient_id']

                cursor.execute("""
                    INSERT OR IGNORE INTO recipe_ingredients (recipe_id, ingredient_id, quantity)
                    VALUES (?, ?, ?)
                """, (recipe_id, ingredient_id, quantity))

        conn.commit()
        conn.close()

        flash('Recipe added successfully!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    # GET request - show form
    conn.close()
    return render_template(
        'add_recipe.html',
        users=users,
        dietary_tags=dietary_tags
    )

@app.route('/add_review/<int:recipe_id>', methods=['POST'])
def add_review(recipe_id):
    """Add a review for a recipe with selected user"""
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    user_id = request.form.get('user_id', type=int)

    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5)', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    if not user_id:
        flash('Please select who is leaving the review.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (recipe_id, user_id, rating, comment))
    conn.commit()
    conn.close()
    
    flash('Review added successfully!', 'success')
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE_PATH):
        from database.init_db import init_database
        init_database()
    
    # Run in production mode for maximum performance
    app.run(debug=False, host='0.0.0.0', port=5005, threaded=True)
