from decimal import Decimal
from Collector.models import Log
from django.db.models import Count
from django.db.models import Q
from django.db.models import Avg
from Recsmodel.baseModel import baseModel

# 流行度推荐
class Popularity(baseModel):
    def predict_score(self, user_id, item_id):
        return None
    def recommend_items(self, user_id, num=5):
        return None
    @staticmethod
    def recommend_items_from_log(num=5):
        items = Log.objects.values('content_id')
        items = items.filter(event='like').annotate(Count("user_id"))
        sorted_items = sorted(items, key=lambda item: -float(item['user_id__count']))
        return sorted_items[:num]