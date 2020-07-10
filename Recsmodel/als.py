from Recsmodel.baseModel import baseModel
from Analytics.models import Rating
from django.db.models import Q
import time
from decimal import Decimal
from Recommender.models import MF

class als(baseModel):
    def __init__(self, min_sim=0.2):
        self.min_sim = 0.2
        self.max_candidates = 100

    def recommend_items(self, user_id, num=5):
        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[:100]
        return self.recommend_items_by_ratings(user_id, active_user_items.values(), num=num)

    def recommend_items_by_ratings(self, user_id, active_user_items, num=4):
        if len(active_user_items) == 0:
            return {}

        movie_ids = [movie['movie_id'] for movie in active_user_items]
        candidate_items = MF.objects.filter(user_id=user_id)
        candidate_items = candidate_items.exclude(movie_id__in=movie_ids)
        sorted_items = candidate_items.order_by('-similarity')[:num]
        recs = []
        for mf in sorted_items:
            recs.append((mf.movie_id, mf.similarity))
        return recs

    def predict_score(self, user_id, item_id):
        return None

