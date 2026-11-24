from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.prayer.models import Prayer

U = get_user_model()

def mk(email):
    return U.objects.create_user(email=email, password='pw-12345')

class OthersPrayers(TestCase):
    def setUp(self):
        self.u = mk('a@x.com'); self.v = mk('b@x.com')
        self.c = APIClient(); self.c.force_authenticate(self.u)
        self.c.post('/api/focus/website-key/', {'key': 'secret1'}, format='json')

    def unlock(self, c=None, key='secret1'):
        c = c or self.c
        r = c.post('/api/focus/website-key/verify/', {'key': key}, format='json')
        return r

    def test_full_flow(self):
        # own prayer: no key needed
        r = self.c.post('/api/prayer/', {'title': 'Mine', 'content': 'x'}, format='json')
        self.assertEqual(r.status_code, 201); self.assertEqual(r.data['prayer_for'], 'self')
        # other prayer without key -> 403 prayers_locked
        body = {'title': 'Healing', 'content': 'for her', 'prayer_for': 'other', 'person_name': 'Mary'}
        r = self.c.post('/api/prayer/', body, format='json')
        self.assertEqual(r.status_code, 403); self.assertTrue(r.data['errors']['prayers_locked'])
        # wrong key: no token
        r = self.unlock(key='nope'); self.assertFalse(r.data['ok']); self.assertNotIn('unlock_token', r.data)
        # right key -> token
        r = self.unlock(); self.assertTrue(r.data['ok']); tok = r.data['unlock_token']
        H = {'HTTP_X_PRAYER_UNLOCK': tok}
        # name required
        r = self.c.post('/api/prayer/', {**body, 'person_name': ' '}, format='json', **H)
        self.assertEqual(r.status_code, 400); self.assertIn('person_name', r.data['errors'])
        r = self.c.post('/api/prayer/', body, format='json', **H)
        self.assertEqual(r.status_code, 201, r.data); pid = r.data['id']
        self.assertEqual(r.data['person_name'], 'Mary')
        # default list = own only, never others
        r = self.c.get('/api/prayer/', **H); self.assertEqual([p['title'] for p in r.data['results']], ['Mine'])
        # others list: locked without token, ok with
        r = self.c.get('/api/prayer/?prayer_for=other'); self.assertEqual(r.status_code, 403)
        r = self.c.get('/api/prayer/?prayer_for=other', **H); self.assertEqual([p['title'] for p in r.data['results']], ['Healing'])
        # detail: locked -> 403 (not leaked), unlocked -> 200
        self.assertEqual(self.c.get(f'/api/prayer/{pid}/').status_code, 403)
        self.assertEqual(self.c.get(f'/api/prayer/{pid}/', **H).status_code, 200)
        # mark answered keeps type; reopen restores
        r = self.c.post(f'/api/prayer/{pid}/mark_answered/', {'note': 'healed'}, format='json', **H)
        self.assertEqual(r.data['data']['status'], 'answered'); self.assertEqual(r.data['data']['prayer_type'], 'request')
        r = self.c.get('/api/prayer/?prayer_for=other&status=answered', **H); self.assertEqual(len(r.data['results']), 1)
        r = self.c.post(f'/api/prayer/{pid}/reopen/', {}, format='json', **H); self.assertEqual(r.data['data']['status'], 'active')
        # answering own prayer still becomes thanksgiving
        mine = Prayer.objects.get(title='Mine')
        r = self.c.post(f'/api/prayer/{mine.id}/mark_answered/', {}, format='json'); self.assertEqual(r.data['data']['prayer_type'], 'thanksgiving')
        # stats count own only
        r = self.c.get('/api/prayer/stats/'); self.assertEqual(r.data['data']['total'], 1)
        # global search never returns others
        r = self.c.get('/api/search/?q=Healing', **H); self.assertEqual(r.data.get('data', r.data).get('prayers', r.data.get('prayers')), [] )
        # logging a prayer for them: needs key; logs hidden while locked
        self.assertEqual(self.c.post(f'/api/prayer/{pid}/log_prayer/', {}, format='json').status_code, 403)
        self.assertEqual(self.c.post(f'/api/prayer/{pid}/log_prayer/', {}, format='json', **H).status_code, 200)
        r = self.c.get('/api/prayer/logs/'); self.assertEqual(len(r.data['results']), 0)
        r = self.c.get('/api/prayer/logs/', **H); self.assertEqual(len(r.data['results']), 1)
        # direct log create against others' prayer without key
        self.assertEqual(self.c.post('/api/prayer/logs/', {'prayer': pid}, format='json').status_code, 403)
        # making own prayer "other" needs key
        r = self.c.patch(f'/api/prayer/{mine.id}/', {'prayer_for': 'other', 'person_name': 'Z'}, format='json'); self.assertEqual(r.status_code, 403)

    def test_token_is_per_user_and_garbage_rejected(self):
        tok = self.unlock().data['unlock_token']
        d = APIClient(); d.force_authenticate(self.v)
        r = d.get('/api/prayer/?prayer_for=other', HTTP_X_PRAYER_UNLOCK=tok); self.assertEqual(r.status_code, 403)  # someone else's token
        r = self.c.get('/api/prayer/?prayer_for=other', HTTP_X_PRAYER_UNLOCK='garbage'); self.assertEqual(r.status_code, 403)
        # user B cannot log against A's prayer
        p = Prayer.objects.create(user=self.u, title='t', content='c')
        self.assertEqual(d.post('/api/prayer/logs/', {'prayer': p.id}, format='json').status_code, 403)
