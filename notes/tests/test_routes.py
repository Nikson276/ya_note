from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):
    ''' Проверяем следующие пункты:
    - Главная страница доступна анонимному пользователю.
    - Страница списка своих заметок и детального просмотра каждой доступна авторитизованому пользователю.
    - Страницы удаления и редактирования заметки доступны автору заметки.
    - При попытке перейти на страницу редактирования или удаления заметки анонимный пользователь перенаправляется на страницу авторизации.
    - Авторизованный пользователь не может зайти на страницы редактирования или удаления чужих заметок (возвращается ошибка 404).
    - Страницы регистрации пользователей, входа в учётную запись и выхода из неё доступны анонимным пользователям.
    '''
    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Гордон Фримен')
        cls.reader = User.objects.create(username='G Man')
        # От имени одного пользователя создаём еще одну заметку:
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        ) 
    
    def test_home_page(self):
        '''Тест главное страницы анонимным пользователем'''
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
    def test_note_page_list(self):
        '''Проверяем доступ автора к своим записям детально и списком'''
        urls = (
            ('notes:detail', {'slug': self.note.slug}),
            ('notes:list', None)
        )
        self.client.force_login(self.author)
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
    
    def test_page_availability(self):
        '''Проверка доступа анонимн юзера на все базовые страницы'''
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),            
        )
        for request in urls:
            name, kwargs = request
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:edit', 'notes:delete'):  
                with self.subTest(user=user, name=name):        
                    url = reverse(name, kwargs={'slug': self.note.slug})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
    
    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')

        for name in ('notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, kwargs={'slug': self.note.slug})
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
