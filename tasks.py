from __future__ import absolute_import

from celery import shared_task
from celery.decorators import task
from celery import chain

from scrape.models import *
from scrape.helper import *
from django.conf import settings



@shared_task
def task_wrapper_expedia_by_hotel_id(timedelay, uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'task_wrapper_scrape_expedia_by_hotel_id'
    timedelay = int(timedelay)
    params = [uid, inputurl, follownext, firstrun, ischained, overall]
    print 'params added'
    task_expedia_by_hotel_id.apply_async(args=params, countdown=timedelay)
    return 'EXPEDIA WRAPPER - QUEUED'

@shared_task
def task_expedia_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    helper_scrape_expedia_by_hotel_id(uid, inputurl, follownext, firstrun, ischained, overall)
    hotel = Hotel.objects.get(hotel_id=uid)
    try:
        from django import db
        db.connections.close_all()
        print 'DB CONNECTION CLOSED expedia'
    except Exception, e:
        print 'ERORR IN CLOSING DB CONNECTION expedia: %s' % (str(e))
    return 'EXPEDIA - uid(%s-%s) - inputurl(%s) - follownext(%s) -- firstrun(%s) -- ischained(%s) -- overall(%s) ' % (uid, hotel.name, inputurl, follownext, firstrun, ischained, overall)



@shared_task
def task_booking_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    helper_scrape_booking_hotel_id(uid, inputurl, follownext, firstrun, ischained, overall)
    hotel = Hotel.objects.get(hotel_id=uid)
    return 'BOOKING - uid(%s-%s) - inputurl(%s) - follownext(%s) -- firstrun(%s) -- ischained(%s) -- overall(%s)" ' % (uid, hotel.name, inputurl, follownext, firstrun, ischained, overall)

@shared_task
def task_wrapper_booking_by_reviewlist_url(timedelay, uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'task_wrapper_booking_by_reviewlist_url'
    timedelay = int(timedelay)
    params = [uid, inputurl, follownext, firstrun, ischained, overall]
    print 'params added'
    task_booking_by_reviewlist_url.apply_async(args=params, countdown=timedelay)
    return 'BOOKING WRAPPER FOR REVIEWLIST - QUEUED'

@shared_task
def task_booking_by_reviewlist_url(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    helper_scrape_booking_by_reviewlist_url(uid, inputurl, follownext, firstrun, ischained, overall)
    try:
        from django import db
        db.connections.close_all()
        print 'DB CONNECTION CLOSED booking'
    except Exception, e:
        print 'ERORR IN CLOSING DB CONNECTION booking: %s' % (str(e))
    hotel = Hotel.objects.get(hotel_id=uid)
    return 'BOOKING - uid(%s-%s) - inputurl(%s) - follownext(%s) -- firstrun(%s) -- ischained(%s) -- overall(%s)" ' % (uid, hotel.name, inputurl, follownext, firstrun, ischained, overall)

@shared_task
def task_wrapper_booking_overall_hotel(timedelay, uid, inputurl=None):
    print 'task_wrapper_booking_overall_hotel'
    timedelay = int(timedelay)
    params = [uid, inputurl]
    print 'params added'
    task_booking_overall_hotel.apply_async(args=params, countdown=timedelay)
    return 'BOOKING WRAPPER FOR RATINGS OVERALL - QUEUED'

@shared_task
def task_booking_overall_hotel(uid, inputurl=None):
    helper_scrape_booking_overall_hotel(uid, inputurl)
    hotel = Hotel.objects.get(hotel_id=uid)
    return 'BOOKING OVERALL RATINGS - "uid(%s-%s) - inputurl(%s)" ' % (uid, hotel.name, inputurl)

@shared_task
def task_wrapper_tripadvisor_by_hotel_id(timedelay, uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'task_wrapper_tripadvisor_by_hotel_id'
    timedelay = int(timedelay)
    params = [uid, inputurl, follownext, firstrun, ischained, overall]
    print 'params added'
    task_tripadvisor_by_hotel_id.apply_async(args=params, countdown=timedelay)
    return 'TRIPADVISOR WRAPPER FOR HOTEL BY ID - QUEUED'

@shared_task
def task_tripadvisor_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    hotel = Hotel.objects.get(hotel_id=uid)
    helper_scrape_tripadvisor_by_hotel_id(uid, inputurl, follownext, firstrun, ischained, overall)
    return 'TRIPADVISOR - uid(%s-%s) - inputurl(%s) - follownext(%s) -- firstrun(%s) -- ischained(%s) -- overall(%s)" ' % (uid, hotel.name, inputurl, follownext, firstrun, ischained, overall)

@shared_task
def task_wrapper_tripadvisor_by_reviewlist(timedelay, uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall):
    print 'task_wrapper_tripadvisor_by_reviewlst'
    timedelay = int(timedelay)
    params = [uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall]
    print 'params added'
    task_tripadvisor_by_reviewlist.apply_async(args=params, countdown=timedelay)
    return 'TRIPADVISOR WRAPPER FOR REVIEWLIST - QUEUED'

@shared_task
def task_tripadvisor_by_reviewlist(uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall):
    print 'task_tripadvisor_by_reviewlist: uid(%s) - reviewid list length(%s) - inputurl list length(%s) - nexturl(%s) - firstrun(%s) - follownext(%s) - ischained(%s) - overall(%s)" ' % (uid, len(reviewid_list), len(inputurl_list), nexturl, firstrun, follownext, ischained, overall)
    hotel = Hotel.objects.get(hotel_id=uid)
    helper_scrape_tripadvisor_by_reviewlist(uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall)
    try:
        from django import db
        db.connections.close_all()
        print 'DB CONNECTION CLOSED tripadvisor'
    except Exception, e:
        print 'ERORR IN CLOSING DB CONNECTION tripadvisor: %s' % (str(e))
    return 'TRIPADVISOR - uid(%s-%s) - reviewid list length(%s) - inputurl list length(%s) - nexturl(%s) - firstrun(%s) - follownext(%s) - ischained(%s) - overall(%s)" ' % (uid, hotel.name, len(reviewid_list), len(inputurl_list), nexturl, firstrun, follownext, ischained, overall)





@shared_task
def task_wrapper_google_by_hotel_id(timedelay, uid):
    print 'task_wrapper_scrape_google_by_hotel_id'
    timedelay = int(timedelay)
    params = [uid]
    print 'params added'
    task_google_by_hotel_id.apply_async(args=params, countdown=timedelay)
    return 'GOOGLE WRAPPER - QUEUED'

@shared_task
def task_google_by_hotel_id(uid):
    helper_scrape_google_by_hotel_id(uid)
    hotel = Hotel.objects.get(hotel_id=uid)
    return 'GOOGLE - uid(%s-%s)' % (uid, hotel.name)



@shared_task
def task_wrapper_hotelscom_by_hotel_id(timedelay, uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'task_wrapper_scrape_hotelscom_by_hotel_id'
    timedelay = int(timedelay)
    params = [uid, inputurl, follownext, firstrun, ischained, overall]
    print 'params added'
    task_hotelscom_by_hotel_id.apply_async(args=params, countdown=timedelay)
    return 'HOTELS.COM WRAPPER - QUEUED'

@shared_task
def task_hotelscom_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    helper_scrape_hotelscom_by_hotel_id(uid, inputurl, follownext, firstrun, ischained, overall)
    try:
        from django import db
        db.connections.close_all()
        print 'DB CONNECTION CLOSED hotelscom'
    except Exception, e:
        print 'ERORR IN CLOSING DB CONNECTION hotelscom: %s' % (str(e))
    hotel = Hotel.objects.get(hotel_id=uid)
    return 'HOTELS.COM - uid(%s-%s) - inputurl(%s) - follownext(%s) -- firstrun(%s) -- ischained(%s) -- overall(%s) ' % (uid, hotel.name, inputurl, follownext, firstrun, ischained, overall)




