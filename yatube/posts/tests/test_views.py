from random import randint

from django import forms
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
        for i in range(10):
            Post.objects.create(
                author=cls.user,
                text='Тестовый текст #' + str(i + 3),
                group=cls.group,
            )

    def test_views_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = PostsViewsTests.post.id
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:group_list', kwargs={'slug': 'test_slug'})):
                'posts/group_list.html',
            (reverse('posts:post_detail', kwargs={'post_id': post_id})):
                'posts/post_detail.html',
            (reverse('posts:profile', kwargs={'username': 'AutoTestUser'})):
                'posts/profile.html',
            (reverse('posts:post_edit', kwargs={'post_id': post_id})):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_has_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_id = randint(3, 12)
        object = response.context['page_obj'][12 - post_id]
        self.assertEqual(object.author, self.user)
        self.assertEqual(object.text, 'Тестовый текст #' + str(post_id))
        self.assertEqual(object.group, self.group)

    def test_first_index_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), RECORS_PER_PAGE)

    def test_second_index_page_contains_two_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_group_list_has_correct_context_and_ten_records(self):
        """Шаблон group_list сформирован с правильным контекстом
        и имеет 10 записей."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        for i in range(len(response.context['page_obj'])):
            object = response.context['page_obj'][i]
            self.assertEqual(object.group, self.group)
        self.assertEqual(len(response.context['page_obj']), RECORS_PER_PAGE)

    def test_second_page_group_list_has_correct_context_and_two_records(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
            + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 2)
        for i in range(len(response.context['page_obj'])):
            object = response.context['page_obj'][i]
            self.assertEqual(object.group, self.group)

    def test_profile_has_correct_context_and_ten_records(self):
        """Шаблон profile сформирован с правильным контекстом
        и имеет 10 записей."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'AutoTestUser'})
        )
        i = 0
        while i < len(response.context['page_obj']):
            object = response.context['page_obj'][i]
            self.assertEqual(object.author, self.user)
            i += 1
        self.assertEqual(len(response.context['page_obj']), RECORS_PER_PAGE)

    def test_second_profile_page_has_correct_context_and_one_record(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'AutoTestUser'})
            + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].author, self.user)

    def test_post_detail_has_correct_context(self):
        post_id = randint(1, 12)
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        post = response.context['post']
        if post_id == 2:
            self.assertEqual(post.author, self.user2)
        else:
            self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, 'Тестовый текст #' + str(post_id))
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.id, post_id)

    def test_new_edit_post_form(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        response = self.authorized_client.post(reverse('posts:post_create'), {
            'text': 'Тестовый текст #13', 'group': 1}, follow=True)
        self.assertRedirects(
            response, (reverse('posts:profile',
                               kwargs={'username': 'AutoTestUser'})))
        post = Post.objects.get(pk=13)
        self.assertEqual(post.text, 'Тестовый текст #13')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.id, 13)
        self.assertEqual(post.author, self.user)

    def test_post_edit(self):
        post_id = randint(3, 12)
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
