import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Follow
from posts.forms import PostForm

User = get_user_model()

PAG_CNT = 13


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def check_context(self, response, is_post=False):
        if is_post:
            post = response.context['post']
        else:
            post = response.context['page_obj'][0]
        contex_page = {
            self.post.author: post.author,
            self.post.text: post.text,
            self.post.group.title: post.group.title,
            self.post.group.slug: post.group.slug,
            self.post.group.description: post.group.description,
            self.post.image.name: post.image.name
        }
        for expected, value in contex_page.items():
            with self.subTest():
                self.assertEqual(value, expected)

    def test_index_page_show_correct_context(self):
        """
        Проверяет совпадения индекса страницы с действительностью.
        """
        response = self.authorized_author.get(reverse('posts:index'))
        self.check_context(response=response)

    def test_group_list_page_show_correct_post(self):
        """
        Поверяет, не является ли пост другой группы
        выведеным на странице старой.
        """
        post = Post.objects.create(
            author=self.user,
            text='Тестовая запись 1',
            group=self.group,
        )
        if post.group:
            self.assertEqual(post.group, self.group)
        else:
            assert False (
                f'Пост {post} не имеет группы {self.group}'
            )

        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Тестовое описание',
        )
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(new_group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_group_list_page_show_correct_contex(self):
        """
        context для групп
        """
        response_group = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        group_object = response_group.context['group']
        self.assertEqual(group_object, self.group)
        self.check_context(response=response_group)

    def test_profile_page_show_correct_context(self):
        """
        context для profile
        """
        response = self.authorized_author.get(
            reverse('posts:profile', args=(self.user.username,))
        )
        author = response.context['author']
        self.assertEqual(author, self.user)
        self.check_context(response=response)

    def test_post_detail_page_show_correct_context(self):
        """
        Проверяет правильность значений объекта сущности поста
        на основе записи объекта сущности из БД на странице детального
        просмотра поста.
        """
        response = self.authorized_author.get(
            reverse('posts:post_detail', args=(self.post.id,)))
        self.check_context(response=response, is_post=True)

    def test_post_edit_and_create_page_show_correct_context(self):
        """
        Проверят контекст для edit и сreate
        """
        test_case = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for name, arg in test_case:
            with self.subTest(name=name):
                response = self.authorized_author.get(reverse(name, args=arg))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_cache_index_page(self):
        """Записи Index хранятся в кэше и обновлялся раз в 20 секунд"""
        Post.objects.all().delete()
        post_cach = Post.objects.create(
            text='Тестовый текст для кэша',
            author=self.user,
            group=self.group,
        )
        response_1 = self.authorized_author.get(reverse('posts:index'))
        post_cach.delete()
        response_2 = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_author.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        # Создаем 13 постов
        cls.post = [
            Post.objects.create(
                author=cls.user,
                text=f'Тестовая запись {page}',
                group=cls.group,
            )
            for page in range(PAG_CNT)
        ]

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.follower = User.objects.create(
            username='follower'
        )
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.follower_client.get(reverse('posts:profile_follow',
                                 args=(self.user.username,)))

    def test_page_contains_paginator_records(self):
        names = (
            ('posts:index', None,),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:follow_index', None,),
        )
        pages = (
            ('?page=1', settings.COUNT_STR,),
            ('?page=2', PAG_CNT - settings.COUNT_STR,),
        )
        for reverse_name, args in names:
            with self.subTest(args=args):
                for page, count in pages:
                    with self.subTest(page=page, count=count):
                        if reverse_name == 'posts:follow_index':
                            response = self.follower_client.get(
                                reverse(reverse_name, args=args) + page)
                            self.assertEqual(len(
                                response.context['page_obj']), count)
                        else:
                            response = self.client.get(
                                reverse(reverse_name, args=args) + page)
                            self.assertEqual(len(
                                response.context['page_obj']), count)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='posts_author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def setUp(self):
        # Клиент подписчика
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        # Клиент автора
        self.author_client = Client()
        self.author_client.force_login(self.author)
        # Клиент не подписчика
        self.user = User.objects.create(
            username='user',
        )
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_authorized_user_follow(self):
        # Авторизованный пользователь может подписаться
        follows_count = Follow.objects.count()
        self.follower_client.get(reverse('posts:profile_follow',
                                 args=(self.author.username,)))
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.user, self.follower)
        self.assertEqual(follow.author, self.author)

    def test_authorized_user_unfollow(self):
        # Авторизованный может отписаться
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        follows_count = Follow.objects.count()
        Follow.objects.all().delete()
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_post_include_in_following(self):
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        response = self.follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertEqual(response.context['page_obj'][0], self.post)

        response = self.user_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertEqual(len(response.context['page_obj']), 0)
