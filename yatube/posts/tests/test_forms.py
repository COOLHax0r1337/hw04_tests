from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='test_group2',
            slug='test_slug2',
            description='Тестовое описание2'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{self.user.username}'})
        self.CREATE_POST_URL = reverse('posts:post_create')

    def test_auth_user_can_publish_post(self):
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'author': self.user,
        }
        response = self.authorized_client.post(
            self.CREATE_POST_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.text, form_data['text'])

    def test_forms_edit_post(self):
        post = Post.objects.create(
            text='test',
            author=self.user,
            group=self.group
        )
        form_data = {
            'text': 'Измененный тестовый текст',
            'group': self.group2.id,
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        post = set(Post.objects.all()).pop()
        mapping = {
            post.text: form_data['text'],
            post.group.pk: form_data['group'],
            post.author: self.user
        }
        for form, value in mapping.items():
            with self.subTest(form=form):
                self.assertEqual(form, value)

    def test_unauth_user_cant_publish_post(self):
        form_data = {'text': 'Текст в форме'}
        response = self.guest_client.post(
            self.CREATE_POST_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '/auth/login/?next=/create/')
