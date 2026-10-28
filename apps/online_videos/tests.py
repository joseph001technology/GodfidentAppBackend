"""API tests for Online Videos.

Run:  python manage.py test apps.online_videos
"""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from . import services
from .models import OnlineVideo, OnlineVideoCollection

User = get_user_model()
VIDEOS = '/api/online-videos/videos/'
COLLS = '/api/online-videos/collections/'

YT = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'


def make_user(email):
    return User.objects.create_user(email=email, password='pass12345')


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class LinkHelpersTests(TestCase):
    def test_platform_is_detected_from_the_address(self):
        d = services.detect_platform
        self.assertEqual(d('https://www.youtube.com/watch?v=x'), 'youtube')
        self.assertEqual(d('https://youtu.be/abc'), 'youtube')
        self.assertEqual(d('https://m.facebook.com/watch/?v=1'), 'facebook')
        self.assertEqual(d('https://www.instagram.com/reel/AbC/'), 'instagram')
        self.assertEqual(d('https://vm.tiktok.com/ZM1/'), 'tiktok')
        self.assertEqual(d('https://example.com/v'), 'other')
        # a look-alike host must not be treated as the real platform
        self.assertEqual(d('https://notyoutube.com/x'), 'other')
        self.assertEqual(d('https://youtube.com.evil.io/x'), 'other')

    def test_bad_links_are_rejected(self):
        from rest_framework.exceptions import ValidationError
        for bad in ['', 'javascript:alert(1)', 'ftp://x.com/a', 'https://', 'not a link',
                    'https://user:pw@example.com/a', 'https://a.com/' + 'x' * 2100]:
            with self.assertRaises(ValidationError, msg=bad):
                services.clean_url(bad)

    def test_client_key_is_only_accepted_when_it_fits_the_platform(self):
        k = services.make_dedupe_key
        self.assertEqual(k(YT, 'youtube', 'youtube:dQw4w9WgXcQ'), 'youtube:dQw4w9WgXcQ')
        # key claims another platform -> replaced by one made from the address
        self.assertTrue(k(YT, 'youtube', 'tiktok:123').startswith('url:'))
        self.assertTrue(k(YT, 'youtube', 'garbage key with spaces').startswith('url:'))


class AuthTests(TestCase):
    def test_every_endpoint_needs_sign_in(self):
        c = APIClient()
        self.assertEqual(c.get(VIDEOS).status_code, 401)
        self.assertEqual(c.post(VIDEOS, {'url': YT}, format='json').status_code, 401)
        self.assertEqual(c.get(COLLS).status_code, 401)
        self.assertEqual(c.delete(f'{VIDEOS}{uuid.uuid4()}/').status_code, 401)


