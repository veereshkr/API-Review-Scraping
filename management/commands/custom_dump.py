from django.core.management.base import BaseCommand, CommandError
from scrape.models import *
from scrape.helper import *
from datetime import datetime, timedelta
import time
import sys
import os
import os.path
import json
from django.utils import timezone
import random
from django.db.models import Q
from email.mime.text import MIMEText
import smtplib
from django.conf import settings
from collections import OrderedDict
import uuid


class Command(BaseCommand):
    help = "custom_dump"
    def add_arguments(self, parser):
	parser.add_argument('model_name')
	print 'add nothing'
    def handle(self, *args, **options):
        print 'h2.py - handle_noargs'
        now = datetime.now()
        print 'now: %s' % now
	model_name = ''
	model_name = options['model_name']
	print 'model_name: %s' % (model_name)
	if model_name != 'hotel' and model_name != 'review':
	    print 'WRONG MODEL NAME'
	    return
	if model_name == 'hotel':
	    dump_hotel()
	if model_name == 'review':
	    dump_review()

def dump_hotel():
    try:
	hotels = Hotel.objects.all().order_by('hotel_id')
	print 'hotels length: %s' % (len(hotels))

	response_data = []
	for hotel in hotels:
	    entry = OrderedDict();
	    entry['_id'] = uuid.uuid4().hex[:16].lower()
	    entry['hotel_id'] = hotel.hotel_id
	    entry['identifier'] = hotel.identifier
	    entry['name'] = hotel.name
	    entry['gt_location_id'] = hotel.gt_location_id
	    entry['tripadvisor_url'] = hotel.tripadvisor_url
	    entry['booking_url'] = hotel.booking_url
	    entry['expedia_url'] = hotel.expedia_url
	    entry['hotelscom_url'] = hotel.hotelscom_url
	    entry['is_gmb_enabled'] = hotel.is_gmb_enabled
	    entry['tripadvisor_update_window'] = hotel.tripadvisor_update_window
	    entry['booking_update_window'] = hotel.booking_update_window
	    entry['expedia_update_window'] = hotel.expedia_update_window
	    entry['hotelscom_update_window'] = hotel.hotelscom_update_window
	    entry['is_tripadvisor_update_running'] = hotel.is_tripadvisor_update_running
	    entry['tripadvisor_last_update_status'] = hotel.tripadvisor_last_update_status
	    try:
	        entry['tripadvisor_last_update_date'] = hotel.tripadvisor_last_update_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['tripadvisor_last_update_date'] = ''
	    entry['is_tripadvisor_task_running_for_reviewlist'] = hotel.is_tripadvisor_task_running_for_reviewlist
	    entry['tripadvisor_reviews_beyond_threshold'] = hotel.tripadvisor_reviews_beyond_threshold
	    entry['is_booking_update_running'] = hotel.is_booking_update_running
	    entry['booking_last_update_status'] = hotel.booking_last_update_status
	    try:
	        entry['booking_last_update_date'] = hotel.booking_last_update_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['booking_last_update_date'] = ''
	    entry['is_expedia_update_running'] = hotel.is_expedia_update_running
	    entry['expedia_last_update_status'] = hotel.expedia_last_update_status
	    try:
	        entry['expedia_last_update_date'] = hotel.expedia_last_update_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['expedia_last_update_date'] = ''
	    entry['is_google_update_running'] = hotel.is_google_update_running
	    entry['google_last_update_status'] = hotel.google_last_update_status
	    try:
	        entry['google_last_update_date'] = hotel.google_last_update_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['google_last_update_date'] = ''
	    entry['is_hotelscom_update_running'] = hotel.is_hotelscom_update_running
	    entry['hotelscom_last_update_status'] = hotel.hotelscom_last_update_status
	    try:
	        entry['hotelscom_last_update_date'] = hotel.hotelscom_last_update_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['hotelscom_last_update_date'] = ''
	    entry['is_unavailable'] = hotel.is_unavailable
	    entry['date_created'] = hotel.date_created.strftime('%Y-%m-%dT%H:%M:%S')
	    entry['last_modified'] = hotel.last_modified.strftime('%Y-%m-%dT%H:%M:%S')
	    response_data.append(entry)
	outfile = '/home/ubuntu/dump/custom_dump/hotel.json'
	try:
            with open(outfile, 'w') as outfile:
                print 'outfile opened for writing'
                json.dump(response_data, outfile, sort_keys = False, indent = 4)
                print 'Wrote %s successfully' % outfile
                outfile.close()
        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
    except Exception, e:
	print 'error in dump_hotel: %s' % (str(e))

