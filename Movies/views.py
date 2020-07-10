from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from Movies.models import Movie, Genre
from Analytics.models import Rating
from Account.models import User

import uuid, random
import json

@ensure_csrf_cookie
def index(request):


    if 'username' not in request.session:
       return redirect(reverse('account:loginPage'))

    username = request.session['username']
    api_key = get_api_key()
    movies = Movie.objects.order_by('-year', 'movie_id')
    page_number = request.GET.get("page", 1)
    page, page_start, page_end = handle_pagination(movies, page_number)

    user = User.objects.filter(username=username).first()
    if user is None:
        return redirect(reverse('account:loginPage'))
    userid = user.id

    active_user_items = Rating.objects.filter(user_id=userid).order_by('-rating')
    movie_ids = []
    for movie in active_user_items:
        movie_ids.append(movie.movie_id)
    # movie_ids = [movie['movie_id'] for movie in active_user_items]
    user_items = Movie.objects.filter(movie_id__in=movie_ids)
    # print(user_items.values())

    context_dict = {
        'movies': page,
        'api_key': api_key,
        'session_id': session_id(request),
        'user_id': userid,
        'user_name': username,
        'user_items': user_items.values(),
        'pages': range(page_start, page_end),
    }
    return render(request, 'Movies/index.html', context_dict)

@ensure_csrf_cookie
def detail(request, movie_id):
    api_key = get_api_key()
    context_dict = {
        'movie_id': movie_id,
        'api_key': api_key,
        'session_id': session_id(request),
        'user_id': user_id(request),
    }
    return render(request, 'Movies/detail.html', context_dict)

def search_for_movie(request):

    search_term = request.GET.get('q', None)
    if search_term is None:
        return redirect('/movies/')

    if 'username' not in request.session:
       return redirect(reverse('account:loginPage'))

    username = request.session['username']
    mov = Movie.objects.filter(title__icontains=search_term).order_by('-year', 'movie_id')
    api_key = get_api_key()
    page_number = request.GET.get("page", 1)
    page, page_start, page_end = handle_pagination(mov, page_number)
    context_dict = {
        'movies': page,
        'api_key': api_key,
        'session_id': session_id(request),
        'user_id': user_id(request),
        'user_name': username,
        'q': search_term,
        'pages': range(page_start, page_end),
    }
    # print(list(mov))

    return render(request, 'Movies/search.html', context_dict)

def user_id(request):
    user_id = request.GET.get("user_id")
    if user_id and len(user_id) > 5:
        request.session["user_id"] = random.randint(1, 40000)

    if not "user_id" in request.session:
        request.session["user_id"] = random.randint(1, 40000)

    # print("ensured id: ", request.session['user_id'])
    return request.session["user_id"]


# 保存会话id
def session_id(request):
    if not "session_id" in request.session:
        request.session["session_id"] = str(uuid.uuid1())
    return request.session["session_id"]


# 处理分页
def handle_pagination(movies, page_number):
    # 每页数据个数
    paginate_by = 24
    paginator = Paginator(movies, paginate_by)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page_number = 1
        page = paginator.page(page_number)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page_number = int(page_number)
    page_start = 1 if page_number < 5 else page_number - 3
    page_end = 6 if page_number < 5 else page_number + 2
    return page, page_start, page_end

# 获取themoviedb的APP key
def get_api_key():
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']

