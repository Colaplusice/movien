import os
import urllib.request

from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recs.settings')

import django

django.setup()

from Movies.models import Movie, Genre


# 创建每一条电影数据并保存
def create_movie(movie_id, title, genres):
    movie = Movie.objects.get_or_create(movie_id=movie_id)[0]
    title_and_year = title.split(sep="(")
    movie.title = title_and_year[0]
    movie.year = title_and_year[1][:-1]

    if genres:
        for genre in genres.split(sep="|"):
            g = Genre.objects.get_or_create(name=genre)[0]
            movie.genres.add(g)
            g.save()
    movie.save()
    return movie


def download_movies(URL='https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/movies.dat'):
    response = urllib.request.urlopen(URL)
    data = response.read()
    return data.decode('utf-8')


# 如果之前存在数据库数据则先删除
def delete_db():
    print('truncate db')
    movie_count = Movie.objects.all().count()
    if movie_count > 1:
        Movie.objects.all().delete()
        Genre.objects.all().delete()
    print('finished truncate db')


def populate():
    movies = download_movies()
    if len(movies) == 0:
        print('The latest dataset seems to be empty. Older movie list downloaded.')
        print('Please have a look at https://github.com/sidooms/MovieTweetings/issues and see if there is an issue')
        movies = download_movies(
            'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/snapshots/100K/movies.dat')
    print('movie data downloaded')
    for movie in tqdm(movies.split(sep='\n')):
        m = movie.split(sep="::")
        if len(m) == 3:
            create_movie(m[0], m[1], m[2])


# 执行此文件前需要先在控制台安装/Applications/Python\ 3.7/Install\ Certificates.command证书
if __name__ == '__main__':
    print("Starting MovieGeeks Population script...")
    delete_db()
    populate()
