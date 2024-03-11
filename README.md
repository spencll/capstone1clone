# Studio Ghibli Fansite

## Introduction

Live render: https://studio-ghibli-fansite.onrender.com/
Welcome to the Studio Ghibli fansite where you can search movies from the studio to get more information and even watch a movie trailer! Upon logging in, you can leave a rating on movies as well as comment.

* The home page displays the top rated movies as well as the latest comments. 
* Your personal page shows your own top rated movies and your latest comments. 
* The movie page shows general movie information along with some images and a movie trailer.
* Use the search bar to find a movie. You can leave it empty if you want to see all the movies. 


## Features

Google OAuth 2.0 server to allow for a streamlined sign up process if you're already logged in to your gmail account.

Search bar with auto drop down list based on search query. Allows for searching even by single letter in case user is not familiar with Studio Ghibli movies. 

Movie page pulls images and information from Studio Ghibli API while Youtube API pulls a trailer for the selected movie. After Youtube API request, the video URL is stored in a cache to avoid having to make the same request. 


## Technology stack

* Python/Flask, PostgreSQL, SQLAlchemy, Jinja, RESTful APIs, JavaScript, HTML, CSS, WTForms
* Authlib for authentication 
* OAuth 2.0 for logging in/signing up with gmail
* Bootstrap to organize HTML
* Ghibli API to get movie information: https://ghibliapi.vercel.app/
* Youtube API to get movie trailers
* ElephantSQL and Render for deploying 

## Schema

### Tables: User, Page, Rating, Comment

All linked using one big association table with foreign keys to each respective table. 

### Relationship name in parenthesis including backrefs  

* Comment (comment_author) <-> association table <-> User (user_comments)
* Rating (rating_author)<-> association table <-> User (user_ratings)
* Comment (page) <-> association table <-> Page (comments)
* Rating (page) <-> association table <-> Page (ratings) 

## CRUD

What's CRUDable?

* User (CRUD)
* Comments (CRD)
* Rating (CRU)
* Page (R)
