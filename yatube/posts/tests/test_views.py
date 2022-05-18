from django import forms
from django.db.models import Max
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from posts.utils import POSTS_PER_PAGE

TESTS_RECORDS_COUNT = 11
POST_TEXT = 'Тестовый текст #{}'


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
        posts = [
            Post(
                author=cls.user,
                text=POST_TEXT.format(num + 1),
                group=cls.group
            ) for num in range(TESTS_RECORDS_COUNT)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_views_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = Post.objects.all().aggregate(Max('id'))
        post_id = post['id__max']
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:group_list', args=(self.group.slug,))):
                'posts/group_list.html',
            (reverse('posts:post_detail', args=(post_id,))):
                'posts/post_detail.html',
            (reverse('posts:profile', args=(self.user.username,))):
                'posts/profile.html',
            (reverse('posts:post_edit', args=(post_id,))):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_pages_have_correct_context(self):
        """Шаблоны index, group list и profile сформированы
        с правильным контекстом, созданный пост появляется на главной странице,
        странице пользователя и в соответствующей группе,
        также, что пост не появляется в другой группе,
        непредназначенной для этого поста."""
        user2 = User.objects.create_user(username='AutoTestUser2')
        group2 = Group.objects.create(
            title='Test group #2',
            slug='test_slug2',
            description='This is a test group #2!',
        )
        post2 = Post.objects.create(
            author=user2,
            text=POST_TEXT.format(TESTS_RECORDS_COUNT + 1),
            group=group2,
        )
        templates_url_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', args=(group2.slug,))),
            (reverse('posts:profile', args=(user2.username,))),
        ]
        for reverse_name in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.author, user2)
                self.assertEqual(
                    post.text, post2.text
                )
                self.assertEqual(post.group, group2)

        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,)
        ))
        for i in range(len(response.context['page_obj'])):
            post = response.context['page_obj'][i]
            self.assertNotEqual(
                post.text, post2.text)

    def test_first_pages_index_group_list_profile_have_ten_records(self):
        """Шаблоны index, group list и profile имееют 10 записей
        на странице."""
        templates_url_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', args=(self.group.slug,))),
            (reverse('posts:profile', args=(self.user.username,))),
        ]
        for reverse_name in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_2nd_pages_index_group_list_profile_have_necessary_records(self):
        """Шаблоны index, group list и profile имееют нужное кол-во записей на
         2ой странице."""
        templates_url_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', args=(self.group.slug,))),
            (reverse('posts:profile', args=(self.user.username,))),
        ]
        for reverse_name in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name, {'page': 2}
                )
            self.assertEqual(
                len(response.context['page_obj']),
                TESTS_RECORDS_COUNT - POSTS_PER_PAGE
            )

    def test_post_detail_has_correct_context(self):
        """Шаблон post detail имеет правильный контекст."""
        post = Post.objects.all().aggregate(Max('id'))
        post_id = post['id__max']
        response = self.client.get(
            reverse('posts:post_detail', args=(post_id,))
        )
        post = response.context['post']
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, POST_TEXT.format(post_id))
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.id, post_id)

    def test_new_post_form(self):
        """Форма добавления поста имеет правильный контекст."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
