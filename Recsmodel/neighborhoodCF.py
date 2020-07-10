from Recsmodel.baseModel import baseModel
from Analytics.models import Rating
from django.db.models import Q
import time
from decimal import Decimal
from Recommender.models import Similarity

class NeighborhoodRecs(baseModel):

    def __init__(self, neighborhood_size=10, min_sim=0):
        # 最近邻个数，最小相似度，最大候选集个数
        self.neighborhood_size = neighborhood_size
        self.min_sim = min_sim
        self.max_candidates = 100

    def recommend_items(self, user_id, num=5):

        # 取出用户有过的评分信息
        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[0: self.max_candidates]
        # print(user_id, active_user_items.values())
        return self.recommend_item_by_ratings(active_user_items.values(), num)

     # 推荐
    def recommend_item_by_ratings(self, active_user_items, num=6):
        #  如果没有评分过的项目则返回空
        if len(active_user_items) == 0:
            return {}


        # 标记时间
        start = time.time()
        movie_ids = {movie['movie_id']: movie['rating'] for movie in active_user_items}

        # 用户平均评分
        user_mean = sum(movie_ids.values()) / len(movie_ids)
        candidate_items = Similarity.objects.filter(Q(source__in=movie_ids.keys())
                                                    & ~Q(target__in=movie_ids.keys())
                                                    & Q(similarity__gt=self.min_sim)
                                                    )
        # print(candidate_items)
        candidate_items = candidate_items.order_by('-similarity')[:self.max_candidates]
        recs = dict()
        for candidate in candidate_items:
            target = candidate.target
            pre = 0
            sim_sum = 0
            rated_items = [i for i in candidate_items if i.target == target][:self.neighborhood_size]
            # print(rated_items)
            if len(rated_items) > 0:
                for sim_item in rated_items:
                    r = Decimal(movie_ids[sim_item.source] - user_mean)
                    pre += sim_item.similarity * r
                    sim_sum += sim_item.similarity

                if sim_sum > 0:
                    recs[target] = {'prediction': Decimal(user_mean) + pre / sim_sum,
                                    'sim_items': [r.source for r in rated_items]}


        sorted_items = sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]
        return sorted_items

    def predict_score(self, user_id, item_id):

        user_items = Rating.objects.filter(user_id=user_id)
        user_items = user_items.exclude(movie_id=item_id).order_by('-rating')[:100]
        movie_ids = {movie.movie_id: movie.rating for movie in user_items}

        return self.predict_score_by_ratings(item_id, movie_ids)

    def predict_score_by_ratings(self, item_id, movie_ids):
        top = Decimal(0.0)
        bottom = Decimal(0.0)
        ids = movie_ids.keys()
        mc = self.max_candidates
        candidate_items = (Similarity.objects.filter(source__in= ids)
                                             .exclude(source=item_id)
                                             .filter(target=item_id))
        candidate_items = candidate_items.distinct().order_by('-similarity')[:mc]

        if len(candidate_items) == 0:
            return 0

        for sim_item in candidate_items:
            r = movie_ids[sim_item.source]
            top += sim_item.similarity * r
            bottom += sim_item.similarity

        return Decimal(top/bottom)
