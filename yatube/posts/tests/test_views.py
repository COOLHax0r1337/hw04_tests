from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Группа фэнов графа',
            slug='tolstoy',
            description='Инфа о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Война и мир - тупа топ',
            group=cls.group,
        )

    def setUp(self):
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
        for i in range(1, 18):
            new_post = Post(
                author=PostViewTests.user,
                text='Тестовый пост ' + str(i),
                group=PostViewTests.group
            )
            paginator_objects.append(new_post)
        Post.objects.bulk_create(paginator_objects)
        paginator_data = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:group_posts',
                kwargs={'slug': PostViewTests.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PostViewTests.user.username}
            )
        }
        for paginator_place, paginator_page in paginator_data.items():
            with self.subTest(paginator_place=paginator_place):
                response_page_1 = self.authorized_client.get(paginator_page)
                response_page_2 = self.authorized_client.get(
                    paginator_page + '?page=2'
                )
                self.assertEqual(len(
                    response_page_1.context['page_obj']),
                    10
                )
                self.assertEqual(len(
                    response_page_2.context['page_obj']),
                    8
                )

    def test_index_show_correct_context(self):
        response_index = self.authorized_client.get(reverse('posts:index'))
        page_index_context = response_index.context
        self.post_exist(page_index_context)

    def test_post_detail_show_correct_context(self):
        response_post_detail = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewTests.post.pk}
            )
        )
        page_post_detail_context = response_post_detail.context
        self.post_exist(page_post_detail_context)

    def test_group_page_show_correct_context(self):
        response_group = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostViewTests.group.slug}
            )
        )
        page_group_context = response_group.context
        task_group = response_group.context['group']
        self.post_exist(page_group_context)
        self.assertEqual(task_group, PostViewTests.group)

    def test_profile_show_correct_context(self):
        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        page_profile_context = response_profile.context
        task_profile = response_profile.context['author']
        self.post_exist(page_profile_context)
        self.assertEqual(task_profile, PostViewTests.user)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewTests.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
