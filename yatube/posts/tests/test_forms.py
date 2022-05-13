from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AutoTestUser')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is a test group!',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_form(self):
        """при отправке валидной формы со страницы создания поста создаётся
        новая запись в базе данных"""
        count = Post.objects.count()
        response = self.authorized_client.post(reverse('posts:post_create'), {
            'text': 'Тестовый текст #1', 'group': 1}, follow=True)
        self.assertRedirects(
            response, (reverse('posts:profile', args=(self.user.username,)))
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text='Тестовый текст #1',
                author=self.user
            ).exists()
        )
        self.assertEqual(Post.objects.count(), count + 1)

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст #2',
            group=self.group,
        )
        self.authorized_client.post(reverse(
            'posts:post_edit', args=(post.id,)
        ), {
            'text': 'Тестовый текст #3',
            'group': 1
        }
        )
        post2 = Post.objects.get(pk=post.id)
        self.assertNotEqual(post2.text, post.text)
        self.assertEqual(post2.group, self.group)
        self.assertEqual(post2.author, self.user)
