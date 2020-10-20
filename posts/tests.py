from django.test import Client, TestCase
from .models import User, Post, Group, Comment
from django.urls import reverse
from django.core.cache import cache


class TestStringMethods(TestCase):

    url = {
        'LOGIN': reverse('login'),
        'NEW_POST': reverse('new_post'),
        'URL': "/auth/login/?next=/new/",
    }

    def setUp(self):
        self.text = 'test_text'
        self.text_2 = 'test_2'
        self.anon_client = Client()
        self.client = Client()
        self.user = User.objects.create_user(username="sarah")
        self.group = Group.objects.create(title='test',
                                          slug='test', description='test')
        self.post = Post.objects.create(text=self.text,
                                        author=self.user, group=self.group)
        self.client.force_login(self.user)

    def test_reg_profile(self):
        response = self.client.get(reverse('profile',
                                           args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

    def func_post(self, template, text, args):
        response = self.client.post(reverse
                                    (template, args=args or None),
                                    {'text': text,
                                     'group': self.group.id}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_auth_post(self):
        self.func_post('new_post', self.text, None)
        self.assertEqual(Post.objects.count(), 2)

    def test_post_edit_equal(self):
        self.func_post('post_edit', self.text_2, args=[
            self.post.author,
            self.post.id],)

    def test_anon_post(self):
        response = self.anon_client.post(self.url['NEW_POST'],
                                         {'text': self.text_2}, follow=True)
        self.assertRedirects(response, self.url['URL'],
                             target_status_code=200)
        self.assertEqual(Post.objects.count(), 1)

    def func_post_and_edit(self, test):
        cache.clear()
        response = self.client.get("")
        self.assertContains(response, text=test, count=1)

        response = self.client.get(reverse('profile',
                                           args=[self.user.username]))
        self.assertContains(response, text=test, count=1)

        response = self.client.get(reverse("post",
                                           args=[self.post.author,
                                                 self.post.id]))
        self.assertContains(response, text=test, count=1)

        response = self.client.get(reverse('groups',
                                           args=[self.group.title]))
        self.assertContains(response, text=test, count=1)

    def test_post_place(self):

        self.func_post_and_edit(self.text)

    def test_post_edit(self):

        self.func_post('post_edit', self.text_2, args=[
            self.post.author,
            self.post.id],)
        self.func_post_and_edit(self.text_2)

    def test_404(self):

        response = self.client.get('random-page')
        self.assertEqual(response.status_code, 404)

    def test_images(self):

        with open('posts/test.jpg', 'rb') as img:
            post = self.client.post(reverse('post_edit',
                                            args=[self.post.author,
                                                  self.post.id]),
                                    {
                'text': self.text,
                'group': self.group.id,
                'image': img
            }, follow=True)

            cache.clear()
            response = self.client.get(reverse('groups',
                                               args=[self.group.title]))
            self.assertContains(response, '<img')

            response = self.client.get(
                reverse(
                    'post',
                    args=[
                        self.post.author,
                        self.post.id]))
            self.assertContains(response, '<img')

            response = self.client.get(reverse('profile',
                                               args=[self.post.author]))
            self.assertContains(response, '<img')

            response = self.client.get(reverse('index'))
            self.assertContains(response, '<img')

    def test_not_img(self):
        with open('posts/test.txt', 'rb') as img:
            post = self.client.post(reverse('post_edit',
                                            args=[self.post.author,
                                                  self.post.id]),
                                    {
                'text': self.text,
                'group': self.group.id,
                'image': img
            }, follow=True)
            self.assertEqual(post.status_code, 200)
            self.assertFormError(
                post,
                "form",
                "image",
                "Загрузите правильное изображение. Файл, "
                "который вы загрузили, поврежден или не является изображением.",)

            cache.clear()
            response = self.client.get(reverse('index'))

            print()
            self.assertNotContains(response, '<img')

    def test_cash(self):

        response = self.client.get(reverse('index'))
        post = self.client.post(self.url['NEW_POST'],
                                {'text': self.text_2}, follow=True)
        self.assertNotContains(response, self.text_2)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.text_2)

    def test_auth_follow(self):
        follower_user = User.objects.create_user(username="follower")
        not_follower = User.objects.create_user(username="not_follower")
        post = Post.objects.create(text=self.text_2,
                                   author=follower_user, group=self.group)

        response = self.client.post(
            reverse(
                'profile_follow',
                args=[
                    follower_user.username]),
            follow=True)
        response = self.client.get(
            reverse(
                "profile", args=[
                    follower_user.username]))
        self.assertEqual(response.context['follower'], 1)

        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.text_2)

        response = self.client.post(
            reverse(
                'profile_unfollow',
                args=[
                    follower_user.username]),
            follow=True)
        self.assertEqual(response.context['follower'], 0)

        self.client.logout()
        self.client.force_login(not_follower)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, self.text_2)

    def test_anon_comment(self):

        self.anon_client.post(reverse('add_comment',
                                      args=[
                                          self.post.author,
                                          self.post.id]),
                              {
            'text': self.text,
        },
            follow=True)
        self.assertEqual(Comment.objects.count(), 0)
        self.client.post(reverse('add_comment',
                                 args=[
                                     self.post.author,
                                     self.post.id]),
                         {
            'text': self.text,
        },
            follow=True)
        self.assertEqual(Comment.objects.count(), 1)
