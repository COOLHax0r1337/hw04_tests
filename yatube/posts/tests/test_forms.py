from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()

CREATE_POST_URL = reverse('posts:post_create')


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'})
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_create_post(self):
        initial_posts = set(Post.objects.all())
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'author': self.user,
        }
        response = self.authorized_client.post(
            CREATE_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.PROFILE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        final_posts = set(Post.objects.all()) - initial_posts
        self.assertEqual(len(final_posts), 1)
        post = final_posts.pop()
        forms = {
            post.author: 'author',
            post.text: 'text',
            post.group.pk: 'group',
        }
        for form, value in forms.items():
            with self.subTest(form=form):
                self.assertEqual(form, form_data[value])

    def test_forms_edit_post(self):
        self.group2 = Group.objects.create(
            title='test_group2',
            slug='test_slug2',
            description='Тестовое описание2'
        )
        form_data = {
            'text': 'Измененный тестовый текст',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        forms = {
            post.text: 'text',
            post.group.pk: 'group',
        }
        for form, value in forms.items():
            with self.subTest(form=form):
                self.assertEqual(form, form_data[value])
