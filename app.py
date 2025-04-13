import os
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_for_testing")

# Configure database
DB_PATH = os.path.join(os.path.dirname(__file__), 'farm_management.db')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    
def init_db():
    """Initialize the database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        farm_name TEXT,
        location TEXT,
        farm_type TEXT,
        date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        quantity INTEGER NOT NULL,
        unit TEXT,
        min_quantity INTEGER DEFAULT 0,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crop_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_type TEXT NOT NULL,
        description TEXT,
        date DATE NOT NULL,
        field_location TEXT,
        crop_type TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        priority INTEGER DEFAULT 3,
        is_recurring INTEGER DEFAULT 0,
        interval_days INTEGER,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER,
        inventory_id INTEGER,
        quantity_required REAL,
        FOREIGN KEY (activity_id) REFERENCES activities (id),
        FOREIGN KEY (inventory_id) REFERENCES inventory (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        date DATE NOT NULL,
        temperature REAL,
        humidity REAL,
        precipitation REAL,
        wind_speed REAL,
        conditions TEXT,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create community_posts table for the community section
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS community_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create tags table for different categories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    ''')
    
    # Create post_tags table for tagging system
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS post_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        FOREIGN KEY (post_id) REFERENCES community_posts (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    )
    ''')
    
    # Create comments table for post responses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES community_posts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create user_connections table to implement the graph data structure
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        connected_user_id INTEGER NOT NULL,
        connection_type TEXT DEFAULT 'friend',
        connection_strength INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (connected_user_id) REFERENCES users (id)
    )
    ''')
    
    # Create private_messages table for user-to-user messaging
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id)
    )
    ''')
    
    # Insert default activity types
    default_activities = ['Planting', 'Irrigation', 'Fertilizing', 'Pesticide Application', 
                         'Harvesting', 'Equipment Maintenance', 'Inspection', 'Weeding']
    for activity in default_activities:
        cursor.execute('INSERT OR IGNORE INTO activity_types (name) VALUES (?)', (activity,))
    
    # Insert default crop types
    default_crops = ['Wheat', 'Rice', 'Corn', 'Soybean', 'Potato', 'Tomato']
    for crop in default_crops:
        cursor.execute('INSERT OR IGNORE INTO crop_types (name) VALUES (?)', (crop,))
        
    # Insert default tags for community posts
    default_tags = [
        ('Pest Disease', 'issue'),
        ('Crop Management', 'technique'),
        ('Fertilizer', 'input'),
        ('Wheat', 'crop'),
        ('Corn', 'crop'),
        ('Rice', 'crop'),
        ('Soybean', 'crop'),
        ('Irrigation', 'technique'),
        ('Organic Farming', 'approach'),
        ('Market Prices', 'business'),
        ('Equipment', 'tool'),
        ('Weather Impact', 'environment')
    ]
    for tag_name, category in default_tags:
        cursor.execute('INSERT OR IGNORE INTO tags (name, category) VALUES (?, ?)', (tag_name, category))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        from models import User
        return User(
            id=user['id'], 
            username=user['username'], 
            email=user['email'],
            password_hash=user['password_hash'],
            full_name=user['full_name'],
            farm_name=user['farm_name'],
            location=user['location'],
            farm_type=user['farm_type']
        )
    return None

@app.route('/login')
def login():
    """Render the login page."""
    # If user is already logged in, redirect to home
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('login.html')
    
@app.route('/')
def root():
    """Direct users to login or home page."""
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/home')
def index():
    """Render the home page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/weather-old')
def weather_old():
    """Legacy weather page route for backward compatibility."""
    return redirect(url_for('weather'))

@app.route('/activity-old')
def activity_old():
    """Legacy activity page route for backward compatibility."""
    return redirect(url_for('activity'))

