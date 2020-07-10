# Generated by Django 2.2.10 on 2020-07-07 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LdaSimilarity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField()),
                ('source', models.CharField(db_index=True, max_length=16)),
                ('target', models.CharField(max_length=16)),
                ('similarity', models.DecimalField(decimal_places=7, max_digits=8)),
            ],
            options={
                'db_table': 'lda_similarity',
            },
        ),
        migrations.CreateModel(
            name='MF',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField()),
                ('user_id', models.CharField(db_index=True, max_length=16)),
                ('movie_id', models.CharField(max_length=16)),
                ('similarity', models.DecimalField(decimal_places=7, max_digits=8)),
            ],
            options={
                'db_table': 'similarity_mf',
            },
        ),
        migrations.CreateModel(
            name='MovieDecriptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movie_id', models.CharField(max_length=16)),
                ('imdb_id', models.CharField(max_length=16)),
                ('title', models.CharField(max_length=512)),
                ('description', models.CharField(max_length=1024)),
                ('genres', models.CharField(default='', max_length=512)),
                ('lda_vector', models.CharField(max_length=56, null=True)),
                ('sim_list', models.CharField(default='', max_length=512)),
            ],
            options={
                'db_table': 'movie_description',
            },
        ),
        migrations.CreateModel(
            name='SeededRecs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('source', models.CharField(max_length=16)),
                ('target', models.CharField(max_length=16)),
                ('support', models.DecimalField(decimal_places=8, max_digits=10)),
                ('confidence', models.DecimalField(decimal_places=8, max_digits=10)),
                ('type', models.CharField(max_length=8)),
            ],
            options={
                'db_table': 'seeded_recs',
            },
        ),
        migrations.CreateModel(
            name='Similarity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField()),
                ('source', models.CharField(db_index=True, max_length=16)),
                ('target', models.CharField(max_length=16)),
                ('similarity', models.DecimalField(decimal_places=7, max_digits=8)),
            ],
            options={
                'db_table': 'similarity',
            },
        ),
    ]
