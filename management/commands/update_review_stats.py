from django.core.management.base import BaseCommand, CommandError
from scrape.models import *
from scrape.tasks import *
from datetime import datetime, timedelta, date
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

def get_review_count_for_hotel(hotel, source, start_date, end_date):
    review_count = Review.objects.filter(hotel=hotel, source=source, is_non_english=False, is_unavailable=False).filter(Q(review_date__gte=start_date)).filter(Q(review_date__lt=end_date)).count()
    review_responded_count = Review.objects.filter(hotel=hotel, source=source, has_manager_response=True, is_non_english=False, is_unavailable=False).filter(Q(review_date__gte=start_date)).filter(Q(review_date__lt=end_date)).count()
    return review_count, review_responded_count

class Command(BaseCommand):
    help = "update_review_stats"
    def add_arguments(self, parser):
	print 'add nothing'
    def handle(self, *args, **options):
        print 'update_review_stats.py - handle_noargs'
        now = datetime.now()
        print 'now: %s' % now

        try:
    	    hotels = Hotel.objects.filter(is_unavailable=False).order_by('hotel_id')
    	    print 'hotels count:%s' % (len(hotels))
    	    first_date_of_month = date.today()
    	    print 'first_date_of_month: %s' % (first_date_of_month)

    	    first_date_of_month = first_date_of_month.replace(day=1)
    	    print 'first_date_of_month: %s' % (first_date_of_month)
    	    next_month = datetime.now().month+1
    	    print 'next_month: %s' % (next_month)
    	    for month in range(1,next_month):
    		print 'for month: %s' % (month)
    		dt1 = first_date_of_month.replace(month=month)
    		dt2 = first_date_of_month.replace(month=month+1)
    		print 'dt1: %s # dt2: %s' % (dt1, dt2)


    		for hotel in hotels[:10]:
    		    print 'hotel: %s' % (hotel)
    		    source = 2
    		    tripadvisor_reviews, tripadvisor_reviews_responded = get_review_count_for_hotel(hotel, source, dt1, dt2)

    		    print 'tripadvisor_reviews: %s/%s' % (tripadvisor_reviews_responded, tripadvisor_reviews)

        except Exception, e:
            print 'Error in update_review_stats.py - %s' % (str(e))
