from django.shortcuts import get_object_or_404, render
from . models import Group, Post, User
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from . forms import PostForm
from posts . paginators import paginate_page


def index(request):
    posts = Post.objects.select_related("group", "author")
    paagination_data = paginate_page(request, posts)
    return render(
        request, "posts/index.html", {**paagination_data})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().select_related('author')
    paagination_data = paginate_page(request, posts)
    context = {
        'group': group,
        'posts': posts,
        **paagination_data
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paagination_data = paginate_page(request, post_list)
    context = {
        'author': author,
        **paagination_data
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {'post': post})


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    temp_form = form.save(commit=False)
    temp_form.author = request.user
    temp_form.save()
    return redirect('posts:profile', temp_form.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(
            'posts:post_detail', post_id
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'posts:post_detail', post_id
        )
    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)
