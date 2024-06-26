# app/routes.py

from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User, Post, Comment, Category, Forum
from app.forms import RegistrationForm, LoginForm, PostForm, CommentForm, UpdateAccountForm
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Ihr Account wurde erstellt! Sie können sich jetzt einloggen.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrieren', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('forum'))  # Weiterleitung zur Forum-Seite, wenn bereits eingeloggt
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('forum'))  # Weiterleitung zur Forum-Seite nach dem Login
        else:
            flash('Login fehlgeschlagen. Bitte überprüfen Sie Ihre E-Mail und Ihr Passwort', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))  # Oder wohin auch immer Sie den Benutzer nach dem Logout umleiten möchten



@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Ihr Konto wurde aktualisiert!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', title='Konto', form=form)


@app.route('/post/new/<int:category_id>', methods=['GET', 'POST'])
@login_required
def new_post(category_id):
    category = Category.query.get_or_404(category_id)
    form = PostForm()
    if form.validate_on_submit():
        # Verarbeiten Sie den Inhalt, der vom CKEditor kommt
        content = request.form['content']
        post = Post(UserID=current_user.UserID, CategoryID=category.CategoryID, Title=form.title.data, Content=content)
        db.session.add(post)
        db.session.commit()
        flash('Der Post wurde erfolgreich erstellt!', 'success')
        return redirect(url_for('category', category_id=category.CategoryID))
    return render_template('create_post.html', category=category, form=form)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', title=post.Title, post=post)


@app.route('/forum')
@login_required
def forum():
    forums = Forum.query.all()  # Alle Foren aus der Datenbank abrufen
    return render_template('forum.html', forums=forums)

@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    posts = category.posts  # Alle Posts der Kategorie abrufen
    return render_template('category.html', category=category, posts=posts)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Keine Datei Teil der Anfrage')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Keine ausgewählte Datei')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'Datei erfolgreich hochgeladen'