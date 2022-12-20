from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.conf import settings

from ..models import Post, Group

from http import HTTPStatus

User = get_user_model()

RANGE_POSTS = 13
PAGINATE_PAGE_SECOND = 3
POST_LIMIT_SECOND = 8


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа фэнов графа',
            slug='slug',
            description='Инфа о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Война и мир - тупа топ',
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
        cls.INDEX_URL = reverse('posts:index')
        cls.CREATE_POST_URL = reverse('posts:post_create')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)

    def post_exist(self, page_context):
        if 'page_obj' in page_context:
            post = page_context['page_obj'][0]
        else:
            post = page_context['post']
        task_author = post.author
        task_text = post.text
        task_group = post.group
        self.assertEqual(
            task_author,
            PostViewTests.post.author
        )
        self.assertEqual(
            task_text,
            PostViewTests.post.text
        )
        self.assertEqual(
            task_group,
            PostViewTests.post.group
        )

    def test_paginator_correct_context(self):
        paginator_objects = []
        for post_num in range(1, 18):
            new_post = Post(
                author=PostViewTests.user,
                text='Тестовый пост ' + str(post_num),
                group=PostViewTests.group
            )
            paginator_objects.append(new_post)
        Post.objects.bulk_create(paginator_objects)
        paginator_data = (
            self.INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE_URL,
        )
        for paginator_page in paginator_data:
            page_numbers = {
                paginator_page: settings.POST_LIMIT,
                ((paginator_page) + '?page=2'): POST_LIMIT_SECOND,
            }
            for page_number, count_page in page_numbers.items():
                with self.subTest(page_number=page_number):
                    response = self.client.get(page_number)
                    self.assertEqual(
                        len(response.context['page_obj']), count_page
                    )

    def test_index_show_correct_context(self):
        response_index = self.authorized_client.get(self.INDEX_URL)
        page_index_context = response_index.context
        self.post_exist(page_index_context)

    def test_post_detail_show_correct_context(self):
        response_post_detail = self.authorized_client.get(self.POST_DETAIL_URL)
        page_post_detail_context = response_post_detail.context
        self.post_exist(page_post_detail_context)

    def test_group_page_show_correct_context(self):
        response_group = self.authorized_client.get(self.GROUP_LIST_URL)
        page_group_context = response_group.context
        task_group = response_group.context['group']
        self.post_exist(page_group_context)
        self.assertEqual(task_group, PostViewTests.group)

    def test_profile_show_correct_context(self):
        response_profile = self.authorized_client.get(self.PROFILE_URL)
        page_profile_context = response_profile.context
        task_profile = response_profile.context['author']
        self.post_exist(page_profile_context)
        self.assertEqual(task_profile, PostViewTests.user)

    def test_views_create_post_and_post_edit_pages_show_correct_context(self):
        post_context = (
            self.CREATE_POST_URL,
            self.POST_EDIT_URL
        )
        for context in post_context:
            response = self.authorized_client.get(context)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField}
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_views_post_added_correctly(self):
        post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group,
        )
        mapping = (
            self.authorized_client.get(self.INDEX_URL),
            self.authorized_client.get(self.GROUP_LIST_URL),
            self.authorized_client.get(self.PROFILE_URL),
        )
        for response in mapping:
            object = response.context['page_obj']
            self.assertIn(post, object)

    def test_post_edit_guest(self):
        form_data = {
            'text': 'Текст в форме',
            'group': self.group.id
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')