class VideoApiTests(TestCase):
    def setUp(self):
        self.user = make_user('a@example.com')
        self.other = make_user('b@example.com')
        self.c = client_for(self.user)

    def save(self, url=YT, **extra):
        return self.c.post(VIDEOS, {'url': url, **extra}, format='json')

    def test_save_and_it_persists_in_the_database(self):
        r = self.save(dedupe_key='youtube:dQw4w9WgXcQ')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertFalse(r.data['duplicate'])
        self.assertEqual(r.data['platform'], 'youtube')
        row = OnlineVideo.objects.get(pk=r.data['id'])
        self.assertEqual(row.user, self.user)
        self.assertEqual(row.url, YT)
        self.assertEqual(row.dedupe_key, 'youtube:dQw4w9WgXcQ')

    def test_library_is_the_same_after_signing_in_again(self):
        # "log out and back in", "reinstall" and "another phone" are all just a new client for the same account
        self.save()
        fresh = client_for(User.objects.get(pk=self.user.pk))
        r = fresh.get(VIDEOS)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['url'], YT)

    def test_duplicate_is_reported_not_created(self):
        a = self.save(dedupe_key='youtube:dQw4w9WgXcQ')
        b = self.save('https://youtu.be/dQw4w9WgXcQ?si=zzz', dedupe_key='youtube:dQw4w9WgXcQ')
        self.assertEqual(b.status_code, 200)
        self.assertTrue(b.data['duplicate'])
        self.assertEqual(a.data['id'], b.data['id'])
        self.assertEqual(OnlineVideo.objects.filter(user=self.user).count(), 1)

    def test_same_video_can_be_saved_by_two_users(self):
        self.save(dedupe_key='youtube:dQw4w9WgXcQ')
        r = client_for(self.other).post(VIDEOS, {'url': YT, 'dedupe_key': 'youtube:dQw4w9WgXcQ'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(OnlineVideo.objects.count(), 2)

    def test_retry_with_the_same_id_does_not_create_a_second_row(self):
        vid = str(uuid.uuid4())
        a = self.save(id=vid)
        b = self.save(id=vid)
        self.assertEqual(a.data['id'], vid)
        self.assertEqual(b.data['id'], vid)
        self.assertEqual(OnlineVideo.objects.count(), 1)

    def test_an_id_owned_by_someone_else_is_not_reused_or_revealed(self):
        mine = self.save().data['id']
        r = client_for(self.other).post(VIDEOS, {'url': 'https://vimeo.com/123', 'id': mine}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertNotEqual(r.data['id'], mine)
        self.assertEqual(OnlineVideo.objects.get(pk=mine).user, self.user)

    def test_invalid_links_are_rejected_with_400(self):
        for bad in ['', 'hello', 'javascript:alert(1)']:
            self.assertEqual(self.save(bad).status_code, 400, bad)
        self.assertEqual(OnlineVideo.objects.count(), 0)

    def test_unknown_platform_is_saved_as_other(self):
        r = self.save('https://example.com/watch/42?utm_source=x')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['platform'], 'other')

    def test_users_cannot_see_or_change_each_others_videos(self):
        vid = self.save().data['id']
        o = client_for(self.other)
        self.assertEqual(o.get(VIDEOS).data['count'], 0)
        self.assertEqual(o.get(f'{VIDEOS}{vid}/').status_code, 404)
        self.assertEqual(o.patch(f'{VIDEOS}{vid}/', {'custom_title': 'x'}, format='json').status_code, 404)
        self.assertEqual(o.delete(f'{VIDEOS}{vid}/').status_code, 404)
        row = OnlineVideo.objects.get(pk=vid)
        self.assertEqual(row.custom_title, '')

    def test_cannot_file_a_video_in_someone_elses_collection(self):
        theirs = OnlineVideoCollection.objects.create(user=self.other, name='Theirs')
        r = self.save(collection=str(theirs.id))
        self.assertEqual(r.status_code, 400)
        vid = self.save().data['id']
        r = self.c.patch(f'{VIDEOS}{vid}/', {'collection': str(theirs.id)}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIsNone(OnlineVideo.objects.get(pk=vid).collection)

    def test_delete_removes_only_that_row(self):
        a = self.save().data['id']
        self.save('https://vimeo.com/55')
        self.assertEqual(self.c.delete(f'{VIDEOS}{a}/').status_code, 204)
        self.assertEqual(OnlineVideo.objects.filter(user=self.user).count(), 1)
        self.assertEqual(self.c.get(f'{VIDEOS}{a}/').status_code, 404)

    def test_rename_and_move(self):
        vid = self.save().data['id']
        coll = self.c.post(COLLS, {'name': 'Sermons'}, format='json').data['id']
        r = self.c.patch(f'{VIDEOS}{vid}/', {'custom_title': '  My title  ', 'collection': coll}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['custom_title'], 'My title')
        self.assertEqual(r.data['collection'], uuid.UUID(coll))
        r = self.c.patch(f'{VIDEOS}{vid}/', {'collection': None}, format='json')
        self.assertIsNone(r.data['collection'])
        self.assertEqual(r.data['custom_title'], 'My title')  # untouched field stays

    def test_pagination_pages_are_complete_and_newest_first(self):
        for i in range(30):
            self.save(f'https://example.com/v/{i}')
        p1 = self.c.get(VIDEOS, {'limit': 12, 'offset': 0}).data
        p2 = self.c.get(VIDEOS, {'limit': 12, 'offset': 12}).data
        p3 = self.c.get(VIDEOS, {'limit': 12, 'offset': 24}).data
        self.assertEqual((p1['count'], len(p1['results']), len(p2['results']), len(p3['results'])), (30, 12, 12, 6))
        self.assertIsNotNone(p1['next'])
        self.assertIsNone(p3['next'])
        ids = [x['id'] for p in (p1, p2, p3) for x in p['results']]
        self.assertEqual(len(set(ids)), 30)  # no repeats, no gaps
        urls = [x['url'] for x in p1['results']]
        self.assertEqual(urls[0], 'https://example.com/v/29')  # newest first

    def test_page_size_is_capped_and_defaults(self):
        for i in range(3):
            self.save(f'https://example.com/v/{i}')
        self.assertEqual(len(self.c.get(VIDEOS).data['results']), 3)
        r = self.c.get(VIDEOS, {'limit': 100000}).data
        self.assertLessEqual(len(r['results']), services.MAX_VIDEOS_PER_USER)
        from .views import VideoPagination
        self.assertEqual(VideoPagination.max_limit, 100)

    def test_collection_filter(self):
        coll = self.c.post(COLLS, {'name': 'Music'}, format='json').data['id']
        self.save('https://example.com/a', collection=coll)
        self.save('https://example.com/b')
        self.assertEqual(self.c.get(VIDEOS, {'collection': coll}).data['count'], 1)
        self.assertEqual(self.c.get(VIDEOS, {'collection': 'none'}).data['count'], 1)
        self.assertEqual(self.c.get(VIDEOS, {'collection': 'nonsense'}).status_code, 400)

    def test_listing_uses_a_constant_number_of_queries(self):
        for i in range(20):
            self.save(f'https://example.com/v/{i}')
        with self.assertNumQueries(2):  # count + page (the user is pre-authenticated)
            self.c.get(VIDEOS, {'limit': 20})

    def test_library_size_limit(self):
        old = services.MAX_VIDEOS_PER_USER
        services.MAX_VIDEOS_PER_USER = 2
        try:
            self.save('https://example.com/1')
            self.save('https://example.com/2')
            self.assertEqual(self.save('https://example.com/3').status_code, 400)
            # a duplicate of an existing link is still answered normally when full
            self.assertEqual(self.save('https://example.com/1').status_code, 200)
        finally:
            services.MAX_VIDEOS_PER_USER = old


class CollectionApiTests(TestCase):
    def setUp(self):
        self.user = make_user('a@example.com')
        self.other = make_user('b@example.com')
        self.c = client_for(self.user)

    def test_create_list_counts(self):
        a = self.c.post(COLLS, {'name': 'Sermons'}, format='json')
        self.assertEqual(a.status_code, 201)
        self.c.post(VIDEOS, {'url': YT, 'collection': a.data['id']}, format='json')
        self.c.post(VIDEOS, {'url': 'https://vimeo.com/9'}, format='json')
        r = self.c.get(COLLS).data
        self.assertEqual(r['results'][0]['name'], 'Sermons')
        self.assertEqual(r['results'][0]['video_count'], 1)
        self.assertEqual((r['total_videos'], r['unsorted_videos']), (2, 1))

    def test_same_name_in_any_case_returns_the_existing_collection(self):
        a = self.c.post(COLLS, {'name': 'Sermons'}, format='json')
        b = self.c.post(COLLS, {'name': '  sermons '}, format='json')
        self.assertEqual(b.status_code, 200)
        self.assertEqual(a.data['id'], b.data['id'])
        self.assertEqual(OnlineVideoCollection.objects.filter(user=self.user).count(), 1)

    def test_two_users_may_use_the_same_name(self):
        self.c.post(COLLS, {'name': 'Music'}, format='json')
        r = client_for(self.other).post(COLLS, {'name': 'Music'}, format='json')
        self.assertEqual(r.status_code, 201)

    def test_blank_name_rejected(self):
        self.assertEqual(self.c.post(COLLS, {'name': '   '}, format='json').status_code, 400)
        self.assertEqual(self.c.post(COLLS, {}, format='json').status_code, 400)

    def test_rename_and_conflict(self):
        a = self.c.post(COLLS, {'name': 'One'}, format='json').data['id']
        self.c.post(COLLS, {'name': 'Two'}, format='json')
        self.assertEqual(self.c.patch(f'{COLLS}{a}/', {'name': 'Uno'}, format='json').data['name'], 'Uno')
        self.assertEqual(self.c.patch(f'{COLLS}{a}/', {'name': 'TWO'}, format='json').status_code, 409)
        self.assertEqual(self.c.patch(f'{COLLS}{a}/', {'name': ''}, format='json').status_code, 400)
        # renaming to its own name in another case is allowed
        self.assertEqual(self.c.patch(f'{COLLS}{a}/', {'name': 'UNO'}, format='json').status_code, 200)

    def test_deleting_a_collection_keeps_its_videos(self):
        a = self.c.post(COLLS, {'name': 'Gone'}, format='json').data['id']
        v = self.c.post(VIDEOS, {'url': YT, 'collection': a}, format='json').data['id']
        self.assertEqual(self.c.delete(f'{COLLS}{a}/').status_code, 204)
        row = OnlineVideo.objects.get(pk=v)
        self.assertIsNone(row.collection)

    def test_collections_are_private(self):
        a = self.c.post(COLLS, {'name': 'Mine'}, format='json').data['id']
        o = client_for(self.other)
        self.assertEqual(o.get(COLLS).data['results'], [])
        self.assertEqual(o.patch(f'{COLLS}{a}/', {'name': 'x'}, format='json').status_code, 404)
        self.assertEqual(o.delete(f'{COLLS}{a}/').status_code, 404)
        self.assertTrue(OnlineVideoCollection.objects.filter(pk=a).exists())

    def test_client_chosen_id_is_used_once(self):
        cid = str(uuid.uuid4())
        self.assertEqual(self.c.post(COLLS, {'id': cid, 'name': 'A'}, format='json').data['id'], cid)
        # a second user cannot take (or learn about) that id
        r = client_for(self.other).post(COLLS, {'id': cid, 'name': 'B'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertNotEqual(r.data['id'], cid)
