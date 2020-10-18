from django.shortcuts import render, get_object_or_404

from .models import Post, Group, User, Comment, Follow

from .forms import PostForm, CommentForm

from django.shortcuts import redirect

from django.urls import reverse

from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required

from django.views.decorators.cache import cache_page


@cache_page(1 * 20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {
            'page': page,
            'paginator': paginator
        })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.all()
    paginator = Paginator(group_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  "group.html",
                  {
                      "page": page,
                      "paginator": paginator,
                      'group': group
                  })


@login_required
def new_post(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse('index'))
    return render(request,
                  'new_post.html',
                  {
                      'form': form}
                  )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower = Follow.objects.filter(author=author).count()
    following = None
    return render(request,
                  'profile.html',
                  {
                      "author": author,
                      "page": page,
                      "paginator": paginator,
                      "following": following,
                      "follower": follower,
                  })


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    form = CommentForm()
    return render(request,
                  'post.html',
                  {
                      "author": author,
                      "post": post,
                      "form": form,
                  })


def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect('post',
                        username=request.user.username,
                        post_id=post_id)
    post = get_object_or_404(Post, id=post_id, author=author)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save()
        return redirect('post',
                        username=request.user.username,
                        post_id=post_id)
    return render(request,
                  'new_post.html',
                  {
                      'form': form,
                      'post': post,
                  })


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None, username)
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user)
    if form.is_valid():
        if request.user.is_authenticated:
            form.instance.author = request.user
            form.instance.post = post
            form.save()
            return redirect('post',
                            username,
                            post_id)
        else:
            return redirect(reverse('login'))
    return render(
        request,
        'comments.html',
        {
            'form': form,
            'post': post,
        })


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    ).all()
    paginator = Paginator(posts, 7)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        "page": page,
        "paginator": paginator,
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_delete = Follow.objects.filter(user=request.user,
                                          author=author)
    follow_delete.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):

    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):

    return render(request,
                  "misc/500.html",
                  status=500)
