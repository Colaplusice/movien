from django.db import models


# Create your models here.
class Genre(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Movie(models.Model):
    movie_id = models.CharField(max_length=16, unique=True, primary_key=True)
    title = models.CharField(max_length=1024)
    year = models.IntegerField(null=True)
    genres = models.ManyToManyField(Genre, related_name='movies', db_table='movie_genres')

    def __str__(self):
        return self.title
