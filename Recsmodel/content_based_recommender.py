from decimal import Decimal
from django.db.models import Q
from Analytics.models import Rating
from Recommender.models import MovieDecriptions,LdaSimilarity
from Recsmodel.baseModel import baseModel



class ContentBasedRecs(baseModel):
    def __init__(self, min_sim= 0.1):
        self.min_sim = min_sim
        self.max_candidates = 100

    def recommend_items(self, user_id, num=5):

        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[:100]
        return self.recommend_items_by_ratings(user_id, active_user_items.values(), num)

    def recommend_items_by_ratings(self,user_id,active_user_items,num=5):

        if len(active_user_items) == 0:
            return {}
        movie_ids = {movie['movie_id']: movie['rating'] for movie in active_user_items}
        user_mean = sum(movie_ids.values()) / len(movie_ids)
        sims = LdaSimilarity.objects.filter(Q(source__in=movie_ids.keys())
                                        &~Q(target__in=movie_ids.keys())
                                        &Q(similarity__gt=self.min_sim))

        # print(active_user_items)
        sims = sims.order_by('-similarity')[:self.max_candidates]

        recs = dict()
        targets = set(s.target for s in sims if not s.target == '')
        for target in targets:
            pre = 0
            sim_sum = 0
            rated_items = [i for i in sims if i.target == target]
            if len(rated_items) > 0:
                for sim_item in rated_items:
                    r = Decimal(movie_ids[sim_item.source] - user_mean)
                    pre += sim_item.similarity * r
                    sim_sum += sim_item.similarity
                    if sim_sum > 0:
                        recs[target] = {'prediction': Decimal(user_mean) + pre / sim_sum,
                                'sim_items': [r.source for r in rated_items]}
        return sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]

    def recommend_items_item_id(self, user_id, item_id, num=5):

        active_items = Rating.objects.filter(movie_id=item_id).order_by('-rating')[:100]
        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[:100]
        return self.recommend_items_by_ratings_item_id(item_id, active_user_items.values(), active_items.values(), num)

    def recommend_items_by_ratings_item_id(self, item_id, active_user_items, active_items, num=5):

        if len(active_items) == 0:
            return {}

        user_ids = {movie['user_id']: movie['rating'] for movie in active_items}
        movie_ids = {movie['movie_id']: movie['rating'] for movie in active_user_items}
        # 计算物品平均得分
        item_mean = sum(user_ids.values()) / len(user_ids)
        # 查询与物品id符合相似度的候选物品id
        sims = LdaSimilarity.objects.filter(Q(source=item_id)
                                        &~Q(target=item_id)
                                        &Q(similarity__gt=self.min_sim))
        print(sims)

        # print(active_user_items)
        sims = sims.order_by('-similarity')[:self.max_candidates]

        recs = dict()
        for sim in sims:
            pre = 0
            if sim.target not in movie_ids:
                pre += sim.similarity * item_mean
                recs[sim.target] = {'prediction': pre,
                                'sim_items': [sim.source]}

        return sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]

    def predict_score(self, user_id, item_id):
        return None
