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
        cls.group2 = Group.objects.create(
            title='Test group #2',
            slug='test_slug2',
            description='This is a test group #2!',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_form(self):
        """при отправке валидной формы со страницы создания поста создаётся
        новая запись в базе данных, пост появляется на главной, странице
        пользователя и в соответствующей группе, также, что пост не появляется
        в другой группе, непредназначенной для этого поста"""
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
        templates_url_names = [
            reverse('posts:index'),
            (reverse('posts:group_list', args=(self.group.slug,))),
            (reverse('posts:profile', args=(self.user.username,))),
        ]
        for reverse_name in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                object = response.context['page_obj'][0]
                self.assertEqual(object.author, self.user)
                self.assertEqual(object.text, 'Тестовый текст #1')
                self.assertEqual(object.group, self.group)

        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group2.slug,)
        ))
        for i in range(len(response.context['page_obj'])):
            object = response.context['page_obj'][i]
            self.assertNotEqual(object.text, 'Тестовый текст #1')

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных."""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст #2',
            group=self.group,
        )
        post_id = self.post.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(post_id,))
        )
        post_text = response.context['form']['text'].value()
        post_group = response.context['form']['group'].value()
        self.assertEqual(post_text, 'Тестовый текст #2')
        self.assertEqual(post_group, 1)

        self.authorized_client.post(reverse(
            'posts:post_edit', args=(post_id,)
        ), {
            'text': 'Тестовый текст #3',
            'group': 1
        }
        )
        post = Post.objects.get(pk=post_id)
        self.assertNotEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
