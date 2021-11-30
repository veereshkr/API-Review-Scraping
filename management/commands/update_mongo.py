from django.core.management.base import BaseCommand, CommandError
from scrape.models import *
from datetime import datetime, timedelta
from django.utils import timezone
import random
from django.db.models import Q
from email.mime.text import MIMEText
import smtplib
from django.conf import settings
from pymongo import MongoClient
from collections import OrderedDict
import uuid
import json
from bson import json_util

db = None

class Command(BaseCommand):
    help = "update_mongo"

    def handle(self, *args, **options):
        print 'update_mongo.py - handle_noargs'
        dt_now = datetime.now()
        print 'dt_now: %s' % (dt_now)
        dt_N_days_ago = datetime.now() - timedelta(days=1)
        print 'dt_N_days_ago: %s' % (dt_N_days_ago)
	try:

	    client = MongoClient('')
	    db = client.reviewdb
	    print 'mongo hotels count: %s' % (db.hotels.find().count())
	    print 'mongo reviews count: %s' % (db.review.find().count())
	except Exception, e:
	    print 'error in getting mongo client: %s' % (str(e))

	hotels = Hotel.objects.filter(is_unavailable=False).order_by('hotel_id')
	for hotel in hotels[0:]:
	    update_reviews_for_hotel(db, hotel.hotel_id);
	client.close()

def update_hotels(db):
    try:
        hotels = Hotel.objects.filter().order_by('date_created')
        print 'Number of eligible hotels: %s' % (len(hotels))
        for hotel in hotels:
            status, result_json = make_jsom_from_hotel(hotel)
            print 'status: %s' % (status)
            print 'result_json len: %s' % len(json.dumps(result_json, default=json_util.default))
            try:
                exist_count = db.hotels.find({'hotel_id':hotel.hotel_id}).count()
                if exist_count == 0:
                    insert_result = db.hotels.insert_one((result_json))
                    print 'insert_result id: %s' % (insert_result.inserted_id)
                else:
                    print 'existing hotel found in mongodb'
            except Exception, e:
                print 'error in inserting in mongo: %s' % (str(e))
    except Exception, e:
        print 'Error in getting hotels - %s' % (str(e))

def update_reviews_for_hotel(db, hotel_id):
    print 'update_reviews_for_hotel: %s' % (hotel_id)
    try:
        reviews = Review.objects.filter(hotel__hotel_id=hotel_id).order_by('date_created')
        print 'Number of eligible reviews: %s' % (len(reviews))
	for review in reviews:
	    status, result_json = make_jsom_from_review(review)
	    print 'status: %s' % (status)
	    print 'result_json len: %s' % len(json.dumps(result_json, default=json_util.default))
	    try:
		exist_count = db.review.find({'review_id':review.review_id}).count()
		if exist_count == 0:
		    insert_result = db.review.insert_one((result_json))
		    print 'insert_result id: %s' % (insert_result.inserted_id)
		else:
		    print 'existing review found in mongodb'
	    except Exception, e:
		print 'error in inserting in mongo: %s' % (str(e))
    except Exception, e:
        print 'Error in getting reviews - %s' % (str(e))

def make_jsom_from_review(review):
    entry = OrderedDict();
    try:
	if review:
            print 'review_id: %s' % (review.review_id)
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
                entry['review_date'] = review.review_date
            except Exception, e:
                entry['review_date'] = ''
            entry['url'] = review.url
            entry['has_manager_response'] = review.has_manager_response
            entry['suggested_response'] = review.suggested_response
            try:
                entry['suggested_response_date'] = review.suggested_response_date
            except Exception, e:
                entry['suggested_response_date'] = ''
            entry['suggested_response_signature'] = review.suggested_response_signature
            entry['response_posted_checkbox'] = review.response_posted_checkbox
            entry['level_1_username'] = review.level_1_username
            entry['level_2_username'] = review.level_2_username
            entry['manager_response'] = review.manager_response
            try:
                entry['manager_response_date'] = review.manager_response_date
            except Exception, e:
                entry['manager_response_date'] = ''
            entry['is_ready_to_be_posted'] = review.is_ready_to_be_posted
            entry['approval_key'] = review.approval_key
            entry['is_sent_for_approval'] = review.is_sent_for_approval
            try:
                entry['sent_for_approval_date'] = review.sent_for_approval_date
            except Exception, e:
                entry['sent_for_approval_date'] = ''
            entry['is_auto_approved'] = review.is_auto_approved
            entry['is_approved'] = review.is_approved
            try:
                entry['approval_date'] = review.approval_date
            except Exception, e:
                entry['approval_date'] = ''
            entry['edited_response'] = review.edited_response
            try:
                entry['edited_response_date'] = review.edited_response_date
            except Exception, e:
                entry['edited_response_date'] = ''
            entry['more_info_key'] = review.more_info_key
            entry['is_sent_for_more_info'] = review.is_sent_for_more_info
            try:
                entry['sent_for_more_info_date'] = review.sent_for_more_info_date
            except Exception, e:
                entry['sent_for_more_info_date'] = ''
            try:
                entry['more_info_received_date'] = review.more_info_received_date
            except Exception, e:
                entry['more_info_received_date'] = ''
            entry['more_info_msg'] = review.more_info_msg
            entry['more_info_response'] = review.more_info_response
            entry['is_sentiment_processed'] = review.is_sentiment_processed
            entry['is_non_english'] = review.is_non_english
            entry['removed_at_source'] = review.removed_at_source
            entry['is_partial'] = review.is_partial
            entry['is_unavailable'] = review.is_unavailable
            entry['date_created'] = review.date_created
            entry['last_modified'] = review.last_modified
            entry['entry_source'] = 'upload'
	    return True, entry
	else:
	    print 'review is None'
	    return False, entry
    except Exception, e:
	print 'Error in converting review to json: %s' % (str(e))
	return False, entry

