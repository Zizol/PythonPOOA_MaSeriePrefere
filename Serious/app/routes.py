from flask import render_template, flash, redirect, url_for, request
import requests
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse


@app.route('/')
@app.route('/home/')
def home():
    url = "https://api.betaseries.com/shows/random"
    querystring = {"key":"7c2f686dfaad","v":"3.0","nb":"3"}
    posts = requests.request("GET", url, params=querystring).json()["shows"]
    for post in posts:
        if len(post["description"]) > 500:
            post["description"] = post["description"][:500] + "..."
    return render_template('home.html', posts=posts, bonjour="eh non")

@app.route('/series/', methods=['GET', 'POST'])
def series():
    if request.method == 'GET':
        url = "https://api.betaseries.com/shows/list"
        starting = request.args.get('starting', default=' ', type=str)
        page = request.args.get('page', default=1, type=int)
        querystring = {"key": "7c2f686dfaad", "v": "3.0", "order": "alphabetical", "limit": "9", "starting": starting,
                       "start": (page-1)*9, "fields": "id,title,images.show"}
        posts = requests.request("GET", url, params=querystring).json()["shows"]
        for post in posts:
            if len(post.keys()) == 2:
                post['images'] = {'show': url_for('static', filename='img/logo.png')}
        return render_template('series.html', posts=posts, starting=starting, page=page)

    elif request.method == 'POST':
        url = "https://api.betaseries.com/search/all"
        search = request.form['search']
        querystring = {"key": "7c2f686dfaad", "v": "3.0", "query": search}
        posts = requests.request("GET", url, params=querystring).json()["shows"]
        for post in posts:
            post['images'] = {'show': url_for('static', filename='img/logo.png')}
        return render_template('series.html', posts=posts, starting=None, page=None)


@app.route('/serie/<int:serie_id>/')
def serie(serie_id):
    urls = ["https://api.betaseries.com/shows/episodes", "https://api.betaseries.com/shows/seasons", "https://api.betaseries.com/shows/display"]
    items = ["episodes", "seasons", "show"]
    requete_serie = Requete(serie_id, items, urls)
    response = requete_serie.run()
    return render_template('serie.html', episodes=response["episodes"], saisons=response["seasons"], display=response["show"])

@app.route('/my_list/<starting>/<int:page>/')
@login_required
def my_list(starting, page):
    url = "https://api.betaseries.com/shows/list"
    querystring = {"key": "7c2f686dfaad", "v": "3.0", "order": "alphabetical", "limit": "9", "starting": starting,
                   "start": (page-1)*9, "fields": "id,title,images.show"}
    posts = requests.request("GET", url, params=querystring).json()["shows"]
    for post in posts:
        if len(post.keys()) == 2:
            post['images'] = {'show': url_for('static', filename='img/logo.png')}
    return render_template('series.html', posts=posts, starting=starting, page=page)

from threading import Thread, RLock
from queue import Queue


class Requete():

    def __init__(self, serie_id, items, urls):
        self.querystring = {"key": "7c2f686dfaad", "v": "3.0", "id": serie_id}
        self.urls = urls
        self.items = items
        self.response = {}
        self.queue = Queue()
        self.verrou = RLock()
        for item in items:
            self.response[item] = ""

    def run(self):
        self.queue.put(self.response)
        threads = [Thread(target=self.requete, args=(self.querystring, item, self.verrou, self.queue, url)) for (item, url) in zip(self.items, self.urls)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return self.queue.get()

    @staticmethod
    def requete(querystring, item, verrou, queue, url):
        display = requests.request("GET", url, params=querystring).json()[item]
        with verrou:
            a = queue.get()
            a[item] = display
            queue.put(a)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)