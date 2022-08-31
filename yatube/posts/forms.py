from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {
            'text': 'текст поста',
            'group': 'группа поста',
            'image': 'картинка поста'
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, в которой будет размещён пост',
            'image': 'Загрузите картинку'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'текст комментария'
        }
        help_texts = {
            'text': 'Вы можете оставить здесь свой комментарий'
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 30, 'rows': 5})
        }
