"""
Optimized Meal-Sharing Web Application
Flask backend with SQLite - MongoDB removed for performance
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime

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
    """Home page showing all recipes - optimized for performance"""
    conn = get_db_connection()
    # Optimized query with all fields the template needs
    recipes = conn.execute('''
        SELECT r.recipe_id, r.name, r.instructions, r.prep_time_minutes, 
               r.cost_estimate, r.created_at,
               i.file_path as image_url, i.alt_text as image_alt,
               4.5 as avg_rating,
               0 as review_count,
               '' as tags
        FROM recipes r
        LEFT JOIN images i ON r.recipe_id = i.recipe_id
        ORDER BY r.name
    ''').fetchall()
    conn.close()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Recipe detail page"""
    conn = get_db_connection()
    
    # Get recipe details
    recipe = conn.execute('''
        SELECT r.*, u.name as author_name
        FROM recipes r
        LEFT JOIN users u ON r.author_id = u.user_id
        WHERE r.recipe_id = ?
    ''', (recipe_id,)).fetchone()
    
    if not recipe:
        conn.close()
        flash('Recipe not found', 'error')
        return redirect(url_for('index'))
    
    # Get images
    images = conn.execute('''
        SELECT file_path, alt_text
        FROM images
        WHERE recipe_id = ?
    ''', (recipe_id,)).fetchall()
    
    # Get reviews
    reviews = conn.execute('''
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.user_id
        WHERE r.recipe_id = ?
        ORDER BY r.created_at DESC
    ''', (recipe_id,)).fetchall()
    
    # Get ingredients
    ingredients = conn.execute('''
        SELECT i.name, ri.quantity
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = ?
    ''', (recipe_id,)).fetchall()

    # Get users for the "Reviewer" dropdown
    users = conn.execute('''
        SELECT user_id, name
        FROM users
        ORDER BY name
    ''').fetchall()
    
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
    query = '''
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
            0 AS review_count,
            COALESCE(GROUP_CONCAT(DISTINCT dt.tag_name), '') AS tags,
            u.name AS author_name
        FROM recipes r
        LEFT JOIN images img ON r.recipe_id = img.recipe_id
        LEFT JOIN users u ON r.author_id = u.user_id
        LEFT JOIN recipe_tags rt ON r.recipe_id = rt.recipe_id
        LEFT JOIN dietary_tags dt ON rt.tag_id = dt.tag_id
        LEFT JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
        LEFT JOIN ingredients ing ON ri.ingredient_id = ing.ingredient_id
        WHERE 1 = 1
    '''
    params = []

    # Tag filter (Dietary Preferences dropdown)
    if current_tag:
        query += ' AND dt.tag_name = ?'
        params.append(current_tag)

    # Max prep time filter
    if current_max_prep_time is not None:
        query += ' AND (r.prep_time_minutes IS NULL OR r.prep_time_minutes <= ?)'
        params.append(current_max_prep_time)

    # Ingredient text search
    if current_ingredient:
        query += ' AND ing.name LIKE ?'
        params.append(f'%{current_ingredient}%')

    # Group + order (because of GROUP_CONCAT)
    query += '''
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
    '''

    recipes = cursor.execute(query, params).fetchall()

    # Tags for the dropdown
    all_tags = cursor.execute(
        'SELECT tag_name FROM dietary_tags ORDER BY tag_name'
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
    """Add new recipe"""

    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        instructions = request.form['instructions']
        prep_time = request.form.get('prep_time', type=int)
        cost_estimate = request.form.get('cost_estimate', type=float)
        author_id = request.form.get('author_id', type=int) or 1

        # Get selected tag IDs (checkboxes)
        tag_ids = request.form.getlist('tags')

        if not name or not instructions:
            flash('Name and instructions are required', 'error')
            users = conn.execute('SELECT user_id, name FROM users ORDER BY name').fetchall()
            all_tags = conn.execute('SELECT tag_id, tag_name FROM dietary_tags ORDER BY tag_name').fetchall()
            conn.close()
            return render_template('add_recipe.html', users=users, all_tags=all_tags)

        cursor = conn.cursor()

        # Insert recipe
        cursor.execute('''
            INSERT INTO recipes (name, instructions, prep_time_minutes, cost_estimate, author_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, instructions, prep_time, cost_estimate, author_id))

        recipe_id = cursor.lastrowid

        # Insert tags
        for tag_id in tag_ids:
            cursor.execute(
                'INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)',
                (recipe_id, tag_id)
            )

        conn.commit()
        conn.close()

        flash('Recipe added successfully!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    # GET request — Show form
    users = conn.execute('SELECT user_id, name FROM users ORDER BY name').fetchall()
    all_tags = conn.execute('SELECT tag_id, tag_name FROM dietary_tags ORDER BY tag_name').fetchall()
    conn.close()

    return render_template('add_recipe.html', users=users, all_tags=all_tags)


@app.route('/add_review/<int:recipe_id>', methods=['POST'])
def add_review(recipe_id):
    """Add a review for a recipe"""
    user_id = request.form.get('user_id', type=int)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not user_id:
        flash('Please select your name.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5)', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    ''', (recipe_id, user_id, rating, comment))
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