def make_jsom_from_hotel(hotel):
    entry = OrderedDict();
    try:
	if hotel:
            print 'hotel_id: %s' % (hotel.hotel_id)
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
                entry['tripadvisor_last_update_date'] = hotel.tripadvisor_last_update_date
            except Exception, e:
                entry['tripadvisor_last_update_date'] = ''
            entry['is_tripadvisor_task_running_for_reviewlist'] = hotel.is_tripadvisor_task_running_for_reviewlist
            entry['tripadvisor_reviews_beyond_threshold'] = hotel.tripadvisor_reviews_beyond_threshold
            entry['is_booking_update_running'] = hotel.is_booking_update_running
            entry['booking_last_update_status'] = hotel.booking_last_update_status
            try:
                entry['booking_last_update_date'] = hotel.booking_last_update_date
            except Exception, e:
                entry['booking_last_update_date'] = ''
            entry['is_expedia_update_running'] = hotel.is_expedia_update_running
            entry['expedia_last_update_status'] = hotel.expedia_last_update_status
            try:
                entry['expedia_last_update_date'] = hotel.expedia_last_update_date
            except Exception, e:
                entry['expedia_last_update_date'] = ''
            entry['is_google_update_running'] = hotel.is_google_update_running
            entry['google_last_update_status'] = hotel.google_last_update_status
            try:
                entry['google_last_update_date'] = hotel.google_last_update_date
            except Exception, e:
                entry['google_last_update_date'] = ''
            entry['is_hotelscom_update_running'] = hotel.is_hotelscom_update_running
            entry['hotelscom_last_update_status'] = hotel.hotelscom_last_update_status
            try:
                entry['hotelscom_last_update_date'] = hotel.hotelscom_last_update_date
            except Exception, e:
                entry['hotelscom_last_update_date'] = ''
            entry['is_unavailable'] = hotel.is_unavailable
            entry['date_created'] = hotel.date_created
            entry['last_modified'] = hotel.last_modified
	    return True, entry
	else:
	    print 'location is None'
	    return False, entry
    except Exception, e:
	print 'Error in converting location to json: %s' % (str(e))
	return False, entry


def update_sentiments(db):
    try:
	reviews = Review.objects.filter(is_sentiment_processed=True, is_unavailable=False).all()
	print 'eligible reviews count: %s' % (len(reviews))
	for review in reviews:
	    if review.review_id and review.hotel.hotel_id:
	        update_sentiment(db, review)
    except Exception, e:
	print 'Error in update_sentiments: %s' % (str(e))

def update_sentiment(db, review):
    try:
	print 'update_sentiment for review_id(%s) / hotel_id(%s)' % (review.review_id, review.hotel.hotel_id)
	hotel_id = review.hotel.hotel_id
	review_id = review.review_id
        review_aspects = SntReviewAspect.objects.filter(r_id=review_id).order_by('last_modified')
	aspects = []
	for item in review_aspects:
	    entry = {}
	    entry['aspect'] = item.aspect
	    entry['aspect_confidence'] = item.a_conf
	    entry['polarity'] = item.polarity
	    entry['polarity_confidence'] = item.p_conf
	    aspects.append(entry)
        print 'aspects: %s' % (aspects)

        review_sentences = SntReviewSentence.objects.filter(r_id=review_id).order_by('last_modified')
	sentences = []
	for item in review_sentences:
	    entry = {}
	    entry['text'] = item.text
	    entry['aspects'] = []
            review_sentence_aspects = SntReviewSentenceAspect.objects.filter(srs_id=item.srs_id).order_by('last_modified')
	    for sa in review_sentence_aspects:
		sub_entry = {}
		sub_entry['aspect'] = sa.aspect
		sub_entry['aspect_confidence'] = sa.a_conf
		sub_entry['polarity'] = sa.polarity
		sub_entry['polarity_confidence'] = sa.p_conf
	        entry['aspects'].append(sub_entry)
	    sentences.append(entry)
	print 'sentences: %s' % (sentences)
	insert_param = OrderedDict();
	insert_param['_id'] = uuid.uuid4().hex[:16].lower()
	insert_param['hotel_id'] = hotel_id
	try:
	    mongo_review_id = None
	    mongo_review = db.review.find_one({'review_id':review_id})
	    if mongo_review:
		print 'mongo_review: %s' % (mongo_review['review_id'])
		mongo_review_id = mongo_review['_id']
		insert_param['mongo_review_id'] = mongo_review_id
		insert_param['review_id'] = review_id
		insert_param['text'] = review.comment
		insert_param['aspects'] = aspects
		insert_param['sentences'] = sentences
		insert_param['source'] = 'upload'
		insert_param['date_created'] = datetime.now()
	    print 'mongo_review_id: %s' % (mongo_review_id)
            exist_count = db.sentiments.find({'mongo_review_id':mongo_review_id}).count()
            if exist_count == 0:
		print 'insert_param: %s' % (insert_param)
                insert_result = db.sentiments.insert_one((insert_param))
                print 'insert_result id: %s' % (insert_result.inserted_id)
            else:
                print 'existing sentiment found in mongodb'
        except Exception, e:
            print 'error in inserting in mongo: %s' % (str(e))

    except Exception, e:
        print 'Error in update_sentiment - %s' % (str(e))

