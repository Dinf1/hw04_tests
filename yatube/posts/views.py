from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import preparation_page_obj


def index(request):
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = preparation_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group.objects.prefetch_related('posts'),
                              slug=slug
                              )
    posts = group.posts.all()
    page_obj = preparation_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(f'/profile/{request.user.username}/')
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    page_obj = preparation_page_obj(request, post_list)
    context = {
        'author': user,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(instance=post, data=request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post_id': post.id,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('group', 'author'),
                             id=post_id
                             )
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)
