import json
from functools import partial

from project.tests.base import BaseTestCase
from project.api.models import User
from project import db

import datetime


def add_user(username, email, created_at=datetime.datetime.utcnow()):
    user = User(username=username, email=email, created_at=created_at)
    db.session.add(user)
    db.session.commit()
    return user


def extractor(x, field): return x[field]


data = partial(extractor, field='data')
username = partial(extractor, field='username')
email = partial(extractor, field='email')
status = partial(extractor, field='status')
first = partial(extractor, field=0)
last = partial(extractor, field=-1)
users = partial(extractor, field='users')
message = partial(extractor, field='message')


class TestUserService(BaseTestCase):

    def test_users(self):
        response = self.client.get('/ping')
        payload = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIn('pong!', message(payload))
        self.assertIn('success', status(payload))

    def test_add_user(self):
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    username='michael',
                    email='michael@realpython.com'
                )),
                content_type='application/json'
            )
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 201)
            self.assertIn('michael@realpython.com was added!', message(payload))
            self.assertIn('success', status(payload))

    def test_add_user_invalid_json(self):
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict()),
                content_type='application/json',
            )
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid payload', message(payload))
            self.assertIn('fail', status(payload))

    def test_add_user_invalid_json_keys(self):
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(email='michael@realpython.com')),
                content_type='application/json',
            )
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid payload.', message(payload))
            self.assertIn('fail', status(payload))

    def test_add_user_duplicate_user(self):
        with self.client:
            self.client.post(
                '/users',
                data=json.dumps(dict(
                    username='michael',
                    email='michael@realpython.com'
                )),
                content_type='application/json',
            )
            response=self.client.post(
                '/users',
                data=json.dumps(dict(
                    username='michael',
                    email='michael@realpython.com'
                )),
                content_type='application/json',
            )

            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Sorry. That email already exists.', message(payload))
            self.assertIn('fail', status(payload))

    def test_single_user(self):
        user = User(username='michael', email='michael@realpython.com')
        db.session.add(user)
        db.session.commit()
        with self.client:
            response = self.client.get(f'/users/{user.id}')
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertTrue('created_at' in data(payload))
            self.assertIn('michael', username(data(payload)))
            self.assertIn('michael@realpython.com', email(data(payload)))
            self.assertIn('success', status(payload))

    def test_single_user_no_id(self):
        with self.client:
            response = self.client.get('/users/blah')
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 404)
            self.assertIn('User does not exist', message(payload))
            self.assertIn('fail', status(payload))

    def test_single_user_incorrect_id(self):
        with self.client:
            response = self.client.get('users/999')
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 404)
            self.assertIn('User does not exist', message(payload))
            self.assertIn('fail', status(payload))

    def test_single_user(self):
        user = add_user('michael', 'michael@realpython.com')
        with self.client:
            response = self.client.get(f'/users/{user.id}')
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertTrue('created_at' in data(payload))
            self.assertIn('michael', username(data(payload)))
            self.assertIn('michael@realpython.com', email(data(payload)))

    def test_all_users(self):
        created = datetime.datetime.utcnow() + datetime.timedelta(-30)
        add_user('michael', 'michael@realpython.com', created)
        add_user('fletcher', 'fletcher@realpython.com')
        with self.client:
            response = self.client.get(f'/users')
            payload = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(users(data(payload))), 2)
            self.assertTrue('created_at' in first(users(data(payload))))
            self.assertTrue('created_at' in last(users(data(payload))))
            self.assertIn('michael', username(last(users(data(payload)))))
            self.assertIn('michael@realpython.com', email(last(users(data(payload)))))
            self.assertIn('fletcher', username(first(users(data(payload)))))
            self.assertIn('fletcher@realpython.com', email(first(users(data(payload)))))
            self.assertIn('success', status(payload))

