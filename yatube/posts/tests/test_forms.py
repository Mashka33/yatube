import shutil
import tempfile

from http import HTTPStatus
from tkinter import image_names

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm
from posts.models import Post, Group, User, Comment


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image_name= 'small.gif'
        self.uploaded = SimpleUploadedFile(
            name=image_name,
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_authorized_client_create_new_post(self):
        # Авторизованный может создать пост
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image.name, 'posts/small.gif')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                author=self.user,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_autorized_author_edit_post(self):
        posts_count_before = Post.objects.count()
        group_2 = Group.objects.create(
            title='Группа2',
            slug='group2-slug',
            description='Описание группы2'
        )
        form_data = {
            'text': 'Новый текст поста',
            'group': group_2.id,
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit',
                    args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        old_group_response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        paginator_number_old_response = old_group_response.context[
            'page_obj'].paginator.count
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=(self.post.pk,)))
        post = Post.objects.first()
        self.assertEqual(post.text, 'Новый текст поста')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, group_2)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст поста',
                author=self.user,
                group=group_2,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(old_group_response.status_code, HTTPStatus.OK)
        self.assertEqual(paginator_number_old_response, 0)
        self.assertEqual(posts_count_before, Post.objects.count())

    def test_guest_client_create_post(self):
        # Анонимный пользователь не может создать пост
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('users:login')
        name = reverse('posts:post_create')
        self.assertRedirects(response,
                             f'{login}?next={name}')
        self.assertEqual(Post.objects.count(), posts_count)


class CommentPostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='post_author',
        )
        cls.post = Post.objects.create(
            text='Рандомный текст',
            author=CommentPostCreateTest.user,
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def test_authorized_client_add_comment(self):
        # Авторизованный пользователь может добавить комментарий
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment',
                    args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=(self.post.pk,)))
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Текст комментария')
        self.assertEqual(comment.author, self.user)

    def test_guest_client_add_comment(self):
        # Неавторизованный не может оставить комментарий
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.client.post(
            reverse('posts:add_comment',
                    args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('users:login')
        post = reverse('posts:add_comment',
                       args=(self.post.pk,))
        self.assertRedirects(response,
                             f'{login}?next={post}')
        self.assertEqual(self.post.comments.count(), comment_count)
