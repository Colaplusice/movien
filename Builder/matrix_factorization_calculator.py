import numpy as np
import pandas as pd
import os
import psycopg2
from tqdm import tqdm
from datetime import datetime
from scipy.sparse import coo_matrix

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Recs.settings")
import django
django.setup()

from Analytics.models import Rating
from Recs import settings

class MatrixFactorization(object):

    def __init__(self, min_sim=0):
        self.min_sim = min_sim
        self.db = settings.DATABASES['default']['ENGINE']


    def train(self, c_ui, factors = 50, regularization = 0.01, iterations=15):
        print("calculating Matrix ... using {} ratings".format(len(c_ui)))
        start_time = datetime.now()

        print("Creating ratings matrix")
        c_ui['rating'] = (c_ui['rating'] - c_ui['rating'].min()) / (c_ui['rating'].max() - c_ui['rating'].min())
        c_ui['rating'] = c_ui['rating'].astype(float)
        # 计算每个user_id的平均评分，并做归一化处理
        # c_ui['avg'] = c_ui.groupby('user_id')['rating'].transform(lambda x: normalize(x))
        #
        # # 把user_id， movie_id转为pandas的类别，以便去重
        # c_ui['avg'] = c_ui['avg'].astype(float)
        c_ui['user_id'] = c_ui['user_id'].astype('category')
        c_ui['movie_id'] = c_ui['movie_id'].astype('category')


        # 构建稀疏评分矩阵，即没有评分的数据全部用0来填充
        coo = coo_matrix((c_ui['rating'].astype(float),
                          (c_ui['movie_id'].cat.codes.copy(),
                           c_ui['user_id'].cat.codes.copy())))

        users, items = coo.shape
        print("Ratings matrix finished， in {} seconds".format(datetime.now() - start_time))

        start_time = datetime.now()
        print("Calculating ALS....")
        # 随机初始化两个隐语义矩阵X,Y
        X = np.random.rand(users, factors) * 0.01
        Y = np.random.rand(items, factors) * 0.01

        cui, ciu = coo.tocsr(), coo.T.tocsr()

        for iteration in range(iterations):
            self.least_squares_cg(cui=cui, X=X, Y=Y, regularization=regularization,)
            self.least_squares_cg(cui=ciu, X=Y, Y=X, regularization=regularization,)

        print("Rating matrix (size {}x{}) finished, in {} seconds".format(coo.shape[0],
                                                                          coo.shape[1],
                                                                          datetime.now() - start_time))

        sim = np.dot(X, Y.T)
        movies_ = dict(enumerate(c_ui['movie_id'].cat.categories))
        users_ = dict(enumerate(c_ui['user_id'].cat.categories))

        self.save_similarity(sim_matrix=sim, movies=movies_, users=users_)
        # # print(sim)
        # self.rmse(coo, sim)
        return X, Y

    # ALS算法/共轭梯度法
    def least_squares_cg(self, cui, X, Y, regularization, cg_steps=3):
        users, factors = X.shape
        YtY = Y.T.dot(Y) + regularization * np.eye(factors)

        for u in range(users):
            # start from previous iteration
            x = X[u]

            # calculate residual r = (YtCuPu - (YtCuY.dot(Xu), without computing YtCuY
            r = -YtY.dot(x)
            for i, confidence in self.nonzeros(cui, u):
                r += (confidence - (confidence - 1) * Y[i].dot(x)) * Y[i]

            p = r.copy()
            rsold = r.dot(r)

            for it in range(cg_steps):
                # calculate Ap = YtCuYp - without actually calculating YtCuY
                Ap = YtY.dot(p)
                for i, confidence in self.nonzeros(cui, u):
                    Ap += (confidence - 1) * Y[i].dot(p) * Y[i]

                # standard CG update
                alpha = rsold / p.dot(Ap)
                x += alpha * p
                r -= alpha * Ap
                rsnew = r.dot(r)
                p = r + (rsnew / rsold) * p
                rsold = rsnew

            X[u] = x

    # 返回CSR矩阵非零元素的索引和值
    def nonzeros(self, m, row):
        """ returns the non zeroes of a row in csr_matrix """
        for index in range(m.indptr[row], m.indptr[row + 1]):
            yield m.indices[index], m.data[index]




    def rmse(self, coo, sim):
        #  取出评分大于0的数据
        start_time = datetime.now()
        print('instantiation of coo_matrix in {} seconds'.format(datetime.now() - start_time))
        csr = coo.tocsr()
        print('Calculating rmse....')
        mse = 0.0
        xs, ys = coo.nonzero()
        number = len(coo.data)
        for x, y in tqdm(zip(xs, ys), leave=True):

            y_r = csr[x, y]
            if y_r > 0:
                y_hat = sim[x][y]
                square_error = (y_r - y_hat) ** 2
                mse += square_error
        print('RMSE {}'.format((mse / number) ** 0.5))

    @staticmethod
    def get_connect():
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            dbUsername = settings.DATABASES['default']['USER']
            dbPassword = settings.DATABASES['default']['PASSWORD']
            dbName = settings.DATABASES['default']['NAME']
            dbPort = settings.DATABASES['default']['PORT']
            conn_str = "dbname={} user={} password={} port={}".format(dbName,
                                                              dbUsername,
                                                              dbPassword, dbPort)
            conn = psycopg2.connect(conn_str)
        return conn

    def save_similarity(self, sim_matrix, movies, users, created=datetime.now()):
        start_time = datetime.now()
        print('truncating table in {} seconds'.format(datetime.now() - start_time))
        sims = []
        no_saved = 0
        start_time = datetime.now()
        print('instantiation of coo_matrix in {} seconds'.format(datetime.now() - start_time))

        query = "insert into similarity_mf (created, user_id, movie_id, similarity) values %s;"
        conn = self.get_connect()
        cur = conn.cursor()

        cur.execute('truncate table similarity_mf')

        print('{} similarities to save'.format(len(sim_matrix)))
        row, column = sim_matrix.shape
        for i in tqdm(range(row)):
            for j in range(column):
                sim = sim_matrix[i][j]
                if sim < self.min_sim:
                    continue
                if (len(sims)) == 500000:
                    psycopg2.extras.execute_values(cur, query, sims)
                    sims = []
                    print("{} saved in {}".format(no_saved,
                                                  datetime.now() - start_time))
                new_similarity = (str(created), users[j], movies[i], sim)
                no_saved += 1
                sims.append(new_similarity)

        psycopg2.extras.execute_values(cur, query, sims, template=None, page_size=1000)
        conn.commit()
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))


def load_all_ratings(min_ratings=1):
    columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

    ratings_data = Rating.objects.all().values(*columns)
    # ratings_data = Rating.objects.all().filter(user_id__range=(0, 4000)).values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)

    user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
    user_count = user_count.reset_index()
    user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
    ratings = ratings[ratings['user_id'].isin(user_ids)]

    ratings['rating'] = ratings['rating'].astype(float)
    return ratings



if __name__ == '__main__':
    all_ratings = load_all_ratings()
    model = MatrixFactorization(min_sim=0.1)
    X, Y = model.train(c_ui=all_ratings, factors=50, regularization=0.01, iterations=1)
