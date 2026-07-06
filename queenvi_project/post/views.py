from django.views import generic
from .models import Post


class PostCreateView(generic.CreateView):
    model = Post
    fields = ["title", "content"]


class PostListView(generic.ListView):
    model = Post
    template_name = "posts/list.html"
    context_object_name = "posts"


class PostDetailView(generic.DetailView):
    model = Post
    template_name = "posts/detail.html"


class PostUpdateView(generic.UpdateView):
    model = Post
    fields = ["title", "content"]
    template_name = "posts/edit.html"
    success_url = "/posts/"


class PostDeleteView(generic.DeleteView):
    model = Post
    success_url = "/posts/"
