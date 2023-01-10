# app.py

from flask import Flask, request, jsonify
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy.exc import NoResultFound, IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

api = Api(app)

# создаем неймспэйсы
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')

class Movie(db.Model):
    """Модель для фильма"""
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")

class Director(db.Model):
    """Модель для режиссера"""
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    """Модель для жанра"""
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

class MovieScheme(Schema):
    """Схема для сериализации фильма"""
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


movie_scheme = MovieScheme()
movies_scheme = MovieScheme(many=True)

class DirectorScheme(Schema):
    """Схема для сериализации режиссера"""
    id = fields.Int(dump_only=True)
    name = fields.Str()


director_scheme = DirectorScheme()
directors_scheme = DirectorScheme(many=True)


class GenreScheme(Schema):
    """Схема для сериализации жанра"""
    id = fields.Int(dump_only=True)
    name = fields.Str()


genre_scheme = GenreScheme()
genres_scheme = GenreScheme(many=True)

# Представление для выдачи всех фильмов,
# фильмов по режиссеру и жанру, фильмов по режиссеру, фильмов по жанру
# и для добавления фильма
@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        director_id = request.args.get('director_id')
        genre_id = request.args.get('genre_id')

        if director_id and genre_id:
            movies = Movie.query.filter(Movie.director_id == director_id, Movie.genre_id == genre_id).all()
            if len(movies) == 0:
                return "Movies not found"
            return jsonify(movies_scheme.dump(movies))
        elif director_id:
            movies = Movie.query.filter(Movie.director_id == director_id).all()
            if len(movies) == 0:
                return "Movies not found"
            return jsonify(movies_scheme.dump(movies))
        elif genre_id:
            movies = Movie.query.filter(Movie.genre_id == genre_id).all()
            if len(movies) == 0:
                return "Movies not found"
            return jsonify(movies_scheme.dump(movies))
        else:
            movies = Movie.query.all()
            return jsonify(movies_scheme.dump(movies))


    def post(self):
        data = request.json
        try:
            add_movie = Movie(
                id=data.get('id'),
                title=data.get('title'),
                description=data.get('description'),
                trailer=data.get('trailer'),
                year=data.get('year'),
                rating=data.get('rating'),
                genre_id=data.get('genre_id'),
                director_id=data.get('director_id'))
            db.session.add(add_movie)
            db.session.commit()
            return 'Movie was added'

        except IntegrityError:
            return 'Movie with this id has already existed'

# Представление фильма по id, обновление информации о фильме, удаление фильма
@movie_ns.route('/<int:id>/')
class MovieView(Resource):
    def get(self, id: int):
        try:
            movie = db.session.query(Movie).filter(Movie.id == id).one()
            return jsonify(movie_scheme.dump(movie))

        except NoResultFound:
            return "Movie is not found"

    def put(self, id: int):
        data = request.json
        try:
            movie = db.session.query(Movie).filter(Movie.id == id).one()
            if data.get('title'):
                movie.title = data.get('title')
            if data.get('description'):
                movie.description = data.get('description')
            if data.get('trailer'):
                movie.trailer = data.get('trailer')
            if data.get('year'):
                movie.year = data.get('year')
            if data.get('rating'):
                movie.rating = data.get('rating')
            if data.get('genre_id'):
                movie.genre_id = data.get('genre_id')
            if data.get('director_id'):
                movie.director_id = data.get('director_id')

            db.session.add(movie)
            db.session.commit()

            return "Movie was updated"

        except NoResultFound:
            return "Movie is not found"

    def delete(self, id: int):
        try:
            movie = db.session.query(Movie).filter(Movie.id == id).one()
            db.session.delete(movie)
            db.session.commit()

            return "Movie was deleted"

        except NoResultFound:
            return "Movie is not found"


# Все режиссеры и добавление режиссера
@director_ns.route('/')
class DirectorsView(Resource):
    def get(self):
        directors = Director.query.all()
        return jsonify(directors_scheme.dump(directors))

    def post(self):
        data = request.json
        try:
            add_director = Director(
                id=data.get('id'),
                name=data.get('name')
            )
            db.session.add(add_director)
            db.session.commit()
            return "Director was added"

        except IntegrityError:
            return "Director with this id has already exist"


# Представление режиссера по id, обновление информации о режиссере, удаление режиссера
@director_ns.route('/<int:id>/')
class DirectorView(Resource):
    def get(self, id: int):
        director = Director.query.get(id)
        if director is None:
            return "Director is not found"
        return jsonify(director_scheme.dump(director))

    def put(self, id: int):
        data = request.json
        try:
            director = db.session.query(Director).filter(Director.id == id).one()
            director.name = data.get('name')
            db.session.add(director)
            db.session.commit()
            return "Director was updated"
        except NoResultFound:
            return "Director is not found"

    def delete(self, id: int):
        try:
            director = db.session.query(Director).filter(Director.id == id).one()
            db.session.delete(director)
            db.session.commit()
            return "Director was deleted"
        except NoResultFound:
            return "Director is not found"


# Представления с выдачей всех жанров и добавлением жанра
@genre_ns.route('/')
class GenresView(Resource):
    def get(self):
        genres = Genre.query.all()
        return jsonify(genres_scheme.dump(genres))

    def post(self):
        data = request.json
        try:
            add_genre = Genre(
                id=data.get('id'),
                name=data.get('name')
                )
            db.session.add(add_genre)
            db.session.commit()
            return "Genre was added"

        except IntegrityError:
            return "Genre with this id has already exist"


# Представление жанра по id, обновление информации о жанре, удаление жанра
@genre_ns.route('/<int:id>/')
class GenreView(Resource):
    def get(self, id: int):
        # сформируем запрос для получения списка фильмов по жанру с заданным id
        query = db.session.query(Genre.id, Genre.name, Movie.title).join(Movie, isouter=True).filter(Genre.id == id)
        raw_data = query.all()
        if len(raw_data) == 0:
            return "Genre is not found"
        movies = []
        # Соберем фильмы в список
        for one_movie in raw_data:
           movies.append(one_movie[2])

        # сформируем словарь для отдачи - с информацией о жанре и списком фильмов
        result = {
            "id": raw_data[0][0],
            "name": raw_data[0][1],
            "movies": movies
            }
        return jsonify(result)

    def put(self, id: int):
        data = request.json
        try:
            genre = db.session.query(Genre).filter(Genre.id == id).one()
            genre.name = data.get('name')
            db.session.add(genre)
            db.session.commit()
            return "Genre was updated"
        except NoResultFound:
            return "Genre is not found"

    def delete(self, id: int):
        try:
            genre = db.session.query(Genre).filter(Genre.id == id).one()
            db.session.delete(genre)
            db.session.commit()
            return "Genre was deleted"
        except NoResultFound:
            return "Genre is not found"


if __name__ == '__main__':
    app.run(debug=True)