@app.route('/community')
def community():
    """Render the community page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    
    # Get all available tags for filtering posts
    tags = conn.execute('SELECT * FROM tags ORDER BY category, name').fetchall()
    
    # Get recent posts with user info
    posts = conn.execute('''
        SELECT p.*, u.username, u.farm_name, u.location,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM community_posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.status = 'active'
        ORDER BY p.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get post tags
    post_ids = [post['id'] for post in posts]
    post_tags = {}
    
    if post_ids:
        post_id_placeholders = ','.join(['?'] * len(post_ids))
        query = f'''
            SELECT pt.post_id, t.id as tag_id, t.name as tag_name, t.category
            FROM post_tags pt
            JOIN tags t ON pt.tag_id = t.id
            WHERE pt.post_id IN ({post_id_placeholders})
        '''
        tag_results = conn.execute(query, post_ids).fetchall()
        
        # Group tags by post_id
        for tag in tag_results:
            if tag['post_id'] not in post_tags:
                post_tags[tag['post_id']] = []
            post_tags[tag['post_id']].append({
                'id': tag['tag_id'],
                'name': tag['tag_name'],
                'category': tag['category']
            })
    
    # Get friend recommendations if user is logged in
    friend_recommendations = []
    
    if user_id:
        # First, build the graph from the database
        from models import CommunityGraph
        
        graph = CommunityGraph()
        connections = conn.execute('''
            SELECT * FROM user_connections
            WHERE user_id = ? OR connected_user_id = ?
        ''', (user_id, user_id)).fetchall()
        
        # Add all connections to the graph
        for conn_row in connections:
            graph.add_connection(
                conn_row['user_id'], 
                conn_row['connected_user_id'], 
                conn_row['connection_strength']
            )
        
        # Find second-degree connections (friends of friends)
        recommendations = graph.find_friend_recommendations(user_id)
        
        if recommendations:
            # Get user details for display
            user_ids = [r['user_id'] for r in recommendations]
            user_id_placeholders = ','.join(['?'] * len(user_ids))
            
            query = f'''
                SELECT id, username, farm_name, location, farm_type
                FROM users
                WHERE id IN ({user_id_placeholders})
            '''
            
            user_details = conn.execute(query, user_ids).fetchall()
            
            # Create a lookup for user details
            user_details_dict = {user['id']: user for user in user_details}
            
            # Combine recommendations with user details
            for rec in recommendations:
                user_detail = user_details_dict.get(rec['user_id'])
                if user_detail:
                    friend_recommendations.append({
                        'user_id': rec['user_id'],
                        'username': user_detail['username'],
                        'farm_name': user_detail['farm_name'],
                        'location': user_detail['location'],
                        'farm_type': user_detail['farm_type'],
                        'score': rec['score'],
                        'connection_path': rec['path']
                    })
    
    conn.close()
    
    return render_template('community.html', 
                          posts=posts,
                          tags=tags,
                          post_tags=post_tags,
                          friend_recommendations=friend_recommendations)


@app.route('/community/post/new', methods=['GET'])
def new_post_form():
    """Render the new post form."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    tags = conn.execute('SELECT * FROM tags ORDER BY category, name').fetchall()
    conn.close()
    
    return render_template('community_new_post.html', tags=tags)


