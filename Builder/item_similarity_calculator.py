import os
from tqdm import tqdm
from datetime import datetime
import pandas as pd
import psycopg2
from scipy.sparse import coo_matrix, csr_matrix
import numpy as np
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Recs.settings")
import django
django.setup()
from Analytics.models import Rating
from Recs import settings


class ItemSimilarityMatrixBuilder(object):
    def __init__(self, min_overlap=15, min_sim=0):
        # 同时对item1和item2有过评分的最小用户数
        self.min_overlap = min_overlap
        # 最小相似度
        self.min_sim = min_sim
        self.db = settings.DATABASES['default']['ENGINE']

    # ratings评分数据，save是否保存到数据库，默认保存
    def build(self, ratings, save=True):
        print("calculating similarities ... using {} ratings".format(len(ratings)))
        start_time = datetime.now()

        print("Creating ratings matrix")
        ratings['rating'] = ratings['rating'].astype(float)
        # 计算每个user_id的平均评分，并做归一化处理
        ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))

        # 把user_id， movie_id转为pandas的类别，以便去重
        ratings['avg'] = ratings['avg'].astype(float)
        ratings['user_id'] = ratings['user_id'].astype('category')
        ratings['movie_id'] = ratings['movie_id'].astype('category')

        # 构建稀疏评分矩阵，即没有评分的数据全部用0来填充
        coo = coo_matrix((ratings['avg'].astype(float),
                          (ratings['movie_id'].cat.codes.copy(),
                           ratings['user_id'].cat.codes.copy())))

        # 计算两个item间的重叠个数，即同时对item1和item2有过评分的用户数
        print("Calculating overlaps between the items")
        overlap_matrix = coo.astype(bool).astype(int).dot(coo.transpose().astype(bool).astype(int))
        # 重叠部分大于min_overlap的item数量
        number_of_overlaps = (overlap_matrix > self.min_overlap).count_nonzero()
        print("Overlap matrix leaves {} out of {} with {}".format(number_of_overlaps,
                                                                         overlap_matrix.count_nonzero(),
                                                                         self.min_overlap))
        print("Rating matrix (size {}x{}) finished, in {} seconds".format(coo.shape[0],
                                                                                coo.shape[1],
                                                                                datetime.now() - start_time))
        sparsity_level = 1 - (ratings.shape[0] / (coo.shape[0] * coo.shape[1]))
        print("Sparsity level is {}".format(sparsity_level))

        start_time = datetime.now()
        # 初始化一个为0的相似度矩阵
        print("Calculating similarity between the items")
        cor = self.calculating_similarity(coo)
        # cor = cosine_similarity(coo, dense_output=False)
        # print(type(cor))
        # print(cor)
        # 相似度大于最小相似度的元素进行对应位置相乘
        cor = cor.multiply(cor > self.min_sim)
        # 相似度大于最小重叠度的元素进行对应位置相乘
        cor = cor.multiply(overlap_matrix > self.min_overlap)
        print(cor)
        movies = dict(enumerate(ratings['movie_id'].cat.categories))
        print('Correlation is finished, done in {} seconds'.format(datetime.now() - start_time))
        if save:
            start_time = datetime.now()
            print('save starting')
            if self.db == 'django.db.backends.postgresql':
                self.save_similarity(cor, movies)

            print('save finished, done in {} seconds'.format(datetime.now() - start_time))

        return cor, movies

     # 计算相似度优化算法，从sklearn得到的启发
    def calculating_similarity(self, coo):
        # 稀疏矩阵转numpy 数组
        data_array = coo.toarray()
        data_array = check_array(data_array)
        # 爱因斯坦求和约定，即对两个矩阵按元素位置对应相乘，之后按行求和
        # [[1 2 3]  [[1 2 3]     [[1 4 9]  [14, 14]
        # [1 2 3]]   [1 2 3]]    [1 4 9]]
        norms = np.einsum('ij,ij->i', data_array, data_array)
        np.sqrt(norms, norms)
        norms[norms == 0.0] = 1.0
        data_array /= norms[:, np.newaxis]

        # 运算完之后需要把numpy 的多维数组或矩阵转为scipy的稀疏矩阵进行计算，否则汇报内存溢出
        array_sparse = csr_matrix(data_array)
        sim_matrix = array_sparse @ array_sparse.transpose()
        return sim_matrix

    def save_similarity(self, sim_matrix, index, created=datetime.now()):
        start_time = datetime.now()
        print('truncating table in {} seconds'.format(datetime.now() - start_time))
        sims = []
        no_saved = 0
        start_time = datetime.now()
        print('instantiation of coo_matrix in {} seconds'.format(datetime.now() - start_time))
        coo = coo_matrix(sim_matrix)
        csr = coo.tocsr()

        query = "insert into similarity (created, source, target, similarity) values %s;"
        conn = self.get_connect()
        cur = conn.cursor()

        cur.execute('truncate table similarity')

        print('{} similarities to save'.format(coo.count_nonzero()))
        xs, ys = coo.nonzero()
        for x, y in tqdm(zip(xs, ys), leave=True):
            if x == y:
                continue
            sim = csr[x, y]

            if sim < self.min_sim:
                continue

            if (len(sims)) == 500000:
                psycopg2.extras.execute_values(cur, query, sims)
                sims = []
                print("{} saved in {}".format(no_saved,
                                                    datetime.now() - start_time))

            new_similarity = (str(created), index[x], index[y], sim)
            no_saved += 1
            sims.append(new_similarity)

        psycopg2.extras.execute_values(cur, query, sims, template=None, page_size=1000)
        conn.commit()
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))



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

# 检查数据类型
def check_array(array, dtype="numeric", order=None):

    array_orig = array
    dtype_numeric = isinstance(dtype, str) and dtype == "numeric"
    dtype_orig = getattr(array, "dtype", None)
    if dtype_numeric:
        if dtype_orig is not None and dtype_orig.kind == "O":
            # if input is object, convert to float.
            dtype = np.float64
        else:
            dtype = None

    if np.may_share_memory(array, array_orig):
        array = np.array(array, dtype=dtype, order=order)

    return array


#  归一化
def normalize(x):
    x = x.astype(float)
    # 计算value的和
    x_sum = x.sum()
    # 计算大于0的元素个数
    x_num = x.astype(bool).sum()
    # 计算均值
    x_mean = 0
    if x_num > 0:
        x_mean = x_sum / x_num
    if x_num == 1 or x.std() == 0:
        return 0.0
    return (x - x_mean) / (x.max() - x.min())


#  加载评分数据
def load_all_ratings(min_ratings=1):
    # 提取相关列的数据
    columns = ['user_id', 'movie_id', 'rating', 'type']
    ratings_data = Rating.objects.all().values(*columns)
    # ratings_data = Rating.objects.all().filter(user_id__range=(0, 4000)).values(*columns)
    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    # 通过user_id分类，统计每个user_id评分过的item数量
    user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
    user_count = user_count.reset_index()
    # 取出评分item数量超过min_ratings的所有user_id
    user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
    # 取出user_ids的评分数据记录
    ratings = ratings[ratings['user_id'].isin(user_ids)]
    # 将评分数据转换成float类型
    ratings['rating'] = ratings['rating'].astype(float)

    return ratings

def main():
    print("Calculation of item similarity")
    all_ratings = load_all_ratings()
    ItemSimilarityMatrixBuilder().build(all_ratings)

if __name__ == '__main__':
    main()
