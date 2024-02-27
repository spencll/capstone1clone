import os
import requests
import json
from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from authlib.integrations.flask_client import OAuth
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from googleapiclient.discovery import build

from forms import LoginForm, RegisterForm, CommentForm, RatingForm, EditUserForm
from models import db, connect_db, Comment, Rating, User, Page


# session key to store logged in user
CURR_USER_KEY = "curr_user"
app = Flask(__name__)

# Integrating authlib with flask
oauth=OAuth(app)
google = oauth.register(
    name='google',
    client_id='749818778496-8jmtc3kvr8rci8vv2vlgh2nhh7f2t713.apps.googleusercontent.com',
    client_secret='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',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={'scope': 'email', 'access_type': 'offline'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    refresh_token_url=None,
    refresh_token_params={'grant_type': 'refresh_token'},
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
    client_kwargs={'scope': 'openid profile email'}
)


# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///ghibli'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)

with app.app_context():
    db.create_all()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

# Functions
def do_login(user):
    """Log in user and sets session key as user id"""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    #If logged in with gmail, remove google token as well
    google_token = session.get('google_token')
    if google_token:
        del session['google_token']

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        return

def rating_avg(page):
    """Calculates average rating for a page"""

    ratings = page.ratings.all()
    rating_lst= [rate.score for rate in ratings]
    avg = round(sum(rating_lst)/len(rating_lst),2)
    return avg

# Cache to store youtube API urls. Youtube API has stupid low daily request quota
url_cache = {}

def get_video_url(query, pid):
    """Getting trailer video via Youtube API"""

    API_KEY = 'AIzaSyDSRLx0r_Dh85E8eGglh-5y0J-YUnsijks'
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Make a request to search for videos
    search_response = youtube.search().list(
        q=query + 'trailer',
        part='snippet',
        type='video',
        maxResults=1 
    ).execute()

    # Extract the video ID from the search results
    video_id = search_response['items'][0]['id']['videoId']

    # Construct the embedable video URL
    embed_url = f'https://www.youtube.com/embed/{video_id}'

    # Store to cache using pid as key to avoid requesting same url 
    url_cache[pid]= embed_url

    # Output the video URL
    return embed_url


@app.route('/google')
def google_signin():
    """Redirect to google login"""

    return google.authorize_redirect(
        redirect_uri=url_for('authorize', _external=True))

@app.route('/authorize')
def authorize():

    # Token generation
    token = google.authorize_access_token()
    session['google_token'] = token
    
    # OAuth response jsonified
    resp = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
    profile= resp.json()

    # Generating new user based on google login info if user not there
    user= User.query.filter_by(username=profile['email']).first()
    if not user:
        user = User.signup(
                    username=profile['email'],
                    # using the id as password placeholder, not sure if this is bad lol
                    password=profile['id'], 
                    email=profile['email'],
                    image_url= User.image_url.default.arg,
                )
        db.session.commit()

    # Setting session key value to demonstrate logged in user
    session[CURR_USER_KEY] = user.id

    return redirect('/')

@app.route('/')
def home():

    # Populating from Ghibli API if not done yet
    if not Page.query.all():
        res = requests.get('https://ghibliapi.vercel.app/films').json()
        for movie in res:
            page = Page(name=movie['title'],
                        running_time=movie['running_time'],
                        release_yr=movie['release_date'],
                        url=movie['url'])
            db.session.add(page)
            db.session.commit()

    #Getting all movie names and convert to json to access in JS
    every = Page.query.all()
    names = json.dumps([page.name for page in every])

    # Sorting rated movies by rating and getting top 6 
    all = Page.query.filter(Page.rating.isnot(None)).order_by(Page.rating.desc()).limit(6).all()

    # Getting the movie image for the top rated movies stored in .img
    for movie in all:
        url = movie.url
        res = requests.get(url).json()
        movie.img = res['image']

    # Getting the most recent comments 
    comments = Comment.query.order_by(Comment.timestamp.desc()).limit(3).all()

    return render_template('home.html', all=all, comments=comments, names=names)

# Search route
@app.route('/search')
def search():
    """Process search query in search bar"""

    # Stores query string
    query = request.args.get('q')

    # Getting filtered pages with query string
    pages = Page.query.filter((Page.name.ilike(f'%{query}%'))).all()

    # Getting movie image again, too lazy to make function 
    for page in pages:
        url = page.url
        res = requests.get(url).json()
        page.img = res['image']

    return render_template('results.html', query=query, pages=pages)


# WTForm related pathways
@app.route('/users/register', methods = ['GET','POST'])
def register():
    """Register user"""

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()
        
        # Isolating error to particular form error 
        except IntegrityError as e:
            db.session.rollback() 
            if "Key (username)" in str(e):
                flash("Username already taken, please choose a different one.", 'danger')
            elif "Key (email)" in str(e):
                flash("Email already taken, please use a different one.", 'danger')
            else:
            # Other errors
                flash("An error occurred, please try again.", 'danger')

            return render_template('users/signup.html', form=form)
        

        # Setting session key value to demonstrate logged in user
        session[CURR_USER_KEY] = user.id
        return redirect("/")

    # GET
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    """Login user"""
    form = LoginForm()

    if form.validate_on_submit():

        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(url_for('show_user_profile', uid=user.id))

        flash("Invalid credentials.", 'danger')

    # GET
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("Successfully logged out", 'success')
    return redirect("/")


@app.route('/users/edit',methods=['GET','POST'])
def edit_user():
    """Edit user information"""
    if not g.user:
        flash("Not authorized user", "danger")
        return redirect("/")
    
    form = EditUserForm()

    # If form left empty, defaults to original 
    if form.validate_on_submit():
        g.user.username = form.username.data or g.user.username
        g.user.email = form.email.data or g.user.email
        g.user.image_url = form.image_url.data or "/static/images/default-pic.png"
        g.user.password = form.password.data or g.user.password
        g.user.bio = form.bio.data or g.user.bio 
        db.session.commit()
        return redirect(url_for('show_user_profile', uid= g.user.id))

    # GET
    return render_template('edit_user.html', form=form)

@app.route('/pages/<pid>/comment', methods=['GET','POST'])
def add_comment(pid):
    """Add comment to page"""
    if not g.user:
        flash("Must be logged in to comment", "danger")
        return redirect(f"/pages/{pid}")

    page = Page.query.get_or_404(pid)
    form = CommentForm()

    if form.validate_on_submit():

        # New comment
        comment = Comment(comment=form.comment.data)
        db.session.add(comment)
        db.session.commit()

        # Adding comment to page and user 
        page.comments.append(comment)
        g.user.user_comments.append(comment)
        db.session.commit()

        return redirect(url_for('show_page',pid=pid))
    
    # GET
    return render_template('comment.html', form=form, pid=pid)
    
@app.route('/comments/<cid>/delete', methods = ['POST'])
def delete_comment(cid):
    """Delete comment"""
    comment = Comment.query.get_or_404(cid)
    db.session.delete(comment)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/users/<uid>/delete', methods= ['POST'])
def delete_user(uid):
    """Logs out user and then deletes user"""
    do_logout()
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return redirect("/")

@app.route('/pages/<pid>/rate', methods=['GET','POST'])
def add_rating(pid):
    """Add rating to page"""
    if not g.user:
        flash("Must be logged in to rate", "danger")
        return redirect(f"/pages/{pid}")
    
    page = Page.query.get_or_404(pid)
    form = RatingForm()

    if form.validate_on_submit():

        # Rating already made, way to edit without making edit route
        rating_authors = [rating.rating_author for rating in page.ratings]

        if [g.user] in rating_authors:
            rating = Rating.query.filter(and_(Rating.rating_author.any(id=g.user.id), Rating.page.any(id=pid))).first()
            rating.score = form.score.data
            db.session.add(rating)
            db.session.commit()
            flash("Changed your rating", "danger")

        # Regular POST method
        else:
            
            # Add new rating
            rating = Rating(score=form.score.data)
            db.session.add(rating)
            db.session.commit()

            # Adding rating to page and user 
            page.ratings.append(rating)
            g.user.user_ratings.append(rating)
            db.session.commit()

        # Commiting new average to page rating
        page.rating = rating_avg(page)
        db.session.commit()
        return redirect(url_for('show_page',pid=pid))
    
    # GET, shows form with prior rating for reference
    rating = Rating.query.filter(and_(Rating.rating_author.any(id=g.user.id), Rating.page.any(id=pid))).first()
    return render_template('rating.html',form=form, rating=rating)
        
# Shows
@app.route('/users/<uid>')
def show_user_profile(uid):
    """Show user profile"""

    user = User.query.get(uid)
    comments = user.user_comments.all() 
    ratings = user.user_ratings.all()

    comments = Comment.query.filter(Comment.comment_author.contains(user)).order_by(Comment.timestamp.desc()).limit(3).all()

    # Getting top ratings from user
    top_ratings = Rating.query.filter(Rating.score.isnot(None), Rating.rating_author.contains(user)).order_by(Rating.score.desc()).limit(6).all()

    # Getting images of top rated movies of user and storing to .img
    for movie in top_ratings:
        url = movie.page[0].url
        res = requests.get(url).json()
        movie.img = res['image']

    return render_template('detail.html', user=user,comments=comments, top_ratings=top_ratings, ratings=ratings)

@app.route('/pages/<pid>')
def show_page(pid):
    """Generates new Page and shows info page"""
    page = Page.query.get(pid)

    # Getting banner image
    url = page.url
    res = requests.get(url).json()
    img = res['movie_banner']

    # Getting comments 
    comments = Comment.query.filter(Comment.page.contains(page)).order_by(Comment.timestamp.desc()).all()

    # Get trailer url from url cache if already exists to avoid google quota
    if pid in url_cache:
        video_url=url_cache[pid]
    else:
        video_url = get_video_url(page.name, pid)

    return render_template('page.html',page=page, comments=comments, img=img, video_url=video_url, res=res)



