from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group


User = get_user_model()

INDEX_URL = reverse('posts:index')
CREATE_POST_URL = reverse('posts:post_create')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая групппа',
            slug='test_slug',
            description='Тест описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='новый пост без указания группы',
            group=cls.group,
        )
        cls.GROUP_LIST_URL = reverse(
            'posts:group_posts', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            self.GROUP_LIST_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            CREATE_POST_URL: 'posts/create_post.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_for_anon(self):
        url = (
            INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE_URL,
            self.POST_DETAIL_URL,
        )
        for url in url:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_auth(self):
        response = self.authorized_client.get(CREATE_POST_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_anon_on_login(self):
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {
            CREATE_POST_URL: url1,
            self.POST_EDIT_URL: url2
        }
        for page, value in pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertRedirects(response, value)

    def test_post_edit_for_author(self):
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
