from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from notes.models import Note
from datetime import datetime, timedelta 


User = get_user_model()


class TestListPage(TestCase):
    
    LIST_URL = reverse('notes:list')
    NOTES_QTY = 15
    
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='создатель')
        cls.viewer = User.objects.create(username='смотритель')
        ''' Создаем сразу пачку записей через bulk_create()'''
        all_notes = [
            Note(title=f'Заметка {index}',
                 text='Просто текст.',
                 slug=f'note_{index}',
                 author=cls.author)
            for index in range(cls.NOTES_QTY)
        ]
        Note.objects.bulk_create(all_notes)
    
    def test_notes_list(self):
        ''' Проверяем следующие пункты:
        - Кол-во заметок на странице со списком заметок равно кол-во заметок в БД для юзера
        - Отдельная заметка передаётся на страницу со списком заметок в списке object_list в словаре context;
        '''        
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, self.NOTES_QTY)
        
        note = Note.objects.get(slug=f'note_{0}')
        self.assertIn(note, object_list)

    def test_list_isolation(self):
        '''Проверяем следующие пункты:
        - В список заметок одного пользователя не попадают заметки другого пользователя;
        '''
        self.client.force_login(self.viewer)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, 0)        


class TestNoteCreate(TestCase):
    ''' Проверяем следующие пункты:
    - Анонимному пользователю недоступна форма для отправки заметки
    - Авторизованному пользователю доступна форма создания заметки
    '''
    
    @classmethod
    def setUpTestData(cls):
        cls.add_url = reverse('notes:add')
        cls.control_url = reverse('users:login')
        cls.author = User.objects.create(username='создатель')

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.add_url)
        self.assertNotIn(response.url, self.control_url)
        
    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.add_url) 
        self.assertIn('form', response.context)
