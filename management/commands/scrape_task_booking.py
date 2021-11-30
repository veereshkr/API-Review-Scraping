from django.core.management.base import BaseCommand, CommandError
from scrape.models import *
from scrape.tasks import *
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

lockfile = '/tmp/scrape_task_booking_lock_file'

def create_lock_file(path):
    try:
        if os.path.exists(path):
            print '%s exists' % path
        else:
            open(path, 'a+').close()
            print 'Created %s file' % path
        try:
            os.chmod(path, 0777)
        except:
            print 'Error in chmod'
    except Exception,e:
        print 'Error in create_lock_file(%s) - %s' % (lockfile, str(e))
        raise


class Command(BaseCommand):
    help = "Scrape Task Expedia"
    def add_arguments(self, parser):
        #parser.add_argument('poll_id', nargs='+', type=int)
	print 'add nothing'
    def handle(self, *args, **options):
        print 'scrape_task_booking.py - handle_noargs'
        now = datetime.now()
        print 'now: %s' % now

	try:
	    if os.path.exists(lockfile):
		print '%s - lock file %s exists. Returning..'  % (datetime.now(), lockfile)
		return
	except Exception, e:
	    print 'Error in chekcing lock file - %s' % (str(e))
	    return

        try:
	    create_lock_file(lockfile)
	    keep_running = True

	    while (keep_running == True):
		interval = 1
	        hotels = Hotel.objects.filter(is_unavailable=False, is_booking_update_running=False).order_by('booking_last_update_date','-hotel_id')
		if len(hotels) == 0:
		    hotels = Hotel.objects.filter(is_unavailable=False, is_booking_update_running=False).order_by('booking_last_update_date','-hotel_id')
		else:
		    print 'check newly added hotels..'
		if len(hotels) > 0:
		    hotel = hotels[0]
		    print 'check for - %s' % (hotel)
		    if hotel.booking_last_update_date is None:
		        print '%s - Run for(last updte date not set) %s - %s' % (datetime.now(), hotel.hotel_id, hotel.name)
			hotel.is_booking_update_running = True
                        hotel.save()
                        task_booking_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
                        is_task_complete = False
                        while (is_task_complete == False):
                            task_hotel = Hotel.objects.get(hotel_id=hotel.hotel_id)
                            if task_hotel.is_booking_update_running == False:
                                is_task_complete = True
                            else:
                                print '%s - Wait for 3 secs..' % (datetime.now())
                                time.sleep(3)
                        random_time = random.randrange(10,20)
                        print '%s - Sleeping for %s secs...' % (datetime.now(), random_time)
                        time.sleep(random_time)
		    else:
		        time_diff = datetime.now() - (hotel.booking_last_update_date).replace(tzinfo=None)
			print '%s - current time_diff: %s' % (datetime.now(), time_diff.total_seconds())
			if time_diff.total_seconds() > 10200:
		            print '%s - Run for %s - %s' % (datetime.now(), hotel.hotel_id, hotel.name)
			    hotel.is_booking_update_running = True
			    hotel.save()
			    task_booking_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
			    is_task_complete = False
			    while (is_task_complete == False):
				task_hotel = Hotel.objects.get(hotel_id=hotel.hotel_id)
				if task_hotel.is_booking_update_running == False:
				    is_task_complete = True
				else:
				    print '%s - Wait for 3 secs..' % (datetime.now())
				    time.sleep(3)
			    random_time = random.randrange(10,20)
			    print '%s - Sleeping for %s secs...' % (datetime.now(), random_time)
			    time.sleep(random_time)
			else:
			    print '%s - You got to wait...' % (datetime.now())
			    keep_running = False
		else:
		    print '%s - No eligible hotels found' % (datetime.now())
		    keep_running = False
        except Exception, e:
            print 'Error in processing hotels - %s' % (str(e))
	try:
	    os.remove(lockfile)
	    print '%s - lock file %s deleted.' % (datetime.now(), lockfile)
	except Exception, e:
	    print '%s - Error in deleting lockfile(%s) - %s' % (datetime.now(), lockfile, str(e))
