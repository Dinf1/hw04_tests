from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

RECORS_PER_PAGE = 10


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='AutoTestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is a test group!',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст #1',
            group=cls.group,
        )
        cls.user2 = User.objects.create_user(username='AutoTestUser2')
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст #2',
            group=cls.group,
        )

    def test_new_edit_post_form(self):
        """при отправке валидной формы со страницы создания поста создаётся
        новая запись в базе данных"""
        response = self.authorized_client.post(reverse('posts:post_create'), {
            'text': 'Тестовый текст #3', 'group': 1}, follow=True)
        self.assertRedirects(
            response, (reverse('posts:profile',
                               kwargs={'username': 'AutoTestUser'})))
        post = Post.objects.get(pk=3)
        self.assertEqual(post.text, 'Тестовый текст #3')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.id, 3)
        self.assertEqual(post.author, self.user)

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных."""
        post_id = 1
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id})
        )
        post_text = response.context['form']['text'].value()
        post_group = response.context['form']['group'].value()
        self.assertEqual(post_text, 'Тестовый текст #' + str(post_id))
        self.assertEqual(post_group, 1)

        self.authorized_client.post(reverse(
                                    'posts:post_edit',
                                    kwargs={'post_id': post_id}
                                    ), {
                                    'text': 'Тестовый текст #'
                                    + str(post_id * 2),
                                    'group': 1
                                    }
                                    )
        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.text, 'Тестовый текст #' + str(post_id * 2))
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.id, post_id)
        self.assertEqual(post.author, self.user)
