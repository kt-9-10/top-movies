from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests, os


SEARCH_ALL_BEARER = os.environ['SEARCH_ALL_BEARER']
SEARCH_BEARER = os.environ['SEARCH_BEARER']


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True)
    year: Mapped[str] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String)
    rating: Mapped[str] = mapped_column(Float, nullable=True)
    ranking: Mapped[str] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String)


class UpdateForm(FlaskForm):
    rating = StringField(label='Your Rating Out of 10 e.g. 7.5', name="new_rating", validators=[DataRequired()])
    review = StringField(label='Your Review', name="new_review", validators=[DataRequired()])
    submit = SubmitField(label='Done')


class AddForm(FlaskForm):
    title = StringField(label='Movie Title', name="new_title", validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()
    all_movies = list(result)
    for i in range(0, len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit/<movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    if request.method == 'POST':
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
            movie_to_update.rating = float(request.form["new_rating"])
            movie_to_update.review = request.form["new_review"]
            db.session.commit()
        return redirect('/')

    form = UpdateForm()
    return render_template("edit.html", form=form)


@app.route('/delete/<movie_id>', methods=['GET', 'POST'])
def delete(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    print(Movie)
    return redirect('/')


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        url = "https://api.themoviedb.org/3/search/movie?query="
        headers = {
            "accept": "application/json",
            "Authorization": SEARCH_ALL_BEARER
        }
        response = requests.get(f"{url}{request.form["new_title"]}", headers=headers)
        searched_movies = response.json()['results']
        print(searched_movies)
        return render_template("select.html", movies=searched_movies)

    form = AddForm()
    return render_template("add.html", form=form)


@app.route("/add_db/<movie_id>", methods=['GET', 'POST'])
def add_db(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}]"
    headers = {
        "accept": "application/json",
        "Authorization": SEARCH_BEARER
    }
    response = requests.get(url, headers=headers)
    movie_data = response.json()
    add_movie = Movie(
        title=movie_data['original_title'],
        year=movie_data['release_date'][:4],
        description=movie_data['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
    )
    with app.app_context():
        db.session.add(add_movie)
        db.session.commit()

    added_movie = db.session.execute(db.select(Movie).where(Movie.title == movie_data['original_title'])).scalar()

    return redirect(f'/edit/{added_movie.id}')


if __name__ == '__main__':
    app.run(debug=True)
