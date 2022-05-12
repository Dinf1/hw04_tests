from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AutoTestUser')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is a test group!',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = self.post.id
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            '/group/test_slug/': 'posts/group_list.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            '/profile/AutoTestUser/': 'posts/profile.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_new_post_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:post_create'))

    def test_post_edit_url_redirect_not_author_on_post_detail(self):
        """Страница по адресу /post/<post_id>/edit/ перенаправит всех, кроме
        автора поста на страницу поста.
        """
        user2 = User.objects.create_user(username='AutoTestUser2')
        post2 = Post.objects.create(
            author=user2,
            text='Тестовый текст #2',
            group=self.group,
        )
        post_id = post2.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(post_id,)), follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(post_id,)))

        response = self.guest_client.get(
            reverse('posts:post_edit', args=(post_id,)), follow=True
        )

        self.assertRedirects(
            response, (
                reverse('users:login') + '?next='
                + (reverse('posts:post_edit', args=(post_id,)))
            ))

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности адресов."""
        post_id = self.post.id
        templates_url_names = [
            reverse('posts:index'),
            reverse('posts:post_create'),
            (reverse('posts:group_list', args=(self.group.slug,))),
            (reverse('posts:post_detail', args=(post_id,))),
            (reverse('posts:profile', args=(self.user.username,))),
            (reverse('posts:post_edit', args=(post_id,))),
        ]
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Проверка несуществующей страницы."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
