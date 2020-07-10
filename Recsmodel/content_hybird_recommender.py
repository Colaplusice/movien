from Recsmodel.baseModel import baseModel
from Analytics.models import Rating
from django.db.models import Q
import time
from decimal import Decimal
from Recommender.models import Similarity, LdaSimilarity
from itertools import chain

class ContentHybridRecs(baseModel):
    def __init__(self, min_sim=0):
        self.min_sim = min_sim
        self.max_candidates = 100

    def recommend_items(self, user_id, num=6):
        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')
        return self.recommend_items_by_items(active_user_items.values(), num)

    def recommend_items_by_items(self, active_user_items, num):

        if len(active_user_items) == 0:
            return {}

        movie_ids = {movie['movie_id']: movie['rating'] for movie in active_user_items}
        user_mean = sum(movie_ids.values()) / len(movie_ids)
        candidate_items_sim = Similarity.objects.filter(Q(source__in=movie_ids.keys())
                                                    & ~Q(target__in=movie_ids.keys())
                                                    & Q(similarity__gt=self.min_sim)
                                                    )
        candidate_items_lda = LdaSimilarity.objects.filter(Q(source__in=movie_ids.keys())
                                                        & ~Q(target__in=movie_ids.keys())
                                                        & Q(similarity__gt=self.min_sim)
                                                        )

        # candidate_items = candidate_items_sim.order_by('-similarity')[:self.max_candidates]
        # candidate_items_1 = candidate_items.values_list('source', 'target')

        candidate_items_1 = candidate_items_sim.order_by('-similarity')[:self.max_candidates].values_list('source',
                                                                                                          'target')

        # candidate_items = candidate_items_lda.order_by('-similarity')[:self.max_candidates]
        candidate_items = candidate_items_lda.order_by('-similarity')
        candidate_items_2 = candidate_items.values_list('source', 'target')

        intersection_items = list(candidate_items_1.intersection(candidate_items_2))

        a = 0.2
        for candidate in candidate_items:
            source = candidate.source
            target = candidate.target
            similarity = candidate.similarity
            if (source, target) in intersection_items:
                candidate.similarity = Decimal(a) * similarity + Decimal(1-a) * similarity
            else:
                candidate.similarity = Decimal(a) * similarity

        recs = dict()
        for candidate in candidate_items:
            target = candidate.target
            pre = 0
            sim_sum = 0
            rated_items = [i for i in candidate_items if i.target == target][:self.max_candidates]
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

    def calculator_score(self, active_user_items, target):
        lamd = 0.5
        sims = 0
        score = 0
        items_for_user = Rating.objects.filter(movie_id=target).order_by('-rating')[
                         :self.max_candidates]
        movie_ids = {movie.movie_id: movie.rating for movie in items_for_user}
        item_mean = sum(movie_ids.values()) / len(movie_ids)
        for movie in active_user_items:
            # 取出lda物品相似度
            lda = LdaSimilarity.objects.filter(Q(source=movie.movie_id)
                                           & Q(target=target)).first()
            # 取出余弦相似度
            sim = Similarity.objects.filter(Q(source=movie.movie_id)
                                            & Q(target=target)).first()
            if lda and sim:
                # 混合相似度
                hybrid_sim = Decimal(lamd) * (sim.similarity + Decimal(1 - lamd) * lda.similarity)
                sims += hybrid_sim
                score += hybrid_sim * (movie.rating - item_mean)
        if score > 0 and sims > 0:
            return target, (item_mean + score/sims)
        return target, item_mean

    def predict_score(self, user_id, item_id):
        return None