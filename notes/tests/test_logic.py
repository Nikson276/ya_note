from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()

class TestNoteCreation(TestCase):
    ''' Проверяем следующие пункты:
    - Анонимный пользователь не может отправить заметку.
    - Авторизованный пользователь может отправить заметку.
    '''
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.author = User.objects.create(username='создатель')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': 'note_1'
            }

    def test_anonymous_user_cant_create_note(self):  
        self.client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.author)


class TestNoteEditDeleteSlug(TestCase):
    ''' Проверяем следующие пункты: 
    - Авторизованный пользователь может редактировать или удалять свои заметки.
    - Авторизованный пользователь не может просматривать,  редактировать или удалять чужие заметки.
    - Не уникальное значение slug не возможно.
    '''
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'note_1'
    NEW_NOTE_TEXT = 'Измененный текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.success_url = reverse('notes:success')
        cls.author1 = User.objects.create(username='Пользователь 1')
        cls.author2 = User.objects.create(username='Пользователь 2')
        cls.auth_client1 = Client()
        cls.auth_client2 = Client()
        cls.auth_client1.force_login(cls.author1)
        cls.auth_client2.force_login(cls.author2)
        cls.create_form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG
            }
        cls.note = Note.objects.create(
            **cls.create_form_data,
            author=cls.author1
            )
        
        cls.upd_form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.SLUG
            }    
        cls.edit_url = reverse('notes:edit', kwargs={'slug': cls.SLUG})
        cls.delete_url = reverse('notes:delete', kwargs={'slug': cls.SLUG})

    def test_auth_edit_notes(self):
        response = self.auth_client1.post(
            self.edit_url,
            data=self.upd_form_data
            )
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_auth_delete_notes(self):
        response = self.auth_client1.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)          

    def test_user_cant_edit_notes_of_another_user(self):
        response = self.auth_client2.post(
            self.edit_url,
            data=self.upd_form_data
            )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_user_cant_delete_notes_of_another_user(self):
        response = self.auth_client2.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_user_cant_see_notes_of_another_user(self):
        response = self.auth_client2.get(
            reverse('notes:detail', kwargs={'slug': self.SLUG})
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_ununique_slug_impossible(self):
        response = self.auth_client2.post(
            reverse('notes:add'),
            data=self.upd_form_data
            )
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.SLUG + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_no_slug_auto_create(self):
        self.create_form_data.pop('slug')
        expected_slug = slugify(self.create_form_data['title'])
        
        response = self.auth_client2.post(
            reverse('notes:add'),
            data=self.create_form_data
            )
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get(slug=expected_slug)
        self.assertIsInstance(note, Note)
