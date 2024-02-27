from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()

association_table = db.Table('association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('comment_id', db.Integer, db.ForeignKey('comments.id')),
    db.Column('rating_id', db.Integer, db.ForeignKey('ratings.id')),
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id'))
)

class Comment(db.Model):
    """Individual comments"""

    __tablename__ = 'comments'

    id = db.Column(db.Integer,primary_key=True)
    comment = db.Column(db.Text,nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def formatted_timestamp(self):
        return self.timestamp.strftime("%m/%d/%Y, %I:%M %p")


class Rating(db.Model):
    """Individual ratings"""

    __tablename__ = 'ratings'

    id = db.Column(db.Integer,primary_key=True)
    score = db.Column(db.Float)

# Generating info page 
class Page(db.Model):
    """Info page for each topic"""

    __tablename__ = 'pages' 

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text, nullable=False)
    release_yr = db.Column(db.Integer)
    running_time = db.Column(db.Integer)
    rating = db.Column(db.Float)
    url = db.Column(db.Text)


    # Setting relationships to access
    comments= db.relationship('Comment', secondary=association_table, backref='page', lazy='dynamic')

    ratings= db.relationship('Rating', secondary=association_table, backref='page', lazy='dynamic')


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.Text,nullable=False,unique=True)
    password = db.Column(db.Text,nullable=False)
    email = db.Column(db.Text,nullable=False,unique=True)
    bio = db.Column(db.Text, default='')
    image_url = db.Column(db.Text, default="/static/images/default-pic.png")

    # Setting relationships to user comments and ratings 
    user_comments= db.relationship('Comment', secondary=association_table, backref='comment_author', lazy='dynamic')

    user_ratings= db.relationship('Rating', secondary=association_table, backref='rating_author', lazy='dynamic')

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)



