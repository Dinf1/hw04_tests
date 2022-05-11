from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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
            text='Тестовый текст',
            group=cls.group,
        )
        cls.user2 = User.objects.create_user(username='AutoTestUser2')
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст #2',
            group=cls.group,
        )

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        task = PostsURLTests.post
        post_id = task.id
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
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_not_author_on_post_detail(self):
        """Страница по адресу /post/<post_id>/edit/ перенаправит всех, кроме
        автора поста на страницу поста.
        """
        post_id = PostsURLTests.post2.id
        response = self.authorized_client.get(
            f'/posts/{post_id}/edit/', follow=True
        )
        self.assertRedirects(
            response, (f'/posts/{post_id}/'))

        response = self.guest_client.get(
            f'/posts/{post_id}/edit/', follow=True
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{post_id}/edit/'))

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности адресов."""
        post_id = PostsURLTests.post.id
        templates_url_names = [
            '/',
            '/create/',
            '/group/test_slug/',
            f'/posts/{post_id}/',
            '/profile/AutoTestUser/',
            f'/posts/{post_id}/edit/',
        ]
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Проверка несуществующей страницы."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
