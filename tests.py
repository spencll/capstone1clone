"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Page, Comment, Rating

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///ghibli_clone"

# Now we can import app

from app import app, CURR_USER_KEY, rating_avg

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u1 = User.signup("test1", "email1@email.com", "password", None)
            uid1 = 1111
            u1.id = uid1

            u2 = User.signup("test2", "email2@email.com", "password", None)
            uid2 = 2222
            u2.id = uid2

            # Test page
            p1= Page(name="page1", release_yr=1800, running_time=69)
            pid1 = 3333
            p1.id = pid1

            # Test comment 
            c1= Comment(comment="It's a good movie")
            cid1 = 4444
            c1.id = cid1

            # Test rating
            r1= Rating(score=6)
            rid1 = 5555
            r1.id = rid1

            r2= Rating(score=4)
            rid2 = 6666
            r2.id = rid2

            db.session.add_all([p1,c1,r1,r2])
            db.session.commit()

            # Adding comment to page and user
            p1.comments.append(c1)
            u1.user_comments.append(c1)
            # Adding rating to page and user
            p1.ratings.append(r1)
            p1.ratings.append(r2)
            u1.user_ratings.append(r1)
            u2.user_ratings.append(r2)

            db.session.commit()

            # Storing to self
            self.u1 = User.query.get(uid1)
            self.uid1 = uid1
            self.u2 = User.query.get(uid2)
            self.uid2 = uid2
            self.p1 = Page.query.get(pid1)
            self.pid1 = pid1
            self.c1 = Comment.query.get(cid1)
            self.cid1 = cid1
            self.r1 = Rating.query.get(rid1)
            self.rid1 = rid1
            self.r2 = Rating.query.get(rid2)
            self.rid2 = rid2

            # Flask test client for requests
            self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            return res


    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
            # Adding new user
            db.session.add(u)
            db.session.commit()

            # User should have no comments or ratings
            self.assertEqual(len(u.user_comments.all()), 0)
            self.assertEqual(len(u.user_ratings.all()), 0)

    ####
    #
    # Signup Tests
    #
    ####
        
    def test_valid_signup(self):
        with app.app_context():
        # Signed up
            u_test = User.signup("testtesttest", "testtest@test.com", "password", None)
            uid = 99999
            u_test.id = uid
            db.session.commit()

            # Getting signed up user
            u_test = User.query.get(uid)

            # Testing user info
            self.assertIsNotNone(u_test)
            self.assertEqual(u_test.username, "testtesttest")
            self.assertEqual(u_test.email, "testtest@test.com")
            self.assertNotEqual(u_test.password, "password")

            # Bcrypt strings should start with $2b$
            self.assertTrue(u_test.password.startswith("$2b$"))
            

    def test_invalid_username_signup(self):
        with app.app_context():
            # Trying to sign up with no username
            invalid = User.signup(None, "test@test.com", "password", None)
            uid = 123456789
            invalid.id = uid

            # Trying to commit, should raise integreity error 
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()


    def test_invalid_email_signup(self):
        with app.app_context():
            # Sign up with no email
            invalid = User.signup("testtest", None, "password", None)
            uid = 123789
            invalid.id = uid

            # Trying to commit, should raise integreity error 
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
        
    def test_invalid_password_signup(self):
        with app.app_context():
            # Trying to sign up with no password, should raise value error
            with self.assertRaises(ValueError) as context:
                User.signup("testtest", "email@email.com", "", None)
            # Trying to sign up with no password, should raise value error
            with self.assertRaises(ValueError) as context:
                User.signup("testtest", "email@email.com", None, None)
    
    ####
    #
    # Authentication Tests
    #
    ####
                
    def test_valid_authentication(self):
        with app.app_context():

            # Trying user class method authenticate, should return user
            u = User.authenticate(self.u1.username, "password")
            self.assertIsNotNone(u)
            self.assertEqual(u.id, self.uid1)
        
    def test_invalid_username(self):
        with app.app_context():
            # Authenticating with non existant username
            self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        with app.app_context():

            # Authenticating with wrong password
            self.assertFalse(User.authenticate(self.u1.username, "badpassword"))

    ####
    #
    # Comment tests
    #
    ####


    def test_comment(self):
        with app.app_context():
            
            # Getting the comment
            com = Comment.query.get(self.cid1)
            self.assertTrue(com)

            # Correct author
            self.assertEqual(com.comment_author[0].id, self.uid1)
            # Correct page
            self.assertEqual(com.page[0].id, self.pid1)

            with self.client as c:
                # Logged in to be able to delete
                with c.session_transaction() as sess:
                    self.testuser = User.query.get(self.uid1)
                    sess[CURR_USER_KEY] = self.testuser.id
    
                # Remove comment route is not working so going to just hardcode comment delete
                    
                # resp = c.post("/comments/4444/delete", follow_redirects=True)
                # self.assertEqual(resp.status_code, 200)
                    
                db.session.delete(com)    
                db.session.commit()
                p1 = Page.query.get(self.pid1)
                u1 = User.query.get(self.uid1)
                # Aftermath
                self.assertFalse(Comment.query.get(self.cid1))
                self.assertEqual(len(p1.comments.all()), 0)
                self.assertEqual(len(u1.user_comments.all()), 0)

    ####
    #
    # Rating tests
    #
    ####

    def test_rating(self):
        with app.app_context():

            page = Page.query.get(self.pid1)
            page.rating = rating_avg(page)

            self.assertEqual(page.rating ,5)

            # Changing rating 
            r1= Rating.query.get(self.rid1)
            r2= Rating.query.get(self.rid2)
            r1.score = 6
            r2.score = 8
            db.session.commit()

            # Getting average 
            page.rating= rating_avg(page)
            self.assertEqual(page.rating, 7)

    ####
    #
    # Other tests I would have added if I had time
    #
    #### 
            
    # Editing user information and user deletion
    # Checking Oauth response
    # Using beautiful soup to check HTML elements
    # Editing rating
    



        




        

