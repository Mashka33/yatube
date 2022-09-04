from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост - 1',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.authclient = User.objects.create_user(username='client')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authclient)
        self.url_status = (
            ('posts:index', None,),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:post_detail', (self.post.pk,)),
            ('posts:post_create', None,),
            ('posts:post_edit', (self.post.pk,)),
            ('posts:add_comment', (self.post.pk,)),
            ('posts:follow_index', None,),
            ('posts:profile_follow', (self.user.username,)),
            ('posts:profile_unfollow', (self.user.username,)),
        )

    # Проверяем неавторизованного пользователя

    def test_guest_client_status(self):
        for reverse_name, args, in self.url_status:
            with self.subTest(args=args):
                if reverse_name in ['posts:post_create', 'posts:post_edit',
                    'posts:add_comment', 'posts:follow_index',
                    'posts:profile_follow', 'posts:profile_unfollow']:
                    response = self.client.get(
                        reverse(reverse_name, args=args))
                    name = reverse(reverse_name, args=args)
                    auth_login = reverse('users:login')
                    self.assertRedirects(
                        response,
                        f'{auth_login}?next={name}')
                else:
                    response = self.client.get(
                        reverse(reverse_name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK, f'Провал status_code для {reverse_name}')

    def test_authorized_client_status(self):
        # Проверяем статус авторизованного пользователя
        for reverse_name, args, in self.url_status:
            with self.subTest(args=args):
                if reverse_name in ['posts:post_edit', 'posts:add_comment']:
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args))
                    self.assertRedirects(
                        response, reverse('posts:post_detail', args=args))
                elif reverse_name in ['posts:profile_follow', 'posts:profile_unfollow']:
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args))
                    self.assertRedirects(
                        response, reverse('posts:profile', args=args))
                else:
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK, f'Провал status_code для {reverse_name}')

    def test_authorized_author_status(self):
        # Проверяем статус автора
        for reverse_name, args, in self.url_status:
            with self.subTest(args=args):
                if reverse_name == 'posts:profile_follow':
                    response = self.authorized_author.get(
                    reverse(reverse_name, args=args))
                    self.assertRedirects(
                        response, reverse('posts:profile', args=args))
                elif reverse_name == 'posts:profile_unfollow':
                    response = self.authorized_author.get(
                        reverse(reverse_name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                elif reverse_name == 'posts:add_comment':
                    response = self.authorized_author.get(
                        reverse(reverse_name, args=args))
                    self.assertRedirects(
                        response, reverse('posts:post_detail', args=args))
                else:
                    response = self.authorized_author.get(
                        reverse(reverse_name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK, f'Провал status_code для {reverse_name}')

    def test_urls_correct_template(self):
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        templates_page_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.pk,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.pk,), 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html')
        )
        for reverse_name, args, template, in templates_page_names:
            with self.subTest(args=args):
                response = self.authorized_author.get(
                    reverse(reverse_name, args=args))
                self.assertTemplateUsed(response, template)

    def test_reverse_name_url(self):
        url_page_names = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
             f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.pk,),
             f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'),
            ('posts:add_comment', (self.post.pk,),
             f'/posts/{self.post.pk}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow', (self.user.username,),
             f'/profile/{self.user.username}/follow/'),
            ('posts:profile_unfollow', (self.user.username,),
             f'/profile/{self.user.username}/unfollow/'),
        )
        for reverse_name, args, url in url_page_names:
            with self.subTest(args=args):
                self.assertEqual(reverse(reverse_name, args=args), url)

    def test_404(self):
        """Cервер возвращает код 404, если страница не найдена."""
        response = self.client.get('/notfound/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