@app.route('/community/post/new', methods=['POST'])
def create_post():
    """Create a new community post."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    title = request.form.get('title')
    content = request.form.get('content')
    selected_tags = request.form.getlist('tags')
    
    if not title or not content or not selected_tags:
        flash('Please provide a title, content, and at least one tag.')
        return redirect(url_for('new_post_form'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert the post
    cursor.execute(
        'INSERT INTO community_posts (user_id, title, content) VALUES (?, ?, ?)',
        (user_id, title, content)
    )
    
    # Get the post ID
    post_id = cursor.lastrowid
    
    # Add tags
    for tag_id in selected_tags:
        cursor.execute(
            'INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)',
            (post_id, tag_id)
        )
    
    conn.commit()
    conn.close()
    
    flash('Your post has been published successfully!')
    return redirect(url_for('community'))


@app.route('/community/post/<int:post_id>')
def view_post(post_id):
    """View a single community post with comments."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get post details with author info
    post = conn.execute('''
        SELECT p.*, u.username, u.farm_name, u.location
        FROM community_posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ? AND p.status = 'active'
    ''', (post_id,)).fetchone()
    
    if not post:
        conn.close()
        flash('Post not found.')
        return redirect(url_for('community'))
    
    # Update view count
    conn.execute(
        'UPDATE community_posts SET views = views + 1 WHERE id = ?',
        (post_id,)
    )
    
    # Get post tags
    tags = conn.execute('''
        SELECT t.id, t.name, t.category
        FROM post_tags pt
        JOIN tags t ON pt.tag_id = t.id
        WHERE pt.post_id = ?
    ''', (post_id,)).fetchall()
    
    # Get comments with user info
    comments = conn.execute('''
        SELECT c.*, u.username, u.farm_name
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()
    
    conn.commit()
    conn.close()
    
    return render_template('community_post.html', 
                          post=post,
                          tags=tags,
                          comments=comments)


@app.route('/community/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    content = request.form.get('comment')
    
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('view_post', post_id=post_id))
    
    conn = get_db_connection()
    
    # Check if post exists
    post = conn.execute(
        'SELECT * FROM community_posts WHERE id = ? AND status = "active"',
        (post_id,)
    ).fetchone()
    
    if not post:
        conn.close()
        flash('Post not found.')
        return redirect(url_for('community'))
    
    # Insert the comment
    conn.execute(
        'INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)',
        (post_id, user_id, content)
    )
    
    # Update connection strength between commenter and post author
    if user_id != post['user_id']:
        # Check if a connection already exists
        existing_connection = conn.execute('''
            SELECT * FROM user_connections 
            WHERE (user_id = ? AND connected_user_id = ?) OR (user_id = ? AND connected_user_id = ?)
        ''', (user_id, post['user_id'], post['user_id'], user_id)).fetchone()
        
        if existing_connection:
            # Increase connection strength
            conn.execute('''
                UPDATE user_connections
                SET connection_strength = connection_strength + 1
                WHERE id = ?
            ''', (existing_connection['id'],))
        else:
            # Create new connection
            conn.execute('''
                INSERT INTO user_connections (user_id, connected_user_id, connection_type, connection_strength)
                VALUES (?, ?, ?, ?)
            ''', (user_id, post['user_id'], 'comment', 1))
    
    conn.commit()
    conn.close()
    
    flash('Your comment has been added.')
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/community/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like a community post."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    
    # Check if post exists
    post = conn.execute(
        'SELECT * FROM community_posts WHERE id = ? AND status = "active"',
        (post_id,)
    ).fetchone()
    
    if not post:
        conn.close()
        flash('Post not found.')
        return redirect(url_for('community'))
    
    # Update like count
    conn.execute(
        'UPDATE community_posts SET likes = likes + 1 WHERE id = ?',
        (post_id,)
    )
    
    # Update connection strength between liker and post author
    if user_id != post['user_id']:
        # Check if a connection already exists
        existing_connection = conn.execute('''
            SELECT * FROM user_connections 
            WHERE (user_id = ? AND connected_user_id = ?) OR (user_id = ? AND connected_user_id = ?)
        ''', (user_id, post['user_id'], post['user_id'], user_id)).fetchone()
        
        if existing_connection:
            # Increase connection strength
            conn.execute('''
                UPDATE user_connections
                SET connection_strength = connection_strength + 1
                WHERE id = ?
            ''', (existing_connection['id'],))
        else:
            # Create new connection
            conn.execute('''
                INSERT INTO user_connections (user_id, connected_user_id, connection_type, connection_strength)
                VALUES (?, ?, ?, ?)
            ''', (user_id, post['user_id'], 'like', 1))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/community/tag/<int:tag_id>')
def posts_by_tag(tag_id):
    """Show all posts with a specific tag."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get tag info
    tag = conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,)).fetchone()
    
    if not tag:
        conn.close()
        flash('Tag not found.')
        return redirect(url_for('community'))
    
    # Get posts with this tag
    posts = conn.execute('''
        SELECT p.*, u.username, u.farm_name, u.location,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM community_posts p
        JOIN users u ON p.user_id = u.id
        JOIN post_tags pt ON p.id = pt.post_id
        WHERE pt.tag_id = ? AND p.status = 'active'
        ORDER BY p.created_at DESC
    ''', (tag_id,)).fetchall()
    
    # Get all tags
    all_tags = conn.execute('SELECT * FROM tags ORDER BY category, name').fetchall()
    
    # Get post tags
    post_ids = [post['id'] for post in posts]
    post_tags = {}
    
    if post_ids:
        post_id_placeholders = ','.join(['?'] * len(post_ids))
        query = f'''
            SELECT pt.post_id, t.id as tag_id, t.name as tag_name, t.category
            FROM post_tags pt
            JOIN tags t ON pt.tag_id = t.id
            WHERE pt.post_id IN ({post_id_placeholders})
        '''
        tag_results = conn.execute(query, post_ids).fetchall()
        
        # Group tags by post_id
        for tag_result in tag_results:
            if tag_result['post_id'] not in post_tags:
                post_tags[tag_result['post_id']] = []
            post_tags[tag_result['post_id']].append({
                'id': tag_result['tag_id'],
                'name': tag_result['tag_name'],
                'category': tag_result['category']
            })
    
    conn.close()
    
    return render_template('community_tag.html', 
                          tag=tag,
                          posts=posts,
                          all_tags=all_tags,
                          post_tags=post_tags)

@app.route('/login', methods=['POST'])
def login_post():
    """Process login form submission."""
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember-me') else False
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    # Check if user exists and password is correct
    if not user or not check_password_hash(user['password_hash'], password):
        flash('Please check your login details and try again.')
        return render_template('login.html', error="Invalid username or password")
    
    # Create user object
    from models import User
    user_obj = User(
        id=user['id'], 
        username=user['username'], 
        email=user['email'],
        password_hash=user['password_hash'],
        full_name=user['full_name'],
        farm_name=user['farm_name'],
        location=user['location'],
        farm_type=user['farm_type']
    )
    
    # Log in user
    login_user(user_obj, remember=remember)
    session['logged_in'] = True
    session['username'] = username
    session['user_id'] = user['id']
    
    return redirect(url_for('index'))

@app.route('/register')
def register():
    """Render the registration page."""
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    """Process registration form submission."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    farm_name = request.form.get('farm_name')
    location = request.form.get('location')
    farm_type = request.form.get('farm_type')
    
    # Check if username or email already exists
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    email_check = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        conn.close()
        flash('Username already exists.')
        return render_template('register.html', error="Username already exists.")
    
    if email_check:
        conn.close()
        flash('Email already exists.')
        return render_template('register.html', error="Email already exists.")
    
    # Create new user
    conn.execute(
        'INSERT INTO users (username, email, password_hash, full_name, farm_name, location, farm_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (username, email, generate_password_hash(password), full_name, farm_name, location, farm_type)
    )
    conn.commit()
    conn.close()
    
    flash('Successfully registered! Please log in.')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Log the user out."""
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/activity')
def activity():
    """Render the activity tracker page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Fetch activity types
    conn = get_db_connection()
    activity_types = conn.execute('SELECT * FROM activity_types ORDER BY name').fetchall()
    crop_types = conn.execute('SELECT * FROM crop_types ORDER BY name').fetchall()
    
    user_id = session.get('user_id')
    
    # Fetch recent and upcoming activities
    recent_activities = None
    upcoming_activities = None
    
    if user_id:
        # Recent activities (completed)
        recent_activities = conn.execute(
            '''SELECT * FROM activities 
               WHERE user_id = ? AND status = 'completed' 
               ORDER BY date DESC LIMIT 5''', 
            (user_id,)
        ).fetchall()
        
        # Upcoming activities (scheduled)
        upcoming_activities = conn.execute(
            '''SELECT * FROM activities 
               WHERE user_id = ? AND status = 'scheduled' AND date >= date('now') 
               ORDER BY date ASC LIMIT 5''', 
            (user_id,)
        ).fetchall()
    
    # Fetch inventory items
    inventory_items = conn.execute(
        'SELECT * FROM inventory WHERE user_id IS NULL OR user_id = ?', 
        (user_id or -1,)
    ).fetchall()
    
    conn.close()
    
    return render_template(
        'activity.html', 
        activity_types=activity_types,
        crop_types=crop_types,
        recent_activities=recent_activities,
        upcoming_activities=upcoming_activities,
        inventory_items=inventory_items
    )

@app.route('/activity/add', methods=['POST'])
def add_activity():
    """Add a new activity."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    activity_type = request.form.get('activity-type')
    activity_date = request.form.get('activity-date')
    field_location = request.form.get('activity-field')
    crop_type = request.form.get('activity-crop')
    description = request.form.get('activity-desc')
    is_recurring = request.form.get('is-recurring') == 'on'
    interval_days = request.form.get('interval-days', 0)
    priority = request.form.get('priority', 3)
    
    user_id = session.get('user_id')
    
    if not user_id or not activity_type or not activity_date or not description:
        flash('Please fill out all required fields.')
        return redirect(url_for('activity'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert the activity
    cursor.execute(
        '''INSERT INTO activities 
           (activity_type, description, date, field_location, crop_type, 
            is_recurring, interval_days, priority, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (activity_type, description, activity_date, field_location, crop_type, 
         1 if is_recurring else 0, interval_days, priority, user_id)
    )
    
    # Get the ID of the inserted activity
    activity_id = cursor.lastrowid
    
    # Handle inventory requirements
    inventory_items = request.form.getlist('inventory-item')
    quantities = request.form.getlist('inventory-quantity')
    
    for i in range(len(inventory_items)):
        if inventory_items[i] and quantities[i]:
            cursor.execute(
                'INSERT INTO activity_inventory (activity_id, inventory_id, quantity_required) VALUES (?, ?, ?)',
                (activity_id, inventory_items[i], quantities[i])
            )
    
    conn.commit()
    conn.close()
    
    flash('Activity added successfully.')
    return redirect(url_for('activity'))

@app.route('/activity/complete/<int:activity_id>', methods=['POST'])
def complete_activity(activity_id):
    """Mark an activity as completed."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    
    # Check if activity belongs to user
    activity = conn.execute(
        'SELECT * FROM activities WHERE id = ? AND user_id = ?', 
        (activity_id, user_id)
    ).fetchone()
    
    if not activity:
        conn.close()
        flash('Activity not found.')
        return redirect(url_for('activity'))
    
    # Update activity status
    conn.execute(
        'UPDATE activities SET status = ? WHERE id = ?',
        ('completed', activity_id)
    )
    
    # If it's a recurring activity, create the next occurrence
    if activity['is_recurring'] and activity['interval_days'] > 0:
        next_date = datetime.strptime(activity['date'], '%Y-%m-%d') + timedelta(days=activity['interval_days'])
        
        conn.execute(
            '''INSERT INTO activities 
               (activity_type, description, date, field_location, crop_type, 
                is_recurring, interval_days, priority, user_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (activity['activity_type'], activity['description'], next_date.strftime('%Y-%m-%d'), 
             activity['field_location'], activity['crop_type'], 1, activity['interval_days'], 
             activity['priority'], user_id, 'scheduled')
        )
    
    # Update inventory quantities based on activity requirements
    required_items = conn.execute(
        '''SELECT ai.inventory_id, ai.quantity_required 
           FROM activity_inventory ai
           WHERE ai.activity_id = ?''',
        (activity_id,)
    ).fetchall()
    
    for item in required_items:
        conn.execute(
            '''UPDATE inventory 
               SET quantity = quantity - ? 
               WHERE id = ? AND user_id = ?''',
            (item['quantity_required'], item['inventory_id'], user_id)
        )
    
    conn.commit()
    conn.close()
    
    flash('Activity marked as completed.')
    return redirect(url_for('activity'))

@app.route('/inventory')
def inventory():
    """Render the inventory management page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    inventory_items = conn.execute(
        'SELECT * FROM inventory WHERE user_id = ? ORDER BY name',
        (user_id,)
    ).fetchall()
    
    # Get low stock alerts
    low_stock_items = conn.execute(
        '''SELECT * FROM inventory 
           WHERE user_id = ? AND quantity <= min_quantity 
           ORDER BY name''',
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template(
        'inventory.html',
        inventory_items=inventory_items,
        low_stock_items=low_stock_items
    )

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    """Add a new inventory item."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    category = request.form.get('category')
    quantity = request.form.get('quantity')
    unit = request.form.get('unit')
    min_quantity = request.form.get('min_quantity', 0)
    
    user_id = session.get('user_id')
    
    if not name or not quantity:
        flash('Please provide a name and quantity.')
        return redirect(url_for('inventory'))
    
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO inventory (name, category, quantity, unit, min_quantity, user_id)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (name, category, quantity, unit, min_quantity, user_id)
    )
    conn.commit()
    conn.close()
    
    flash('Inventory item added successfully.')
    return redirect(url_for('inventory'))

@app.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    """Update an inventory item's quantity."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    quantity = request.form.get('quantity')
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    
    # Check if item belongs to user
    item = conn.execute(
        'SELECT * FROM inventory WHERE id = ? AND user_id = ?',
        (item_id, user_id)
    ).fetchone()
    
    if not item:
        conn.close()
        flash('Item not found.')
        return redirect(url_for('inventory'))
    
    conn.execute(
        'UPDATE inventory SET quantity = ? WHERE id = ?',
        (quantity, item_id)
    )
    conn.commit()
    conn.close()
    
    flash('Inventory updated successfully.')
    return redirect(url_for('inventory'))

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    """Render the weather page and handle weather data updates."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle weather data update from client
        data = request.get_json()
        user_id = session.get('user_id')
        
        if data and user_id:
            conn = get_db_connection()
            
            # Check if we already have weather for this date and location
            existing = conn.execute(
                '''SELECT id FROM weather_data 
                   WHERE location = ? AND date = ? AND user_id = ?''',
                (data['location'], data['date'], user_id)
            ).fetchone()
            
            if existing:
                # Update existing weather data
                conn.execute(
                    '''UPDATE weather_data 
                       SET temperature = ?, humidity = ?, precipitation = ?, 
                           wind_speed = ?, conditions = ? 
                       WHERE id = ?''',
                    (data['temperature'], data['humidity'], data['precipitation'], 
                     data['wind_speed'], data['conditions'], existing['id'])
                )
            else:
                # Insert new weather data
                conn.execute(
                    '''INSERT INTO weather_data 
                       (location, date, temperature, humidity, precipitation, 
                        wind_speed, conditions, user_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (data['location'], data['date'], data['temperature'], 
                     data['humidity'], data['precipitation'], data['wind_speed'], 
                     data['conditions'], user_id)
                )
            
            conn.commit()
            
            # Check for irrigation activities that could be affected by rain
            if data['conditions'].lower() in ['rain', 'rainy', 'showers', 'thunderstorm'] or data['precipitation'] > 0.5:
                from datetime import datetime, timedelta
                current_date = datetime.strptime(data['date'], '%Y-%m-%d')
                
                # Look for irrigation activities in the next 3 days
                start_date = current_date.strftime('%Y-%m-%d')
                end_date = (current_date + timedelta(days=3)).strftime('%Y-%m-%d')
                
                irrigation_activities = conn.execute(
                    '''SELECT * FROM activities 
                       WHERE user_id = ? AND activity_type LIKE '%irrigation%' 
                       AND status = 'scheduled' AND date BETWEEN ? AND ?''',
                    (user_id, start_date, end_date)
                ).fetchall()
                
                # Mark these activities as potentially not needed
                for activity in irrigation_activities:
                    conn.execute(
                        '''UPDATE activities 
                           SET status = 'rain-check' 
                           WHERE id = ?''',
                        (activity['id'],)
                    )
                
                conn.commit()
            
            conn.close()
            return {'success': True}
        
        return {'success': False, 'error': 'Invalid data or user not logged in'}
    
    # GET request - display weather page
    user_id = session.get('user_id')
    weather_data = None
    
    if user_id:
        conn = get_db_connection()
        
        # Get user's location
        user = conn.execute('SELECT location FROM users WHERE id = ?', (user_id,)).fetchone()
        user_location = user['location'] if user else None
        
        # Get today's weather if available
        today = datetime.now().strftime('%Y-%m-%d')
        weather_today = conn.execute(
            '''SELECT * FROM weather_data 
               WHERE user_id = ? AND date = ? 
               ORDER BY id DESC LIMIT 1''',
            (user_id, today)
        ).fetchone()
        
        # Get 7-day forecast
        forecast = conn.execute(
            '''SELECT * FROM weather_data 
               WHERE user_id = ? AND date >= ? 
               ORDER BY date ASC LIMIT 7''',
            (user_id, today)
        ).fetchall()
        
        conn.close()
        
        weather_data = {
            'location': user_location,
            'today': weather_today,
            'forecast': forecast
        }
    
    return render_template('weather.html', weather_data=weather_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
