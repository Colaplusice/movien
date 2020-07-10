import os
from tqdm import tqdm
import psycopg2
from datetime import datetime
from scipy.sparse import coo_matrix

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Recs.settings")

import django
from Recs import settings

django.setup()


from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from gensim import corpora, models, similarities

from  Recommender.models import MovieDecriptions, LdaSimilarity

class LdaModel(object):
    def __init__(self, min_sim=0):
        self.min_sim = min_sim;
        self.db = settings.DATABASES['default']['ENGINE']


    def train(self, data=None, docs=None):
        if data is None:
            data, docs = load_data()
        NUM_TOPICS = 10
        self.build_lda_model(data, docs, NUM_TOPICS)

    def build_lda_model(self, data, docs, n_topics = 5):
        texts = []
        # 英文分词
        tokenizer = RegexpTokenizer(r'\w+')
        for d in tqdm(data):
            raw = d.lower()
            tokens = tokenizer.tokenize(raw)
            # 去除停用词
            stop_tokens = self.remove_stopwords(tokens)
            stemmed_tokens = stop_tokens
            texts.append(stemmed_tokens)

        # 构建词典
        dictionary = corpora.Dictionary(texts)
        # 生成语料库
        corpus = [dictionary.doc2bow(text) for text in texts]


        lda_model = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=n_topics)


        index = similarities.MatrixSimilarity(corpus)

        self.save_similarities_with_postgresql(index, docs)

        return dictionary, texts, lda_model


    @staticmethod
    def remove_stopwords(tokenized_data):
        # 去除停用词
        en_stop = get_stop_words('en')
        stop_tokens = [token for token in tokenized_data if token not in en_stop]
        return stop_tokens

    def save_similarities_with_postgresql(self, index, docs, created=datetime.now()):
        start_time = datetime.now()
        print(f'truncating table in {datetime.now() - start_time} seconds')
        sims = []
        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(index)
        csr = coo.tocsr()
        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')

        query = "insert into lda_similarity (created, source, target, similarity) values %s;"
        conn = self.get_conn()
        cur = conn.cursor()
        # cur.execute('drop table lda_similarity')
        # cur.execute('ALTER TABLE lda_similarity ADD COLUMN similarity decimal(8, 7) NOT NULL')
        cur.execute('truncate table lda_similarity')

        print(f'{coo.count_nonzero()} similarities to save')
        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):

            if x == y:
                continue

            sim = float(csr[x, y])
            x_id = str(docs[x].movie_id)
            y_id = str(docs[y].movie_id)
            if sim < self.min_sim:
                continue

            if len(sims) == 100000:
                psycopg2.extras.execute_values(cur, query, sims)
                sims = []
                print(f"{no_saved} saved in {datetime.now() - start_time}")

            new_similarity = (str(created), x_id, y_id, sim)
            no_saved += 1
            sims.append(new_similarity)

        psycopg2.extras.execute_values(cur, query, sims, template=None, page_size=1000)
        conn.commit()
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    @staticmethod
    def get_conn():
        dbUsername = settings.DATABASES['default']['USER']
        dbPassword = settings.DATABASES['default']['PASSWORD']
        dbName = settings.DATABASES['default']['NAME']
        dbPort = settings.DATABASES['default']['PORT']
        conn_str = "dbname={} user={} password={} port={}".format(dbName,
                                                                  dbUsername,
                                                                  dbPassword, dbPort)
        conn = psycopg2.connect(conn_str)
        return conn


def load_data():
     docs = list(MovieDecriptions.objects.all())
     data = ["{}, {}, {}".format(d.title, d.genres, d.description) for d in docs]

     if len(data) == 0:
         print("No descriptions were found, run populate_sample_of_descriptions")

     return data, docs


if __name__ == '__main__':
    print("Calculating lda model...")

    data, docs = load_data()
    lda = LdaModel()
    lda.train(data, docs)
