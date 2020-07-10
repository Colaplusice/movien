import datetime
import decimal
import os
import urllib.request

import django
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recs.settings')
django.setup()

from Analytics.models import Rating


# 插入评分记录
def create_rating(user_id, content_id, rating, timestamp):
    rating = Rating(user_id=user_id, movie_id=content_id, rating=decimal.Decimal(rating),
                    rating_timestamp=datetime.datetime.fromtimestamp(float(timestamp)))
    rating.save()
    return rating


def download_ratings():
    URL = 'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/ratings.dat'
    response = urllib.request.urlopen(URL)
    data = response.read()
    print('download finished')
    return data.decode('utf-8')


# 删除已有的评分数据
def delete_db():
    print('truncate db')
    Rating.objects.all().delete()
    print('finished truncate db')


def populate():
    delete_db()
    # ratings = download_ratings()
    ratings = open('ratings.dat', 'r').read()
    for rating in tqdm(ratings.split(sep="\n")[:1000]):
        r = rating.split(sep="::")
        if len(r) == 4:
            create_rating(r[0], r[1], r[2], r[3])


if __name__ == '__main__':
    print("Starting MovieRecs Population script...")
    populate()
