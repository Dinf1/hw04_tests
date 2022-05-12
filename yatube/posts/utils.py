from django.core.paginator import Paginator

POSTS_PER_PAGE = 10


def preparation_page_obj(request, post_list):
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
