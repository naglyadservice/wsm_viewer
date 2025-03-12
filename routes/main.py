from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from db.database import create_connection

main_bp = Blueprint("main", __name__)

def get_post_data(sort_by=None):
    """Получает посты с услугами"""
    connection = create_connection()
    if not connection:
        return []

    cursor = connection.cursor()
    
    query = """
        SELECT DISTINCT pm.post_id, p.post_title
        FROM wp_postmeta pm
        JOIN wp_posts p ON pm.post_id = p.id
        WHERE pm.meta_key = 'iscolourful'
    """

    query += " ORDER BY p.post_title ASC" if sort_by == "title" else " ORDER BY pm.post_id ASC"

    cursor.execute(query)
    posts = cursor.fetchall()
    
    for post in posts:
        cursor.execute("""
            SELECT DISTINCT
                p.meta_id,
                t.meta_value as title,
                p.meta_value as price
            FROM 
                (SELECT * FROM wp_postmeta WHERE post_id = %s AND meta_key = 'title') t
                JOIN 
                (SELECT * FROM wp_postmeta WHERE post_id = %s AND meta_key = 'price') p
                ON t.meta_id = p.meta_id - 1
            ORDER BY t.meta_id
        """, (post["post_id"], post["post_id"]))
        post["services"] = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return posts

@main_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        meta_id = request.form.get("meta_id")
        new_price = request.form.get("new_price")

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE wp_postmeta SET meta_value = %s WHERE meta_id = %s", (new_price, meta_id))
        connection.commit()

        cursor.close()
        connection.close()
        return jsonify({"success": True})

    sort_by = request.args.get("sort", "id")
    posts = get_post_data(sort_by)
    return render_template("index.html", posts=posts, sort_by=sort_by)

@main_bp.route("/price-list", methods=["GET"])
@login_required
def price_list():
    sort_by = request.args.get("sort", "id")
    posts = get_post_data(sort_by)
    return render_template("price_list.html", posts=posts, sort_by=sort_by)
