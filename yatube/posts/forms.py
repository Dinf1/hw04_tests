from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {'text': 'Текст', 'group': 'Группа'}
        help_texts = {'text': 'Текст поста',
                      'group': 'Группа, к которой будет относиться пост'}

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Пост не может быть пустым!')
        return data
