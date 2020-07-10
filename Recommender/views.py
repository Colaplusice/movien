from django.db.models import Avg
from django.http import JsonResponse

from Collector.models import Log
from Movies.models import Movie
from Recommender.models import SeededRecs
from Recsmodel.als import als
from Recsmodel.content_based_recommender import ContentBasedRecs
from Recsmodel.content_hybird_recommender import ContentHybridRecs
from Recsmodel.neighborhoodCF import NeighborhoodRecs
from Recsmodel.popularity import Popularity


# Create your views here.

def chart(request, take=10):
    sorted_items = Popularity().recommend_items_from_log(take)
    ids = [i['content_id'] for i in sorted_items]
    ms = {m['movie_id']: m['title'] for m in
          Movie.objects.filter(movie_id__in=ids).values('title', 'movie_id')}
    if len(ms) > 0:
        sorted_items = [{'movie_id': i['content_id'],
                         'title': ms[i['content_id']]} for i in sorted_items]
    else:
        print("No data for chart found. This can either be because of missing data, or missing movie data")
        sorted_items = []
    data = {
        'data': sorted_items
    }

    return JsonResponse(data, safe=False)


def recs_cf(request, user_id, num=6):
    min_sim = request.GET.get('min_sim', 0.1)
    sorted_items = NeighborhoodRecs(min_sim=min_sim).recommend_items(user_id=user_id, num=num)
    # print(f"cf sorted_items is: {sorted_items}")
    data = {
        'user_id': user_id,
        'data': sorted_items
    }
    return JsonResponse(data, safe=False)


def recs_mf(request, user_id, num=6):
    min_sim = request.GET.get('min_sim', 0.1)
    sorted_items = als(min_sim=min_sim).recommend_items(user_id=user_id, num=num)
    print(f"mf sorted_items is: {sorted_items}")
    data = {
        'user_id': user_id,
        'data': sorted_items
    }
    return JsonResponse(data, safe=False)


def recs_cb(request, user_id, num=6):
    # sorted_items = ContentBasedRecs().recommend_items(user_id, num)
    sorted_items = ContentBasedRecs().recommend_items_item_id(user_id, num)
    print(f"cb sorted_items is: {sorted_items}")
    data = {
        'user_id': user_id,
        'data': sorted_items
    }

    return JsonResponse(data, safe=False)


def recs_item(request, user_id, movie_id, num=6):
    sorted_items = ContentBasedRecs().recommend_items_item_id(user_id, movie_id, num)
    print(f"cb sorted_items is: {sorted_items}")
    data = {
        'user_id': user_id,
        'data': sorted_items
    }

    return JsonResponse(data, safe=False)


def recs_hf(request, user_id, num=6):
    sorted_items = ContentHybridRecs().recommend_items(user_id, num)
    # print(f"hf sorted_items is: {sorted_items}")
    data = {
        'user_id': user_id,
        'data': sorted_items
    }
    #
    return JsonResponse(data, safe=False)


def recs_using_association_rules(request, user_id, take=6):
    events = Log.objects.filter(user_id=user_id) \
        .order_by('created') \
        .values_list('content_id', flat=True) \
        .distinct()

    seeds = set(events[:20])

    rules = SeededRecs.objects.filter(source__in=seeds) \
        .exclude(target__in=seeds) \
        .values('target') \
        .annotate(confidence=Avg('confidence')) \
        .order_by('-confidence')

    recs = [{'id': '{0:07d}'.format(int(rule['target'])),
             'confidence': rule['confidence']} for rule in rules]

    print("recs from association rules: \n{}".format(recs[:take]))
    return JsonResponse(dict(data=list(recs[:take])))
