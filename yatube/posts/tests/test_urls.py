# posts/tests/test_urls.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group
from http import HTTPStatus
User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая групппа',
            slug='test_group',
            description='Тест описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_for_anon(self):
        url = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        }
        for url in url:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_auth(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_anon_on_login(self):
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {
            '/create/': url1,
            f'/posts/{self.post.id}/edit/': url2
        }
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_post_edit_for_author(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        response = self.guest_client.get('/unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
