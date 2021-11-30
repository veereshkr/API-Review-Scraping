from django.core.management.base import BaseCommand, CommandError
from scrape.models import *
from scrape.helper import *
from datetime import datetime, timedelta
import time
import sys
import os
import os.path
from django.utils import timezone
import random
from django.db.models import Q
from email.mime.text import MIMEText
import smtplib
from django.conf import settings


class Command(BaseCommand):
    help = "h1"
    def add_arguments(self, parser):

	print 'add nothing'
    def handle(self, *args, **options):
        print 'h1.py - handle_noargs'
        now = datetime.now()
        print 'now: %s' % now
    v_test_1()
