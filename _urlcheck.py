import os  
os.environ.setdefault('DJANGO_SETTINGS_MODULE','godfident.settings')  
import django  
django.setup()  
from django.urls import reverse, NoReverseMatch  
ok=[];fail=[]  
names=['register','login','token-refresh','logout','me','profile','translation-list','book-list','verse','chapter','search','reading-progress','verse-of-the-day','devotional-list','today-devotional','reading-plan-list','user-reading-plan-list','prayer-list','prayer-session-list','prayer-journal-list','prayer-log-list','prayer-streak','ai-chat','study-history','notification-list','fcm-device-list','analytics-dashboard','analytics-prayer','analytics-focus','analytics-notes','note-list','note-folder-list','note-topic-list','rule-list','rule-category-list','reminder-list','focus-session-list','blocked-app-list','achievement-list','user-achievement-list','global-search']  
for n in names:  
    try: reverse(n); ok.append(n)  
    except NoReverseMatch: fail.append(n)  
print('Resolved:',len(ok),'Failed:',len(fail))  
[print('FAIL',n) for n in fail]  
