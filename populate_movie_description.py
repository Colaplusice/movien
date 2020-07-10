import json
import os

import django
import pandas as pd
import requests
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recs.settings')
django.setup()

from Recommender.models import MovieDecriptions
from Analytics.models import Rating


def get_descriptions_with_movieid(movie_id):
    url = "https://api.themoviedb.org/3/find/tt{}?external_source=imdb_id&api_key={}"
    api_key = get_api_key()
    print('success')
    format_url = url.format(movie_id, api_key)
    r = requests.get(format_url)
    print(r.status_code)
    for film in r.json()['movie_results']:
        md = MovieDecriptions.objects.get_or_create(movie_id=movie_id)[0]
        md.imdb_id = movie_id
        if 'title' in film:
            md.title = film['title']
        if 'overview' in film:
            md.description = film['overview']
        if 'genre_ids' in film:
            md.genres = film['genre_ids']
        if len(md.description) > 0:
            md.save()
            # print("{}: {}".format(movie_id, r.json()))


def delete_db():
    print('truncate db')
    # MovieDecriptions.objects.all().delete()
    print('finished truncate db')


def get_api_key():
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']


#  加载评分数据
def load_all_ratings():
    # 提取相关列的数据
    columns = ['movie_id']
    ratings_data = Rating.objects.all().values(*columns)
    movie_ids = pd.DataFrame.from_records(ratings_data, columns=columns)
    movie_ids = movie_ids.drop_duplicates(subset=None, keep='first', inplace=False)
    movie_ids = movie_ids.reset_index()
    return movie_ids


if __name__ == '__main__':
    print("Starting MovieRecs Population script...")
    delete_db()
    movie_ids = load_all_ratings()
    movie_ids = movie_ids.iloc[:, 1]
    print(len(movie_ids.values))
    for movie_id in tqdm(movie_ids.values):
        print(movie_id)
        _, created = MovieDecriptions.objects.get_or_create(movie_id=movie_id)
        if not created:
            print('existed')
            continue
        get_descriptions_with_movieid(movie_id)
