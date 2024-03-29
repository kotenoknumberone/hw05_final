from django import forms

from .models import Post, Comment

from django.forms import ModelForm


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

    text = forms.CharField(widget=forms.Textarea)