def dump_review():
    try:
	reviews = Review.objects.filter(Q(hotel_id__lt=3))
	print 'reviews length: %s' % (len(reviews))

	response_data = []
	for review in reviews:
	    entry = OrderedDict();
	    entry['_id'] = uuid.uuid4().hex[:16].lower()
	    entry['review_id'] = review.review_id
	    entry['identifier'] = review.identifier
	    entry['hotel_id'] = review.hotel.hotel_id
	    entry['source'] = review.source
	    entry['title'] = review.title
	    entry['comment'] = review.comment
	    entry['comment_negative'] = review.comment_negative
	    entry['comment_pro'] = review.comment_pro
	    entry['comment_location'] = review.comment_location
	    entry['rating'] = review.rating
	    entry['rating_list_title'] = review.rating_list_title
	    entry['rating_list_text'] = review.rating_list_text
	    entry['room_tip'] = review.room_tip
	    author = {}
	    author['reviewer_id'] = review.author.reviewer_id
	    author['identifier'] = review.author.identifier
	    author['name'] = review.author.name
	    author['contributor_level'] = review.author.contributor_level
	    author['total_reviews'] = review.author.total_reviews
	    author['hotel_reviews'] = review.author.hotel_reviews
	    author['helpful_votes'] = review.author.helpful_votes
	    author['remarks'] = review.author.remarks
	    entry['author'] = author
	    try:
	        entry['review_date'] = review.review_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['review_date'] = ''
	    entry['url'] = review.url
	    entry['has_manager_response'] = review.has_manager_response
	    entry['suggested_response'] = review.suggested_response
	    try:
	        entry['suggested_response_date'] = review.suggested_response_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['suggested_response_date'] = ''
	    entry['suggested_response_signature'] = review.suggested_response_signature
	    entry['response_posted_checkbox'] = review.response_posted_checkbox
	    entry['level_1_username'] = review.level_1_username
	    entry['level_2_username'] = review.level_2_username
	    entry['manager_response'] = review.manager_response
	    try:
	        entry['manager_response_date'] = review.manager_response_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['manager_response_date'] = ''
	    entry['is_ready_to_be_posted'] = review.is_ready_to_be_posted
	    entry['approval_key'] = review.approval_key
	    entry['is_sent_for_approval'] = review.is_sent_for_approval
	    try:
	        entry['sent_for_approval_date'] = review.sent_for_approval_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['sent_for_approval_date'] = ''
	    entry['is_auto_approved'] = review.is_auto_approved
	    entry['is_approved'] = review.is_approved
	    try:
	        entry['approval_date'] = review.approval_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['approval_date'] = ''
	    entry['edited_response'] = review.edited_response
	    try:
	        entry['edited_response_date'] = review.edited_response_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['edited_response_date'] = ''
	    entry['more_info_key'] = review.more_info_key
	    entry['is_sent_for_more_info'] = review.is_sent_for_more_info
	    try:
	        entry['sent_for_more_info_date'] = review.sent_for_more_info_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['sent_for_more_info_date'] = ''
	    try:
	        entry['more_info_received_date'] = review.more_info_received_date.strftime('%Y-%m-%dT%H:%M:%S')
	    except Exception, e:
	        entry['more_info_received_date'] = ''
	    entry['more_info_msg'] = review.more_info_msg
	    entry['more_info_response'] = review.more_info_response
	    entry['is_sentiment_processed'] = review.is_sentiment_processed
	    entry['is_non_english'] = review.is_non_english
	    entry['removed_at_source'] = review.removed_at_source
	    entry['is_partial'] = review.is_partial
	    entry['is_unavailable'] = review.is_unavailable
	    entry['date_created'] = review.date_created.strftime('%Y-%m-%dT%H:%M:%S')
	    entry['last_modified'] = review.last_modified.strftime('%Y-%m-%dT%H:%M:%S')

	    response_data.append(entry)
	outfile = '/home/ubuntu/dump/custom_dump/review.json'
	try:
            with open(outfile, 'w') as outfile:
                print 'outfile opened for writing'
                json.dump(response_data, outfile, sort_keys = False, indent = 4)
                print 'Wrote %s successfully' % outfile
                outfile.close()
        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
    except Exception, e:
	print 'error in dump_review: %s' % (str(e))
