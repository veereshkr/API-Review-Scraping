import requests
import urllib2
from bs4 import BeautifulSoup

import os
import os.path
import subprocess
from datetime import datetime, timedelta
import sys
import time
import json
import random
import re
from requests.auth import HTTPBasicAuth
import dateutil.parser

from django.conf import settings
from scrape.models import *
from scrape.mongo_helper import *


DATA_SERVER_1 = 'x.x.x.x'

DATA_SERVER_2_APACHE = 'x.x.x.x'

DATA_SERVER_3_APACHE = 'x.x.x.x'

DATA_SERVER_2 = 'x.x.x.x'


DATA_SERVER_3_SELENIUM = 'x.x.x.x'

ua_list = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
            'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
            'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
        ]

count_beyond_date_tripadvisor = 0

def convert_rating_to_number_tripadvisor(rating):
    rating_number = 0;
    try:
        # "3 of 5 bubbles" / "3 of 5 stars" / "3.0 of 5 bubbles"
        tstr = rating
        tarr = tstr.split('of')
        rating_number = float(tarr[0].lstrip().rstrip())
    except Exception, e:
        print 'Error in convert_rating_to_number_tripadvisor: %s' % (str(e))
    return rating_number

def convert_rating_to_number_booking(rating):
    rating_number = 0;
    try:
        # "3.1" / "10"
        tstr = rating
        rating_number = float(tstr.lstrip().rstrip())
    except Exception, e:
        print 'Error in convert_rating_to_number_booking: %s' % (str(e))
    return rating_number

def convert_rating_to_number_expedia(rating):
    rating_number = 0;
    try:
	# "3 out of 5" / "3out of 5"
	tstr = rating
	tarr = tstr.split('out')
	rating_number = float(tarr[0].lstrip().rstrip())
    except Exception, e:
	print 'Error in convert_rating_to_number_expedia: %s' % (str(e))
    return rating_number

def convert_rating_to_number_google(rating):
    rating_number = 0;
    try:
        # "ONE" / "TWO"
        tstr = rating
	tstr = tstr.lstrip().rstrip()
	if tstr == "ONE":
	    return float(1);
	if tstr == "TWO":
	    return float(2);
	if tstr == "THREE":
	    return float(3);
	if tstr == "FOUR":
	    return float(4);
	if tstr == "FIVE":
	    return float(5);
    except Exception, e:
        print 'Error in convert_rating_to_number_google: %s' % (str(e))
    return rating_number

def convert_rating_to_number_hotelscom(rating):
    rating_number = 0;
    try:
        # "3.1" / "10"
        tstr = rating
        rating_number = float(tstr.lstrip().rstrip())
    except Exception, e:
        print 'Error in convert_rating_to_number_hotelscom: %s' % (str(e))
    return rating_number

def get_tripadvisor_hotel_id_from_url(url):
    hotel_id = ''
    try:
	t1 = url
	tlist = t1.split('/Hotel_Review')
	if len(tlist) == 2:
	    t1 = tlist[1]
	    tlist = t1.split('-d')
	    if len(tlist) == 2:
		t1 = tlist[1]
		tlist = t1.split('-')
		if len(tlist) > 1:
		    hotel_id = tlist[0]
    except Exception, e:
	print 'Error in get_tripadvisor_hotel_id_from_url: %s' % (str(e))
    return hotel_id

def get_expedia_hotel_id_from_url(url):
    hotel_id = ''
    try:
        t1 = url
	if t1.find('expedia.com') > 0:
            tlist = t1.split('.Hotel-Reviews')
            if len(tlist) == 2:
                t1 = tlist[0]
                tlist = t1.split('.h')
                if len(tlist) == 2:
                    hotel_id = tlist[1]
    except Exception, e:
        print 'Error in get_expedia_hotel_id_from_url: %s' % (str(e))
    return hotel_id

def get_hotelscom_hotel_id_from_url(url):
    hotel_id = ''
    try:
        t1 = url
        if t1.find('hotels.com/ho') > 0:
            tlist = t1.split('.com/ho')
            if len(tlist) == 2:
                t1 = tlist[1]
                tlist = t1.split('-tr/')
                if len(tlist) == 2:
                    hotel_id = tlist[0]
    except Exception, e:
        print 'Error in get_hotelcom_hotel_id_from_url: %s' % (str(e))
    if hotel_id == '':
	try:
	    t1 = url
	    if t1.find('hotels.com/hotel/details') > 0:
		tlist = t1.split('hotelId=')
		if len(tlist) == 2:
		    t1 = tlist[1]
		    tlist = t1.split('&')
		    if len(tlist) > 1:
			hotel_id = tlist[0]
	except Exception, e:
	    print 'Error in get_hotelcom_hotel_id_from_url fallback: %s' % (str(e))
    return hotel_id

def get_booking_hotel_id_from_url(url):
    hotel_id = ''
    try:
	args = { 'auth' :'zc3wiu4e6z1nwgye', 'q': url}
	data_server_url = 'http://{0}/bnuy6vwh89enjkyo/'.format(DATA_SERVER_2)
	print 'data_server_url: %s' % (data_server_url)
	connect_timeout, read_timeout = 5.0, 20.0
        response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
        print response.status_code
        page = response.content
	soup = BeautifulSoup(page, "html5lib")
	hotel_id = str(soup.find('input',attrs={'name':'hotel_id'}).get('value').lstrip().rstrip())
        print '# hotel_id: %s' % (hotel_id)
    except Exception, e:
        print 'Error in get_booking_hotel_id_from_url: %s' % (str(e))
    return hotel_id


def read_overall_booking(hotel, soup):
    print 'read_overall_booking %s' % hotel
    try:
	found = False
	curdate = datetime.now().date()
	overall = ''
	all = BookingOverallRating.objects.filter(hotel=hotel).order_by('-date_created')
	for a in all:
	    if a.date_created.date() == curdate:
		found = True
		overall = a
		break
	if found == False:
	    overall = BookingOverallRating.objects.create(hotel=hotel)
	    print 'New BookingOverallRating created'
	if found == True:
	    print 'Existing BookingOverallRating found'
    except Exception, e:
	print 'Error in getting BookingOverallRating record - %s' % (str(e))
	return
    try:
	print 'processing soup'
	total_reviews_for_score = hotel_stars = hotel_rank = rating_overall = rating_cleanliness = rating_comfort = rating_location = rating_facilities = rating_staff = rating_value_for_money = rating_free_wifi = ''
	try:
            tstr = soup.find('div', attrs={'id':'review_list_score'}).find('p', attrs={'class':'review_list_score_count'}).text.lstrip().rstrip()
	    if tstr.find('hotel reviews') > 0:
		tstr = tstr[0:tstr.find('hotel reviews')].lstrip().rstrip()
	    if tstr.find('Based on') == 0:
		tstr = tstr[len('Based on'):].lstrip().rstrip()
	    total_reviews_for_score = tstr
            print 'total_reviews_for_score: %s' % total_reviews_for_score
        except Exception, e:
            print 'Error in getting total_reviews_for_score - %s' % (str(e))
	try:
            hotel_stars = soup.find('div', attrs={'id':'standalone_reviews_hotel_info_wrapper'}).find('h1', attrs={'class':'hotel_name'}).find('i', attrs={'class':'stars'}).get('title').lstrip().rstrip()
            print 'hotel_stars: %s' % hotel_stars
        except Exception, e:
            print 'Error in getting hotel_stars - %s' % (str(e))
	try:
            hotel_rank = soup.find('div', attrs={'id':'standalone_reviews_hotel_info_wrapper'}).find('p', attrs={'class':'hotel_rank'}).text.lstrip().rstrip()
            print 'hotel_rank: %s' % hotel_rank
        except Exception, e:
            print 'Error in getting hotel_rank - %s' % (str(e))
	try:
            rating_overall = soup.find('div', attrs={'id':'review_list_score'}).find('div', attrs={'id':'review_list_main_score'}).text.lstrip().rstrip()
            print 'rating_overall: %s' % rating_overall
        except Exception, e:
            print 'Error in getting rating_overall - %s' % (str(e))
	try:
	    links = soup.find('div', attrs={'id':'review_list_score'}).find('ul', attrs={'id':'review_list_score_breakdown'}).findAll('li')
	    for link in links:
		key = link.find('p', attrs={'class':'review_score_name'}).text.lstrip().rstrip()
		value = link.find('p', attrs={'class':'review_score_value'}).text.lstrip().rstrip()
		if key == 'Cleanliness':
		    rating_cleanliness = value
		    print 'rating_cleanliness: %s' % rating_cleanliness
		    continue
		if key == 'Comfort':
		    rating_comfort = value
		    print 'rating_comfort: %s' % rating_comfort
		    continue
		if key == 'Location':
		    rating_location = value
		    print 'rating_location: %s' % rating_location
		    continue
		if key == 'Facilities':
		    rating_facilities = value
		    print 'rating_facilities: %s' % rating_facilities
		    continue
		if key == 'Staff':
		    rating_staff = value
		    print 'rating_staff: %s' % rating_staff
		    continue
		if key == 'Value for money':
                    rating_value_for_money = value
                    print 'rating_value_for_money: %s' % rating_value_for_money
                    continue
		if key == 'Free WiFi':
                    rating_free_wifi = value
                    print 'rating_free_wifi: %s' % rating_free_wifi
                    continue
	except Exception, e:
	    'Error in getting rating_cleanliness / rating_comfort / etc - %s' % (str(e))
    except Exception, e:
	print 'error in processing soup - %s' % (str(e))
	return
    try:
	overall.total_reviews_for_score = total_reviews_for_score
	overall.hotel_stars = hotel_stars
	overall.hotel_rank = hotel_rank
	overall.rating_overall = rating_overall
	overall.rating_cleanliness = rating_cleanliness
	overall.rating_comfort = rating_comfort
	overall.rating_location = rating_location
	overall.rating_facilities = rating_facilities
	overall.rating_staff = rating_staff
	overall.rating_value_for_money = rating_value_for_money
	overall.rating_free_wifi = rating_free_wifi
	print 'Try saving BookingOverallRating'
	overall.save()
	print 'BookingOverallRating updated'
    except Exception, e:
	print 'Error in updating BookingOverallRating - %s' % (str(e))
    try:
	mongo_overall = MongoBookingOverallRating()
	mentry = OrderedDict()
        mentry['hotel_id'] = hotel.hotel_id
        mentry['total_reviews_for_score'] = total_reviews_for_score
        mentry['hotel_stars'] = hotel_stars
        mentry['hotel_rank'] = hotel_rank
        mentry['rating_overall'] = rating_overall
        mentry['rating_cleanliness'] = rating_cleanliness
        mentry['rating_comfort'] = rating_comfort
        mentry['rating_location'] = rating_location
        mentry['rating_facilities'] = rating_facilities
        mentry['rating_staff'] = rating_staff
        mentry['rating_value_for_money'] = rating_value_for_money
        mentry['rating_free_wifi'] = rating_free_wifi
        mentry['date_created'] = datetime.now()
        print 'Try saving MongoBookingOverallRating'
	mongo_overall.add_params(mentry)
        mongo_overall.save()
        print 'MongoBookingOverallRating updated'
    except Exception, e:
        print 'Error in updating MongoBookingOverallRating - %s' % (str(e))
    return

## Read overall rating info from Expedia
def read_overall_expedia(hotel, soup):
    print 'read_overall_expedia %s' % hotel
    try:
	found = False
	curdate = datetime.now().date()
	overall = ''
	all = ExpediaOverallRating.objects.filter(hotel=hotel).order_by('-date_created')
	for a in all:
	    if a.date_created.date() == curdate:
		found = True
		overall = a
		break
	if found == False:
	    overall = ExpediaOverallRating.objects.create(hotel=hotel)
	    print 'NEW ExpediaOverallRating created'
	if found == True:
	    print 'EXISTING ExpediaOverallRating found'
    except Exception, e:
	print 'URGENT - Error in getting ExpediaOverallRating record - %s' % (str(e))
	return
    try:
	print 'processing soup'
	total_reviews_for_score = hotel_stars = rating_overall = rating_cleanliness = rating_comfort = rating_staff = rating_hotel_condition = recommendation_percentage = ''
	try:
            tstr = soup.find('section', attrs={'class':'review-summary'}).find('h2', attrs={'class':'header'}).text.lstrip().rstrip()
	    if tstr.find('Verified Reviews') > 0:
		tstr = tstr[0:tstr.find('Verified Reviews')].lstrip().rstrip()
	    if tstr.find('Ratings based on') == 0:
		tstr = tstr[len('Ratings based on'):].lstrip().rstrip()
	    total_reviews_for_score = tstr
            print 'total_reviews_for_score: %s' % total_reviews_for_score
        except Exception, e:
            print 'Error in getting total_reviews_for_score - %s' % (str(e))
	try:
            hotel_stars = soup.find('div', attrs={'id':'license-plate'}).find('span', attrs={'class':'visuallyhidden'}).text.lstrip().rstrip()
            print 'hotel_stars: %s' % hotel_stars
        except Exception, e:
            print 'Error in getting hotel_stars - %s' % (str(e))
	try:
	    links = soup.find('section', attrs={'class':'review-summary'}).find('div', attrs={'class':'rating-and-satisfaction'}).findAll('div')
            rating_overall = links[0].text.lstrip().rstrip()
            print 'rating_overall: %s' % rating_overall
        except Exception, e:
            print 'Error in getting rating_overall - %s' % (str(e))
	try:
            links = soup.find('section', attrs={'class':'review-summary'}).find('div', attrs={'class':'rating-and-satisfaction'}).findAll('div')
            recommendation_percentage = links[3].text.lstrip().rstrip()
            print 'recommendation_percentage: %s' % recommendation_percentage
        except Exception, e:
            print 'Error in getting recommendation_percentage - %s' % (str(e))
	try:
	    links = soup.find('section', attrs={'class':'review-summary'}).find('div', attrs={'class':'dimensions'}).findAll('div')
	    for link in links:
		tstr = link.text.lstrip().rstrip()
		if tstr.find('Room cleanliness') > 0:
		    rating_cleanliness = tstr[0:tstr.find('Room cleanliness')].lstrip().rstrip()
		    print 'rating_cleanliness: %s' % rating_cleanliness
		    continue
		if tstr.find('Service & staff') > 0:
                    rating_comfort = tstr[0:tstr.find('Service & staff')].lstrip().rstrip()
                    print 'rating_comfort: %s' % rating_comfort
                    continue
		if tstr.find('Room comfort') > 0:
                    rating_staff = tstr[0:tstr.find('Room comfort')].lstrip().rstrip()
                    print 'rating_staff: %s' % rating_staff
                    continue
		if tstr.find('Hotel condition') > 0:
                    rating_hotel_condition = tstr[0:tstr.find('Hotel condition')].lstrip().rstrip()
                    print 'rating_hotel_condition: %s' % rating_hotel_condition
                    continue
	except Exception, e:
	    'Error in getting rating_cleanliness / rating_comfort / etc - %s' % (str(e))
    except Exception, e:
	print 'URGENT - error in processing soup - %s' % (str(e))
	return
    try:
	overall.total_reviews_for_score = total_reviews_for_score
	overall.hotel_stars = hotel_stars
	overall.rating_overall = rating_overall
	overall.rating_cleanliness = rating_cleanliness
	overall.rating_comfort = rating_comfort
	overall.rating_staff = rating_staff
	overall.rating_hotel_condition = rating_hotel_condition
	overall.recommendation_percentage = recommendation_percentage
	print 'Try saving ExpediaOverallRating'
	overall.save()
	print 'ExpediaOverallRating updated'
    except Exception, e:
	print 'URGENT - Error in updating ExpediaOverallRating - %s' % (str(e))
    try:
        mongo_overall = MongoExpediaOverallRating()
        mentry = OrderedDict()
        mentry['hotel_id'] = hotel.hotel_id
        mentry['total_reviews_for_score'] = total_reviews_for_score
        mentry['hotel_stars'] = hotel_stars
        mentry['rating_overall'] = rating_overall
        mentry['rating_cleanliness'] = rating_cleanliness
        mentry['rating_comfort'] = rating_comfort
        mentry['rating_staff'] = rating_staff
        mentry['rating_hotel_condition'] = rating_hotel_condition
        mentry['recommendation_percentage'] = recommendation_percentage
        mentry['date_created'] = datetime.now()
        print 'Try saving MongoExpediaOverallRating'
        mongo_overall.add_params(mentry)
        mongo_overall.save()
        print 'MongoExpediaOverallRating updated'
    except Exception, e:
        print 'Error in updating MongoExpediaOverallRating - %s' % (str(e))
    return

## Read overall rating info from tripadvisor
def read_overall_tripadvisor(hotel, soup):
    print 'read_overall_tripadvisor %s' % hotel
    try:
	found = False
	curdate = datetime.now().date()
	overall = ''
	all = TripadvisorOverallRating.objects.filter(hotel=hotel).order_by('-date_created')
	for a in all:
	    if a.date_created.date() == curdate:
		found = True
		overall = a
		break
	if found == False:
	    overall = TripadvisorOverallRating.objects.create(hotel=hotel)
	    print 'New TripadvisorOverallRating created'
	if found == True:
	    print 'Existing TripadvisorOverallRating found'
	except Exception, e:
	print 'Error in getting TripadvisorOverallRating record - %s' % (str(e))
	return
    try:
	print 'processing soup'
	total_reviews = rating_overall = hotel_rank = rating_excellent = rating_very_good = rating_average = rating_poor = rating_terrible = for_families = for_couples = for_solo = for_business = for_friends = ''
	try:
            #total_reviews = soup.find('div', attrs={'class':'heading_ratings'}).find('a', attrs={'class':'more'}).text.lstrip().rstrip()
            total_reviews = soup.find('span', attrs={'class':'header_rating'}).find('a', attrs={'class':'more'}).text.lstrip().rstrip()
	    total_reviews = total_reviews.split(' ')[0]
            print 'total_reviews: %s' % total_reviews
        except Exception, e:
            print 'Error in getting total_reviews - %s' % (str(e))
	try:
            rating_overall = soup.find('span', attrs={'class':'header_rating'}).find('span', attrs={'class':'ui_bubble_rating'}).get('alt').lstrip().rstrip()
            print 'rating_overall: %s' % rating_overall
        except Exception, e:
            print 'Error in getting rating_overall - %s' % (str(e))
	try:
            hotel_rank = soup.find('div', attrs={'class':'rating_and_popularity'}).find('span', attrs={'class':'header_popularity'}).text.lstrip().rstrip()
            print 'hotel_rank: %s' % hotel_rank
        except Exception, e:
            print 'Error in getting hotel_rank - %s' % (str(e))
	try:
	    links = soup.find('div', attrs={'id':'ratingFilter'}).findAll('li')
	    for link in links:
		key = link.find('label').find('div', attrs={'class':'row_label'}).text.lstrip().rstrip()
		value = link.find('label').find('span', attrs={'class':None}).text.lstrip().rstrip()
		if key == 'Excellent':
		    rating_excellent = value
		    print 'rating_excellent: %s' % rating_excellent
		    continue
		if key == 'Very good':
		    rating_very_good = value
		    print 'rating_very_good: %s' % rating_very_good
		    continue
		if key == 'Average':
		    rating_average = value
		    print 'rating_average: %s' % rating_average
		    continue
		if key == 'Poor':
		    rating_poor = value
		    print 'rating_poor: %s' % rating_poor
		    continue
		if key == 'Terrible':
		    rating_terrible = value
		    print 'rating_terrible: %s' % rating_terrible
		    continue
	except Exception, e:
	    'Error in getting rating_excellent / rating_very_good / etc - %s' % (str(e))
	try:
            links = soup.find('div', attrs={'id':'filterControls'}).find('div', attrs={'class':'segment'}).findAll('li')
            for link in links:
                tstr = link.find('label').text.lstrip().rstrip()
		if tstr.find('Families') == 0:
		    tstr = tstr[len('Families'):].lstrip().rstrip()
		    if tstr.find('(') == 0:
			tstr = tstr[1:].lstrip().rstrip()
		    if tstr.find(')') > 0:
			tstr = tstr[0:tstr.find(')')].lstrip().rstrip()
		    for_families = tstr
		    print 'for_families: %s' % for_families
		    continue;
		if tstr.find('Couples') == 0:
                    tstr = tstr[len('Couples'):].lstrip().rstrip()
                    if tstr.find('(') == 0:
                        tstr = tstr[1:].lstrip().rstrip()
                    if tstr.find(')') > 0:
                        tstr = tstr[0:tstr.find(')')].lstrip().rstrip()
                    for_couples = tstr
		    print 'for_couples: %s' % for_couples
                    continue;
		if tstr.find('Solo') == 0:
                    tstr = tstr[len('Solo'):].lstrip().rstrip()
                    if tstr.find('(') == 0:
                        tstr = tstr[1:].lstrip().rstrip()
                    if tstr.find(')') > 0:
                        tstr = tstr[0:tstr.find(')')].lstrip().rstrip()
                    for_solo = tstr
		    print 'for_solo: %s' % for_solo
                    continue;
		if tstr.find('Business') == 0:
                    tstr = tstr[len('Business'):].lstrip().rstrip()
                    if tstr.find('(') == 0:
                        tstr = tstr[1:].lstrip().rstrip()
                    if tstr.find(')') > 0:
                        tstr = tstr[0:tstr.find(')')].lstrip().rstrip()
                    for_business = tstr
		    print 'for_business: %s' % for_business
                    continue;
		if tstr.find('Friends') == 0:
                    tstr = tstr[len('Friends'):].lstrip().rstrip()
                    if tstr.find('(') == 0:
                        tstr = tstr[1:].lstrip().rstrip()
                    if tstr.find(')') > 0:
                        tstr = tstr[0:tstr.find(')')].lstrip().rstrip()
                    for_friends = tstr
		    print 'for_friends: %s' % for_friends
                    continue;
        except Exception, e:
            'Error in getting for_families / for_couples / etc - %s' % (str(e))
    except Exception, e:
	print 'error in processing soup - %s' % (str(e))
	return
    try:
	overall.total_reviews = total_reviews
	overall.rating_overall = rating_overall
	overall.hotel_rank = hotel_rank
	overall.rating_excellent = rating_excellent
	overall.rating_very_good = rating_very_good
	overall.rating_average = rating_average
	overall.rating_poor = rating_poor
	overall.rating_terrible = rating_terrible
	overall.for_families = for_families
	overall.for_couples = for_couples
	overall.for_solo = for_solo
	overall.for_business = for_business
	overall.for_friends = for_friends
	print 'Try saving TripadvisorOverallRating'
	overall.save()
	print 'TripadvisorOverallRating updated'
    except Exception, e:
	print 'Error in updating TripadvisorOverallRating - %s' % (str(e))
    try:
        mongo_overall = MongoTripadvisorOverallRating()
        mentry = OrderedDict()
        mentry['hotel_id'] = hotel.hotel_id
        mentry['total_reviews'] = total_reviews
        mentry['hotel_rank'] = hotel_rank
        mentry['rating_excellent'] = rating_excellent
        mentry['rating_very_good'] = rating_very_good
        mentry['rating_average'] = rating_average
        mentry['rating_poor'] = rating_poor
        mentry['rating_terrible'] = rating_terrible
        mentry['for_families'] = for_families
        mentry['for_couples'] = for_couples
        mentry['for_solo'] = for_solo
        mentry['for_business'] = for_business
        mentry['for_friends'] = for_friends
        mentry['date_created'] = datetime.now()
        print 'Try saving MongoTripadvisorOverallRating'
        mongo_overall.add_params(mentry)
        mongo_overall.save()
        print 'MongoTripadvisorOverallRating updated'
    except Exception, e:
        print 'Error in updating MongoTripadvisorOverallRating - %s' % (str(e))
    return

def read_overall_hotelscom(hotel, soup):
    print 'read_overall_hotelscom %s' % hotel
    try:
	found = False
	curdate = datetime.now().date()
	overall = ''
	all = HotelsComOverallRating.objects.filter(hotel=hotel).order_by('-date_created')
	for a in all:
	    if a.date_created.date() == curdate:
		found = True
		overall = a
		break
	if found == False:
	    overall = HotelsComOverallRating.objects.create(hotel=hotel)
	    print 'NEW HotelsComOverallRating created'
	if found == True:
	    print 'EXISTING HotelsComOverallRating found'
    except Exception, e:
	print 'URGENT - Error in getting HotelsComOverallRating record - %s' % (str(e))
	return
    try:
	print 'processing soup'
	total_reviews = hotel_stars = reviews_with_5_star = reviews_with_4_star = reviews_with_3_star = reviews_with_2_star = reviews_with_1_star = total_reviews_business = total_reviews_romance = total_reviews_family = total_reviews_friends = total_reviews_other = rating_overall = rating_location = rating_location_text = rating_cleanliness = rating_cleanliness_text = rating_service = rating_service_text = rating_room = rating_room_text = rating_comfort = rating_comfort_text = rating_vibe = rating_vibe_text = ''
	try:
            hotel_stars = soup.find('div', attrs={'class':'property-description'}).find('span',attrs={'class':'star-rating-text'}).find('span').text.lstrip().rstrip()
            print 'hotel_stars: %s' % hotel_stars
        except Exception, e:
            print 'Error in getting hotel_stars - %s' % (str(e))

	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-all'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
	    total_reviews = tstr
            print 'total_reviews: %s' % total_reviews
        except Exception, e:
            print 'Error in getting total_reviews - %s' % (str(e))
	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-business'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
            total_reviews_business = tstr
            print 'total_reviews_business: %s' % total_reviews_business
        except Exception, e:
            print 'Error in getting total_reviews_business - %s' % (str(e))
	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-romance'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
            total_reviews_romance = tstr
            print 'total_reviews_romance: %s' % total_reviews_romance
        except Exception, e:
            print 'Error in getting total_reviews_romance - %s' % (str(e))
	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-family'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
            total_reviews_family = tstr
            print 'total_reviews_family: %s' % total_reviews_family
        except Exception, e:
            print 'Error in getting total_reviews_family - %s' % (str(e))
	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-with-friends'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
            total_reviews_friends = tstr
            print 'total_reviews_friends: %s' % total_reviews_friends
        except Exception, e:
            print 'Error in getting total_reviews_friends - %s' % (str(e))
	try:
            tstr = soup.find('div', attrs={'class':'reviews-summary'}).find('li',attrs={'class':'tt-other'}).find('span').text.lstrip().rstrip()
	    tstr = tstr.lstrip('(').rstrip(')')
            total_reviews_other = tstr
            print 'total_reviews_other: %s' % total_reviews_other
        except Exception, e:
            print 'Error in getting total_reviews_other - %s' % (str(e))

	try:
	    li_list = soup.find('div', attrs={'class':'reviews-summary'}).find('div',attrs={'class':'overall'}).find('ul', attrs={'class':'scores'}).findAll('li')
	    for li in li_list:
		if li.find('a',attrs={'data-score-key':'5.0'}):
		    tstr = li.find('a',attrs={'data-score-key':'5.0'}).text.lstrip().rstrip()
		    tstr = tstr.lstrip('(').rstrip(')')
		    reviews_with_5_star = tstr
		    continue
		if li.find('a',attrs={'data-score-key':'4.0'}):
		    tstr = li.find('a',attrs={'data-score-key':'4.0'}).text.lstrip().rstrip()
		    tstr = tstr.lstrip('(').rstrip(')')
		    reviews_with_4_star = tstr
		    continue
		if li.find('a',attrs={'data-score-key':'3.0'}):
		    tstr = li.find('a',attrs={'data-score-key':'3.0'}).text.lstrip().rstrip()
		    tstr = tstr.lstrip('(').rstrip(')')
		    reviews_with_3_star = tstr
		    continue
		if li.find('a',attrs={'data-score-key':'2.0'}):
		    tstr = li.find('a',attrs={'data-score-key':'2.0'}).text.lstrip().rstrip()
		    tstr = tstr.lstrip('(').rstrip(')')
		    reviews_with_2_star = tstr
		    continue
		if li.find('a',attrs={'data-score-key':'1.0'}):
		    tstr = li.find('a',attrs={'data-score-key':'1.0'}).text.lstrip().rstrip()
		    tstr = tstr.lstrip('(').rstrip(')')
		    reviews_with_1_star = tstr
		    continue
            print 'reviews_with_5_star: %s' % reviews_with_5_star
            print 'reviews_with_4_star: %s' % reviews_with_4_star
            print 'reviews_with_3_star: %s' % reviews_with_3_star
            print 'reviews_with_2_star: %s' % reviews_with_2_star
            print 'reviews_with_1_star: %s' % reviews_with_1_star
        except Exception, e:
            print 'Error in getting reviews_with_stars - %s' % (str(e))

	try:
            rating_overall = soup.find('div', attrs={'class':'reviews-summary'}).find('div',attrs={'class':'overall'}).find('div', attrs={'class':'overall-score'}).find('span').text.lstrip().rstrip()
            print 'rating_overall: %s' % rating_overall
        except Exception, e:
            print 'Error in getting rating_overall - %s' % (str(e))

	try:
            li_list = soup.find('div', attrs={'class':'reviews-summary'}).find('div',attrs={'class':'overall'}).find('div', attrs={'class':'trust-you-reviews'}).find('ul').findAll('li')
            for li in li_list:
                if li.find('div',attrs={'title':'Location'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_location = tstr
                    rating_location_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
                if li.find('div',attrs={'title':'Cleanliness'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_cleanliness = tstr
                    rating_cleanliness_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
                if li.find('div',attrs={'title':'Service'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_service = tstr
                    rating_service_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
                if li.find('div',attrs={'title':'Room'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_room = tstr
                    rating_room_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
                if li.find('div',attrs={'title':'Comfort'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_comfort = tstr
                    rating_comfort_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
                if li.find('div',attrs={'title':'Vibe'}):
                    tstr = li.find('div',attrs={'class':'score-bar'}).find('div',attrs={'class':'amount'}).get('style').lstrip().rstrip()
                    tstr = tstr.lstrip('width:').rstrip(';')
                    rating_vibe = tstr
                    rating_vibe_text = li.find('span',attrs={'class':'review-text'}).text.lstrip().rstrip()
                    continue
            print 'rating_location: %s' % rating_location
            print 'rating_location_text: %s' % rating_location_text
            print 'rating_cleanliness: %s' % rating_cleanliness
            print 'rating_cleanliness_text: %s' % rating_cleanliness_text
            print 'rating_service: %s' % rating_service
            print 'rating_service_text: %s' % rating_service_text
            print 'rating_room: %s' % rating_room
            print 'rating_room_text: %s' % rating_room_text
            print 'rating_comfort: %s' % rating_comfort
            print 'rating_comfort_text: %s' % rating_comfort_text
            print 'rating_vibe: %s' % rating_vibe
            print 'rating_vibe_text: %s' % rating_vibe_text
        except Exception, e:
            print 'Error in getting reviews_* - %s' % (str(e))

    except Exception, e:
	print 'URGENT - error in processing soup - %s' % (str(e))
	return
    try:
	overall.total_reviews = total_reviews
	overall.hotel_stars = hotel_stars
	overall.reviews_with_5_star = reviews_with_5_star
	overall.reviews_with_4_star = reviews_with_4_star
	overall.reviews_with_3_star = reviews_with_3_star
	overall.reviews_with_2_star = reviews_with_2_star
	overall.reviews_with_1_star = reviews_with_1_star
	overall.total_reviews_business = total_reviews_business
	overall.total_reviews_romance = total_reviews_romance
	overall.total_reviews_family = total_reviews_family
	overall.total_reviews_friends = total_reviews_friends
	overall.total_reviews_other = total_reviews_other
	overall.rating_overall = rating_overall
	overall.rating_location = rating_location
	overall.rating_location_text = rating_location_text
	overall.rating_cleanliness = rating_cleanliness
	overall.rating_cleanliness_text = rating_cleanliness_text
	overall.rating_service = rating_service
	overall.rating_service_text = rating_service_text
	overall.rating_room = rating_room
	overall.rating_room_text = rating_room_text
	overall.rating_comfort = rating_comfort
	overall.rating_comfort_text = rating_comfort_text
	overall.rating_vibe = rating_vibe
	overall.rating_vibe_text = rating_vibe_text
	print 'Try saving HotelsComOverallRating'
	overall.save()
	print 'HotelsComOverallRating updated'
    except Exception, e:
	print 'URGENT - Error in updating HotelsComOverallRating - %s' % (str(e))
    try:
        mongo_overall = MongoHotelscomOverallRating()
        mentry = OrderedDict()
        mentry['hotel_id'] = hotel.hotel_id
	mentry['total_reviews'] = total_reviews
        mentry['hotel_stars'] = hotel_stars
        mentry['reviews_with_5_star'] = reviews_with_5_star
        mentry['reviews_with_4_star'] = reviews_with_4_star
        mentry['reviews_with_3_star'] = reviews_with_3_star
        mentry['reviews_with_2_star'] = reviews_with_2_star
        mentry['reviews_with_1_star'] = reviews_with_1_star
        mentry['total_reviews_business'] = total_reviews_business
        mentry['total_reviews_romance'] = total_reviews_romance
        mentry['total_reviews_family'] = total_reviews_family
        mentry['total_reviews_friends'] = total_reviews_friends
        mentry['total_reviews_other'] = total_reviews_other
        mentry['rating_overall'] = rating_overall
        mentry['rating_location'] = rating_location
        mentry['rating_location_text'] = rating_location_text
        mentry['rating_cleanliness'] = rating_cleanliness
        mentry['rating_cleanliness_text'] = rating_cleanliness_text
        mentry['rating_service'] = rating_service
        mentry['rating_service_text'] = rating_service_text
        mentry['rating_room'] = rating_room
        mentry['rating_room_text'] = rating_room_text
        mentry['rating_comfort'] = rating_comfort
        mentry['rating_comfort_text'] = rating_comfort_text
        mentry['rating_vibe'] = rating_vibe
        mentry['rating_vibe_text'] = rating_vibe_text
        mentry['date_created'] = datetime.now()
        print 'Try saving MongoHotelscomOverallRating'
        mongo_overall.add_params(mentry)
        mongo_overall.save()
        print 'MongoHotelscomOverallRating updated'
    except Exception, e:
        print 'Error in updating MongoHotelscomOverallRating - %s' % (str(e))
    return

def helper_scrape_expedia_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'helper_scrape_expedia_by_hotel_id: uid(%s) - url(%s) - follownext(%s) - firstrun(%s) - ischained(%s) - overall(%s)' % (uid, inputurl, follownext, firstrun, ischained, overall)
    source = 'expedia'
    sourceid = 4
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel

        try:
	    if inputurl is None:
		inputurl = hotel.expedia_url
	    print 'inputurl: %s' % inputurl
	    if len(inputurl) == 0:
		print 'Invalid input url. Returning...'
		hotel.is_expedia_update_running = False
		hotel.expedia_last_update_status = 'url is empty.'
		hotel.expedia_last_update_date = datetime.now()
                hotel.save()
                return
	    try:
		args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':2 }
		data_server_url = 'http://{0}/q/'.format(DATA_SERVER_2_APACHE)
		print 'data_server_url: %s' % (data_server_url)
		connect_timeout, read_timeout = 5.0, 20.0
		response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
		page = response.content

		soup = BeautifulSoup(page, "html5lib")
		print 'title: %s' % soup.find('h1', attrs={'id':'hotel-name'}).text.lstrip().rstrip()
		nexturl = ''
		if overall == True:
                    read_overall_expedia(hotel, soup)
                    overall = False
		try:
		    inreviews = soup.find('section', attrs={'id':'reviews'}).findAll('article', attrs={'class':'segment'})
		    if len(inreviews) == 0:
			print 'No reviews found. Not a valid page. Returning...'
			hotel.expedia_last_update_status = 'Invalid url.'
			hotel.is_expedia_update_running = False
			hotel.expedia_last_update_date = datetime.now()
        		hotel.save()
			return
		    print 'inreviews len: %s' % (len(inreviews))
		    for inreview in inreviews:
			response_data = {}
			reviewid = rating = title = review_text = review_pos = review_neg = review_location = review_date = review_date_format = review_dt = ''
			reviewer_name = reviewer_location = reviewer_recommendation = ''
			manager_response_text = manager_response_date = manager_response_date_format = manager_response_dt = ''
			has_manager_response = False
			try:
			    rating = inreview.find('div', attrs={'class':'summary'}).find('span', attrs={'class':'rating'}).text.lstrip().rstrip()
			    print 'rating: %s' % rating
			except Exception, e:
			    print 'Error in getting rating - %s' %(str(e))
			try:
			    tstr = inreview.find('div', attrs={'class':'summary'}).find('div', attrs={'class':'user'}).text.lstrip().rstrip()
			    print tstr
			    if tstr.find('from') > 0:
				tlist = tstr.split('from')
				if len(tlist) >= 2:
				    reviewer_name = tlist[0].lstrip().rstrip()
				    reviewer_location = tlist[1].lstrip().rstrip()
				else:
				    reviewer_name = tstr
			    else:
				reviewer_name = tstr
			    print 'reviewer_name: %s' % reviewer_name
			    print 'reviewer_location: %s' % reviewer_location
			except Exception, e:
			    print 'Error in getting reviewer info - %s' %(str(e))
			try:
			    reviewer_recommendation = inreview.find('div', attrs={'class':'summary'}).find('span', attrs={'class':'icon'}).text.lstrip().rstrip()
			    print 'reviewer_recommendation: %s' % reviewer_recommendation
			except Exception, e:
			    print 'Error in getting reviewer_recommendation - %s' %(str(e))
			try:
			    title = inreview.find('div', attrs={'class':'details'}).find('h3').text.lstrip().rstrip()
			    print 'title: %s' % title
			except Exception, e:
			    print 'Error in getting title - %s' %(str(e))
			try:
			    tstr = inreview.find('div', attrs={'class':'details'}).find('span', attrs={'class':'date-posted'}).text.lstrip().rstrip()
			    print tstr
			    if tstr.find(',') > 0: #Posted Aug 15, 2015 on Hotels
                    		if tstr.find('on') > 0:
                        	    tstr = tstr.split('on')[0].lstrip().rstrip()
                    		review_date_format = "fm2" # Aug 15, 2015
                    		tarr = tstr.split('Posted') #Remove Posted
                    		if len(tarr) >= 2:
                        	    review_date = tarr[1].lstrip().rstrip()
                	    else:
                    		if tstr.find('on') > 0:
                        	    tstr = tstr.split('on')[0].lstrip().rstrip()
                    		review_date_format = "fm1"; #07-Jul-2011
                    		tarr = tstr.split(' ') #Remove Posted
                    		if len(tarr) >= 2:
                        	    review_date = tarr[1].lstrip().rstrip()
			    print 'review_date: %s' % review_date
			    print 'review_date_format: %s' % review_date_format
			    if review_date_format == "fm1": #06-Mar-2015
                		try:
                    		    tlist =  review_date.split("-")
                    		    if len(tlist) == 3:
                        		tstr = tlist[2] + "-" + tlist[1] + "-" + tlist[0].rstrip(',')
                        		print tstr
                        		review_dt = datetime.strptime(tstr, '%Y-%b-%d')
                        		print review_dt
                		except Exception, e:
                    		    print 'Error in review date coversion fm1  - %s' %(str(e))
			    if review_date_format == "fm2": #Aug 18, 2015
                                try:
                                    tlist =  review_date.split(" ")
                                    if len(tlist) == 3:
                                        tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                                        print tstr
                                        review_dt = datetime.strptime(tstr, '%Y-%b-%d')
                                        print review_dt
                                except Exception, e:
                                    print 'Error in review date coversion fm2 - %s' %(str(e))
			    print 'review_dt: %s' % review_dt
			    try:
                                if firstrun == False: #update
                                    if hotel.expedia_update_window is None:
                                        dt_threshold = datetime.now() - timedelta(days=30)
                                    else:
                                        dt_threshold = datetime.now() - timedelta(days=int(hotel.expedia_update_window))
				    print 'spl dt_threshold: %s' % dt_threshold
                                    if review_dt >= dt_threshold:
                                        print 'REVIEW FOUND in update window'
                                    else:
                                        print 'BEYOND UPDATE WINDOW. RETURNING...'
                                        hotel.is_expedia_update_running = False
					hotel.expedia_last_update_status = ''
					hotel.expedia_last_update_date = datetime.now()
                                        hotel.save()
                                        return
                            except Exception, e:
                                print 'URGENT Error in check dt_threshold for update. Returning...- %s' %(str(e))
                                hotel.is_expedia_update_running = False
				hotel.expedia_last_update_status = 'Error in check dt_threshold for update.'
				hotel.expedia_last_update_date = datetime.now()
                                hotel.save()
                                return
			except Exception, e:
			    print 'Error in getting review date - %s' %(str(e))
			try:
                            remarks = inreview.find('div', attrs={'class':'details'}).findAll('div', attrs={'class':'remark'})
			    for remark in remarks:
				tstr = remark.text.lstrip().rstrip()
				if tstr.find('Pros') == 0:
				    review_pos = tstr[len('Pros:'):].lstrip().rstrip()
			    	    review_pos = review_pos.replace('[strong]','')
			    	    review_pos = review_pos.replace('[/strong]','')
				if tstr.find('Cons') == 0:
				    review_neg = tstr[len('Cons:'):].lstrip().rstrip()
			    	    review_neg = review_neg.replace('[strong]','')
			    	    review_neg = review_neg.replace('[/strong]','')
				if tstr.find('Location') == 0:
				    review_location = tstr[len('Location:'):].lstrip().rstrip()
			    	    review_location = review_location.replace('[strong]','')
			    	    review_location = review_location.replace('[/strong]','')
			    print 'review_pos: %s' % review_pos
			    print 'review_neg: %s' % review_neg
			    print 'review_location: %s' % review_location
                        except Exception, e:
                            print 'Error in getting remarks - %s' % (str(e))
			try:
                            review_text = inreview.find('div', attrs={'class':'details'}).find('div', attrs={'class':'review-text'}).text.lstrip().rstrip()
			    review_text = review_text.replace('[strong]','')
			    review_text = review_text.replace('[/strong]','')
                            print 'review_text: %s' % review_text
                        except Exception, e:
                            print 'Error in getting review_text - %s' % (str(e))
			try:
                            tstr = inreview.find('div', attrs={'class':'details'}).find('div', attrs={'class':'management-response'}).find('div', attrs={'class':'date-posted'}).text.lstrip().rstrip()
                            print tstr
			    if tstr.find(' by ') > 0:
				tlist = tstr.split('by')
				if len(tlist) == 2:
				    manager_response_date = tlist[0].lstrip().rstrip()
				    if manager_response_date.find('-') > 0:
					manager_response_date_format = "fm1"
				    else:
					manager_response_date_format = "fm2"
				    has_manager_response = True

			    print 'manager_response_date: %s' % manager_response_date
			    print 'manager_response_date_format: %s' % manager_response_date_format
			    if manager_response_date_format == "fm1": #06-Mar-2015
                                try:
                                    tlist =  manager_response_date.split("-")
                                    if len(tlist) == 3:
                                        tstr = tlist[2] + "-" + tlist[1] + "-" + tlist[0].rstrip(',')
                                        print tstr
                                        manager_response_dt = datetime.strptime(tstr, '%Y-%b-%d')
                                        print manager_response_dt
                                except Exception, e:
                                    print 'Error in review date coversion fm1 - %s' % (str(e))
                            if manager_response_date_format == "fm2": #Aug 18, 2015
                                try:
                                    tlist =  manager_response_date.split(" ")
                                    if len(tlist) == 3:
                                        tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                                        print tstr
                                        manager_response_dt = datetime.strptime(tstr, '%Y-%b-%d')
                                        print manager_response_dt
                                except Exception, e:
                                    print 'Error in review date coversion fm2 - %s' % (str(e))
			    print 'manager_response_dt: %s' % manager_response_dt
                        except Exception, e:
                            print 'Error in getting management response - %s' % (str(e))
			try:
                            manager_response_text = inreview.find('div', attrs={'class':'details'}).find('div', attrs={'class':'management-response'}).find('div', attrs={'class':'text'}).text.lstrip().rstrip()
                            print 'manager_response_text: %s' % manager_response_text
                        except Exception, e:
                            print 'Error in getting manager_response_text - %s' % (str(e))
			response_data['rating'] = rating
			response_data['title'] = title
			response_data['review_pos'] = review_pos
			response_data['review_neg'] = review_neg
			response_data['review_location'] = review_location
			response_data['review_text'] = review_text
			response_data['review_date'] = review_date
			response_data['review_date_format'] = review_date_format
			response_data['reviewer_name'] = reviewer_name
			response_data['reviewer_location'] = reviewer_location
			response_data['has_manager_response'] = has_manager_response
			response_data['manager_response_date'] = manager_response_date
			response_data['manager_response_date_format'] = manager_response_date_format
			response_data['manager_response_text'] = manager_response_text

			try:
			    reviewid = review_dt.strftime('%Y%m%d')
			    print 'reviewid: %s' % reviewid
			except Exception, e:
			    print 'Error in making reviewid. Skipping... - %s' % (str(e))
			    continue

			print 'response_data: %s' % (response_data)

			try:
			    create = False
			    update = False
			    print 'Check in DB for the review'
			    reviewid = hotel.identifier + '_' + reviewid
			    print 'reviewid: %s' % reviewid
			    spl_title = title.replace(' ', '')[0:3]
			    spl_title = ''.join(e for e in spl_title if e.isalnum())
			    spl_text = review_text.replace(' ', '')[0:3]
			    spl_text = ''.join(e for e in spl_text if e.isalnum())
			    reviewid = reviewid + '#' + rating.replace(' ', '') + '#' + spl_title + '#' + spl_text
			    print 'reviewid: %s' % reviewid

			    # UPDATE MONGODB
			    try:
				upserted_review_id = None
        			mongo_review = MongoReview()
				find_param = {}
				find_param['identifier'] = reviewid
				find_param['hotel_id'] = hotel.hotel_id
				find_param['source'] = 4 #Expedia
				find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
        			update_param = OrderedDict()
				find_count = mongo_review.count(find_param)
				if find_count == 0:
				    print 'create new expedia MongoReview'
        			    update_param['_id'] = uuid.uuid4().hex[:16].lower()
				else:
				    print 'existing expedia MongoReview found'
        			update_param['title'] = title
        			update_param['comment'] = review_text
        			update_param['comment_negative'] = review_neg
        			update_param['comment_pro'] = review_pos
        			update_param['comment_location'] = review_location
        			update_param['rating'] = rating
        			rating_number = convert_rating_to_number_expedia(rating)
        			update_param['rating_number'] = rating_number
        			update_param['rating_out_of_5'] = rating_number
				author = {}
				author['name'] = reviewer_name
				author['location'] = reviewer_location
        			update_param['author'] = author
				if isinstance(review_dt, datetime):
        			    update_param['review_date'] = review_dt
				else:
				    print 'expedia No review_date'
				    alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('expedia', hotel.hotel_id, reviewid, title, reviewer_name)
				    mongo_log_alert(type='scrape', info=alert_msg)
        			update_param['has_manager_response'] = has_manager_response
				if isinstance(manager_response_dt, datetime):
        			    update_param['manager_response_date'] = manager_response_dt
        			update_param['manager_response'] = manager_response_text
				if find_count == 0:
        			    update_param['date_created'] = datetime.now()
				else:
        			    update_param['date_updated'] = datetime.now()
        			print 'Try saving expedia MongoReview'
        			mongo_review.set_find_param(find_param)
				print 'try setting update_param'
        			mongo_review.set_update_param(update_param)
        			mongo_result = mongo_review.update()
				if mongo_result:
				    upserted_review_id = mongo_result.upserted_id
				    print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
				    print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
				    print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
        			print 'expedia MongoReview updated'
    			    except Exception, e:
        			print 'Error in updating expedia MongoReview - %s' % (str(e))

			    # UPDATE POSTGRES
			    reviews = Review.objects.filter(identifier=reviewid, source=4, hotel=hotel, is_unavailable=False).order_by('-date_created')
			    print 'reviews len: %s' % len(reviews)
			    if len(reviews) == 0:
				create = True
			    else:
				print ' exisiting review found.'
			    	print 'reviews len: %s' % len(reviews)
				if len(reviews) > 1:
                                    print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
				review = reviews[0]
				update = True
				print 'update set to True'
			    if create == True:
                                print 'CREATING new reviewer and review'
                                reviewer = Reviewer.objects.create(source=sourceid)
				if len(reviewer_name) > 0:
				    reviewer.name = reviewer_name
				    reviewer.location = reviewer_location
				    try:
				  	reviewer.save()
					print 'Reviewer saved successfully'
					review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
					review.title = title
					review.comment = review_text
					review.comment_negative = review_neg
					review.comment_pro = review_pos
					review.comment_location = review_location
					review.rating = rating
					try:
					    if isinstance(review_dt, datetime):
					        review.review_date = review_dt
					    else:
						print 'ERROR review_dt missing'
					except Exception, e:
					    print 'Error in review_dt assignment - %s' % (str(e))
					review.has_manager_response = has_manager_response
					review.response_posted_checkbox = False
					review.is_non_english = False
					review.partial = False
					try:
					    if isinstance(manager_response_dt, datetime):
					        review.manager_response_date = manager_response_dt
					    else:
						print 'manager_response_dt missing'
					except Exception, e:
					    print 'Error in manager_response_dt assignment - %s' % (str(e))
					review.manager_response = manager_response_text
					try:
					    review.save()
					    print 'review saved'

					    #Update review_id in mongodb
					    if upserted_review_id:
					        try:
					            print 'Update review_id %s' % (review.review_id)
						    mongo_review = MongoReview()
                                		    find_param = {}
                                		    find_param['_id'] = upserted_review_id
						    update_param = {}
						    update_param['review_id'] = review.review_id
						    print 'Try saving review_id expedia MongoReview'
                                		    mongo_review.set_find_param(find_param)
                                		    print 'try setting review_id update_param'
                                		    mongo_review.set_update_param(update_param)
                                		    mongo_result = mongo_review.update()
                                		    if mongo_result:
                                    			print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                    			print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                    			print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                			print 'expedia MongoReview review_id updated'
					        except Exception, e:
						    print 'Error in updating review_id in mongodb: %s' % (str(e))
					    else:
					    	print 'upserted_review_id is None'

					except Exception, e:
					    print 'Error in executing save of review - new record. Skipping..  - %s' % (str(e))
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    continue
				    except Exception, e:
					print 'Erorr in saving reviewer and review. Skipping - %s' % (str(e))
					try:
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					except Exception, e:
					    print 'Errro in deleting reviewer, may be it doesnt exists - %s' % (str(e))
					continue
			    else:
				if update == True:
				    print 'UPDATING existing one....'
				    review.title = title
				    review.comment = review_text
				    review.comment_negative = review_neg
				    review.comment_pro = review_pos
				    review.comment_location = review_location
				    review.rating = rating
				    try:
					if isinstance(review_dt, datetime):
					    review.review_date = review_dt
					else:
					    print 'ERROR review_dt missing'
				    except Exception, e:
					print 'Error in review_dt assignment - %s' % (str(e))
				    review.has_manager_response = has_manager_response
				    try:
					if isinstance(manager_response_dt, datetime):
					    review.manager_response_date = manager_response_dt
					else:
					    print 'manager_response_dt missing'
				    except Exception, e:
					print 'Error in manager_response_dt assignment - %s' % (str(e))
				    review.manager_response = manager_response_text
				    try:
					review.save()
					print 'review updated'
				    except Exception, e:
					print 'Error in executing save of review - existing record. Skipping.. - %s' % (str(e))
					continue

			except Exception, e:
			    print 'Error in checking in DB for the review. Skipping... - %s' % (str(e))
			    continue

		    #End of for


		except Exception, e:
		    print 'Error in processing reviews - %s' % (str(e))
		try:
		    print 'Check for next url'
		    nexturl = soup.find('span', attrs={'id':'pagination-control'}).find('a', attrs={'id':'next-page-button'}).get('href')
		    nexturl = nexturl.lstrip().rstrip()
		    print 'nexturl: %s' % nexturl
		except Exception, e:
		    print 'Error in getting nexturl - %s' % (str(e))

		if firstrun == False and follownext == False:
		    hotel.is_expedia_update_running = False
		    hotel.expedia_last_update_status = ''
		    hotel.expedia_last_update_date = datetime.now()
        	    hotel.save()
		    return
		if len(nexturl) > 0:
		    print 'Queue the next page'
		    try:
			timedelay = random.randrange(5,10)
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
                        args = {'args': [timedelay, uid, nexturl, follownext, firstrun, ischained, overall]}
                        url = '{}/async-apply/scrape.tasks.task_wrapper_expedia_by_hotel_id'.format(task_api)
                        print url
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'task post status code: %s' % (resp.status_code)
        		hotel.is_expedia_update_running = True
                    except Exception, e:
                        print 'Error in making celery web request - %s' % (str(e))
       			hotel.is_expedia_update_running = False
        		hotel.expedia_last_update_status = 'Error in making celery web request'
        		hotel.expedia_last_update_date = datetime.now()
        		hotel.save()
			return
		else:
        	    hotel.is_expedia_update_running = False

                hotel.expedia_last_update_status = ''
	    except Exception, e:
		print 'Error in making soup - %s' % (str(e))
        	hotel.is_expedia_update_running = False
                hotel.expedia_last_update_status = 'e1 - {0}'.format(str(e))
	except Exception, e:
	    print 'Error in processing hotel - %s' % (str(e))
       	    hotel.is_expedia_update_running = False
            hotel.expedia_last_update_status = 'e2 - {0}'.format(str(e))
        hotel.expedia_last_update_date = datetime.now()
        hotel.save()
	return
    except Exception, e:
	print 'Error in helper_scrape_expedia_by_hotel_id - %s' % (str(e))
       	hotel.is_expedia_update_running = False
        hotel.expedia_last_update_status = 'error in helper_scrape_expedia_by_hotel_id'
        hotel.expedia_last_update_date = datetime.now()
        hotel.save()
	return

#Booking Scrape
#Compile the reviewlist url from main booking page for each location
def helper_scrape_booking_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'helper_scrape_booking_hotel_id: %s - %s - %s - %s - %s - %s' % (uid, inputurl, follownext, firstrun, ischained, overall)
    source = 'booking'
    sourceid = 3
    country_code = 'us'
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
	#hotel.is_booking_update_running = True
	#hotel.save()
        try:
	    if inputurl is None:
		inputurl = hotel.booking_url
	    print 'inputurl: %s' % inputurl
	    if len(inputurl) == 0:
		print 'Invalid input url. Returning...'
		hotel.booking_last_update_status = 'url missing'
		hotel.is_booking_update_running = False
		hotel.booking_last_update_date = datetime.now()
                hotel.save()
                return
	    #get the country code
	    try:
		clist = inputurl.split('/')
		if len(clist) >= 6:
		    country_code = clist[4]
		    print 'country_code: %s' % (country_code)
	    except Exception, e:
		print 'URGENT - Error in getting country code - %s' % (str(e))
	    print 'country_code: %s' % (country_code)
	    try:
		# m(1) - requests / m(2) - urllib2
		#args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':1 }
                #data_server_url = 'http://{0}/q/'.format(DATA_SERVER_1)
		args = { 'auth' :'zc3wiu4e6z1nwgye', 'q': inputurl}
                data_server_url = 'http://{0}/bnuy6vwh89enjkyo/'.format(DATA_SERVER_2)
                print 'data_server_url: %s' % (data_server_url)
                connect_timeout, read_timeout = 5.0, 20.0
                response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
		print response.url
                page = response.content

	        #ua_string = ua_list[random.randrange(0,len(ua_list))]
		#print 'user agent: %s' % (ua_string)
		#headers = {'User-Agent': ua_string}
		#response = requests.get(inputurl, headers=headers)
		#html = response.content
		soup = BeautifulSoup(page, "html5lib")

		#if response.status_code != 200:
		#    print 'URGENT - Response code %s' % (response.status_code)
		#    hotel.is_booking_update_running = False
		#    hotel.save()
		#    return
		#url = 'http://www.booking.com/hotel/us/la-mesa-7475-el-cajon-boulevard.en-gb.html'
		#pagename = 'la-mesa-7475-el-cajon-boulevard'

		# Get booking_hotel_id
		try:
		    booking_hotel_id = str(soup.find('input',attrs={'name':'hotel_id'}).get('value').lstrip().rstrip())
		    print '# booking_hotel_id: %s' % (booking_hotel_id)
		    hotel.booking_hotel_id = booking_hotel_id
                    hotel.save()
		except Exception, e:
		    print 'Error in getting and updating booking_hotel_id: %s' % (str(e))

		pagename = ''
		try:
		    if inputurl.find('.com/hotel/') > 0:
		        tstr = inputurl[inputurl.find('.com/hotel/')+len('.com/hotel/'):]
		        tarr = tstr.split('/')
		        if len(tarr) >= 2:
			    pagename = tarr[1]
			    if pagename.find('.') > 0:
				pagename = pagename[:pagename.find('.')]
		except Exception, e:
		    print 'URGENT - Error in getting pagename - %s' % (str(e))
		    pagename = ''
		if len(pagename) == 0:
		    print 'URGENT - pagename missing'
                    hotel.is_booking_update_running = False
		    hotel.booking_last_update_status = 'pagename missing in soup'
                    hotel.booking_last_update_date = datetime.now()
                    hotel.save()
                    return
		print 'pagename: %s' % (pagename)
		topurl = ''
		try:
		    topurl = soup.find('div', attrs={'id':'top'}).find('a').get('href')
		except Exception, e:
		    print 'URGENT - Error in getting topurl - %s' % (str(e))
		if len(topurl) == 0:
		    print 'URGENT - topurl missing'
		    hotel.is_booking_update_running = False
		    hotel.booking_last_update_status = 'topurl missing in soup'
                    hotel.booking_last_update_date = datetime.now()
                    hotel.save()
                    return
		print 'topurl: %s' % (topurl)
		url_p1 = ''
		if topurl.find('label=') > 0:
		    topurl = topurl[topurl.find('label='):]
		    if topurl.find('click_from_logo=') > 0:
			url_p1 = topurl[:topurl.find('click_from_logo=')]
		if len(url_p1) == 0:
                    print 'URGENT - label sid missing'
                    hotel.is_booking_update_running = False
		    hotel.booking_last_update_status = 'label sid missing in soup'
                    hotel.booking_last_update_date = datetime.now()
                    hotel.save()
                    return
		print 'url_p1: %s' % (url_p1)
		#review_url = 'http://www.booking.com/reviewlist.en-gb.html?{0}pagename={1};cc1={2};type=total;dist=1;offset=0;rows=10;r_lang=en;'.format(url_p1, pagename, country_code)
		review_url = 'http://www.booking.com/reviewlist.en-gb.html?{0}pagename={1};cc1={2};type=total;dist=1;offset=0;rows=10;r_lang=en;sort=f_recent_desc;'.format(url_p1, pagename, country_code)
		#review_url = 'http://www.booking.com/reviewlist.en-gb.html?pagename={0};cc1={1};type=total;dist=1;offset=0;rows=10;r_lang=en;'.format(pagename, country_code)
		print 'review_url: %s' % (review_url)
		if len(review_url) > 0:
		    try:
			timedelay = random.randrange(13,15)
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
                        args = {'args': [timedelay, uid, review_url, follownext, firstrun, ischained, overall]}
                        url = '{}/async-apply/scrape.tasks.task_wrapper_booking_by_reviewlist_url'.format(task_api)
                        print url
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'task post status code: %s' % (resp.status_code)
                    except Exception, e:
                        print 'Error in making celery web request for reviews scrape - %s' % (str(e))
		        hotel.is_booking_update_running = False
		        hotel.booking_last_update_status = 'error in queuing review url'
                        hotel.booking_last_update_date = datetime.now()
		        hotel.save()
		        return
		else:
		    print 'URGENT - review url is missing'
		    hotel.is_booking_update_running = False
		    hotel.booking_last_update_status = 'review url is missing'
                    hotel.booking_last_update_date = datetime.now()
		    hotel.save()
		    return
		try:
		    tstr = soup.find('a', attrs={'class':'show_all_reviews_btn'}).get('href')
		    rating_page_url = 'http://www.booking.com{0}'.format(tstr)
		    print 'rating_page_url: %s' % (rating_page_url)
		    try:
                        timedelay = random.randrange(2,5)
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
                        args = {'args': [timedelay, uid, rating_page_url]}
                        url = '{}/async-apply/scrape.tasks.task_wrapper_booking_overall_hotel'.format(task_api)
                        print url
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'task post status code: %s' % (resp.status_code)
                    except Exception, e:
                        print 'URGENT - Error in making celery web request for overall rating scrape - %s' % (str(e))
		except Exception, e:
		    print 'Error in getting overall ratings page url - %s' % (str(e))
	    except Exception, e:
		print 'Error in making soup for main url(%s) - %s' % (inputurl, str(e))
		hotel.is_booking_update_running = False
                hotel.booking_last_update_status = 'error in making soup'
        except Exception, e:
            print 'Error in processing hotel - %s' % (str(e))
	    hotel.is_booking_update_running = False
            hotel.booking_last_update_status = 'error in processing location'
        hotel.booking_last_update_date = datetime.now()
        hotel.save()
        return
    except Exception, e:
	print 'Error in helper_scrape_booking_hotel_id - %s' % (str(e))
	hotel.is_booking_update_running = False
        hotel.booking_last_update_status = 'Error in helper_scrape_booking_hotel_id'
        hotel.booking_last_update_date = datetime.now()
        hotel.save()
        return

## get reviews from reviewlist url and queue the next page
def helper_scrape_booking_by_reviewlist_url(uid, inputurl, follownext=False, firstrun=False, ischained=False, overall=False, retry_flag=False):
    print 'helper_scrape_booking_by_reviewlist_url: %s - %s - %s - %s - %s - %s - (retry_flag)%s' % (uid, inputurl, follownext, firstrun, ischained, overall, retry_flag)
    source = 'booking'
    sourceid = 3
    count_beyond_date = 0
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
	#hotel.is_booking_update_running = True
	#hotel.save()
        try:
            #base_dir = "/home/ubuntu/sujaav/scrapecasper/hotels/"
            #check_or_create_dir(base_dir + hotel.identifier, True)
            #processing_dir = base_dir + hotel.identifier + "/" + source
            #check_or_create_dir(processing_dir, True)
            #check_or_create_dir(processing_dir + '/reviews', True)
	    if inputurl is None or len(inputurl) == 0:
		print 'URGENT - inputurl is None / missing'
		hotel.is_booking_update_running = False
		hotel.booking_last_update_status = 'reviewlist url is empty.'
		hotel.booking_last_update_date = datetime.now()
		hotel.save()
		return
	    print 'inputurl: %s' % inputurl
	    try:
		# m(1) - requests / m(2) - urllib2
                #args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':1 }
                #data_server_url = 'http://{0}/q/'.format(DATA_SERVER_2)
		args = { 'auth' :'zc3wiu4e6z1nwgye', 'q': inputurl}
                data_server_url = 'http://{0}/bnuy6vwh89enjkyo/'.format(DATA_SERVER_2)
                print 'data_server_url: %s' % (data_server_url)
                connect_timeout, read_timeout = 5.0, 20.0
                response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
                page = response.content
		print '-----------------------'
		print len(page)
		print '-------------------------'

	        #ua_string = ua_list[random.randrange(0,len(ua_list))]
		#headers = {'User-Agent': ua_string}
                #response = requests.get(inputurl, headers=headers)
                #html = response.content
                soup = BeautifulSoup(page, "html5lib")
                #if response.status_code != 200:
                #    print 'URGENT - Response code %s' % (response.status_code)
                #    hotel.is_booking_update_running = False
                #    hotel.save()
                #    return
		nexturl = ''
		try:
		    temp_reviews = soup.find('ul', attrs={'class':'review_list'}).findAll('li', attrs={'class':'review_item'})
		    print 'PAGE VALID'
		except Exception, e:
		    print 'Error in checking page validity - %s' % (str(e))
		    print 'retry_flag: %s' % (retry_flag)
		    random_sleep = random.randrange(1,4)
		    print 'retry after %s seconds' % (random_sleep)
		    if retry_flag == False:
		        helper_scrape_booking_by_reviewlist_url(uid, inputurl, follownext, firstrun, ischained, overall, True)
		    else:
			print 'ALREADY RETRIED'
		try:
		    reviews = soup.find('ul', attrs={'class':'review_list'}).findAll('li', attrs={'class':'review_item'})
		    if len(reviews) == 0:
			print 'No reviews found. Not a valid page. Returning...'
			hotel.is_booking_update_running = False
			hotel.booking_last_update_status = 'Not a valid reviewlist url.'
			hotel.booking_last_update_date = datetime.now()
			hotel.save()
			return
		    for review in reviews:
			response_data = {}
			reviewid = rating = title = review_pos = review_neg = rating_list = review_date = review_date_format = review_dt = ''
			reviewer_name = reviewer_country = reviewer_review_count = reviewer_age_group = ''
			manager_response_text = manager_response_date = manager_response_date_format = manager_response_dt = ''
                        has_manager_response = False
			print '...'
			#print str(review)
			#print '========'
			try:
			    reviewid = review.find('input', attrs={'name':'review_url'}).get('value')
			    if len(reviewid) == 0:
				print 'URGENT - ID not found. skipping'
				continue
			    print 'REVIEWID: %s' % reviewid
			except Exception, e:
			    print 'URGENT - Error in getting review reviewid %s' % (str(e))
			    continue
			try:
			    review_date = review.find('p', attrs={'class':'review_item_date'}).text.lstrip().rstrip()
			    if review_date.find(',') > 0:
			        review_date_format = "fm1" #November 3, 2015
			    else:
			        review_date_format = "fm2" #10 May 2016
			    print 'review_date: %s' % review_date
			    if review_date_format == "fm1": #November 3, 2015
                		try:
                    		    tlist =  review_date.split(" ")
                    		    if len(tlist) == 3:
                        		tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                        		print tstr
                        		review_dt = datetime.strptime(tstr, '%Y-%B-%d')
                        		print review_dt
				    try:
				        if firstrun == False: #update
					    if hotel.booking_update_window is None:
					        dt_threshold = datetime.now() - timedelta(days=30)
					    else:
					        dt_threshold = datetime.now() - timedelta(days=int(hotel.booking_update_window))
					    print 'spl dt_threshold: %s' % dt_threshold
					    if review_dt >= dt_threshold:
						print 'REVIEW FOUND in update window'
					    else:
						if count_beyond_date == 2:
						    print '%s - BEYOND UPDATE WINDOW. RETURNING...' % (count_beyond_date)
						    hotel.is_booking_update_running = False
						    hotel.booking_last_update_status = ''
						    hotel.booking_last_update_date = datetime.now()
                        			    hotel.save()
                        			    return
						else:
						    print 'CRAZY - old review found'
						    count_beyond_date = count_beyond_date + 1
				    except Exception, e:
					print 'URGENT Error in check dt_threshold for update. Returning...%s' % (str(e))
					hotel.is_booking_update_running = False
					hotel.booking_last_update_status = 'Error in check dt_threshold for update'
					hotel.booking_last_update_date = datetime.now()
					hotel.save()
					return
                		except Exception, e:
                    		    print 'URGENT Error in review date coversion fm1 - %s' % (str(e))
			    if review_date_format == "fm2": #10 May 2016
                                try:
                                    tlist =  review_date.split(" ")
                                    if len(tlist) == 3:
                                        tstr = tlist[2] + "-" + tlist[1] + "-" + tlist[0]
                                        print tstr
                                        review_dt = datetime.strptime(tstr, '%Y-%B-%d')
                                        print review_dt
                                except Exception, e:
                                    print 'URGENT Error in review date coversion fm2 - %s' % (str(e))
			    try:
                                if firstrun == False: #update
                                    if hotel.booking_update_window is None:
                                        dt_threshold = datetime.now() - timedelta(days=30)
                                    else:
                                        dt_threshold = datetime.now() - timedelta(days=int(hotel.booking_update_window))
                                    print 'spl dt_threshold: %s' % dt_threshold
                                    if review_dt >= dt_threshold:
                                        print 'REVIEW FOUND in update window'
                                    else:
                                        if count_beyond_date == 2:
                                            print '%s - BEYOND UPDATE WINDOW. RETURNING....' % (count_beyond_date)
                                            hotel.is_booking_update_running = False
                                            hotel.booking_last_update_status = ''
                                            hotel.booking_last_update_date = datetime.now()
                                            hotel.save()
					    #try:
					    #    from django import db
					    #    db.connections.close_all()
					#	print 'DB CONNECTION CLOSED'
					#    except Exception, e:
					#	print 'ERORR IN CLOSING DB CONNECTION: %s' % (str(e))

                                            return
                                        else:
                                            print 'CRAZY - old review found'
                                            count_beyond_date = count_beyond_date + 1
                            except Exception, e:
                                print 'URGENT Error in check dt_threshold for update. Returning...%s' % (str(e))
                                hotel.is_booking_update_running = False
                                hotel.booking_last_update_status = 'Error in check dt_threshold for update'
                                hotel.booking_last_update_date = datetime.now()
                                hotel.save()
                                return
			except Exception, e:
			    print 'Error in getting review_date - %s' % (str(e))
			try:
			    #rating = review.find('meta', attrs={'itemprop':'ratingValue'}).get('content')
			    rating = review.find('div', attrs={'class':'review_item_review_score'}).text.lstrip().rstrip()
			    print 'booking rating: %s' % rating
			    if rating == None:
				raise Exception('rating is None')
			except Exception, e:
			    print 'Error in getting booking rating - %s' % (str(e))
			    try:
			        rating = review.find('span', attrs={'class':'review-score-badge'})
			        print 'booking rating find: %s' % rating
			        rating = rating.text.lstrip().rstrip()
			        print 'booking rating: %s' % rating
			    except Exception, e:
				print 'booking rating retry error: %s' % (str(e))
				print 'booking rating -- %s' % (review.find('div', attrs={'class':'review_item_review'}))
			try:
			    title = review.find('div', attrs={'class':'review_item_header_content_container'}).find('div', attrs={'class':'review_item_header_content'}).text.lstrip().rstrip()
			    try:
				title = re.sub('[^a-zA-Z0-9-_*. ]', '', title)
			    except Exception, e:
				print 'Error in regex - %s' % (str(e))
			    print 'title: %s' % title
			except Exception, e:
			    print 'Error in getting title - %s' % (str(e))
			try:
			    tempelement = review.find('div', attrs={'class':'review_item_review_content'}).find('p', attrs={'class':'review_pos'})
			    t = tempelement.find('i', attrs={'class':'review_item_icon'}).extract()
			    review_pos = tempelement.text.lstrip().rstrip()
			    print 'review_pos: %s' % review_pos
			except Exception, e:
			    print 'Error in getting review_pos - %s' % (str(e))
			try:
			    tempelement = review.find('div', attrs={'class':'review_item_review_content'}).find('p', attrs={'class':'review_neg'})
			    t = tempelement.find('i', attrs={'class':'review_item_icon'}).extract()
			    review_neg = tempelement.text.lstrip().rstrip()
			    print 'review_neg: %s' % review_neg
			except Exception, e:
			    print 'Error in getting review_neg - %s' % (str(e))
			try:
			    #tags = review.find('div', attrs={'class':'review_item_review_container'}).find('ul', attrs={'class':'review_item_info_tags'}).findAll('li')
			    tags = review.find('div', attrs={'class':'review_item_review'}).find('ul', attrs={'class':'review_item_info_tags'}).findAll('li')
			    for tag in tags:
				temp = [s.extract() for s in tag.find('span')]
				rating_list = rating_list + tag.text.lstrip().rstrip() + '#'
			    print 'rating_list: %s' % rating_list
			except Exception, e:
			    print 'Error in getting rating_list - %s' % (str(e))
			try:
                            reviewer_name = review.find('div', attrs={'class':'review_item_reviewer'}).find('h4').text.lstrip().rstrip()
                            print 'reviewer_name: %s' % reviewer_name
                        except Exception, e:
                            print 'Error in getting reviewer_name - %s' % (str(e))
			try:
                            reviewer_country = review.find('div', attrs={'class':'review_item_reviewer'}).find('span', attrs={'class':'reviewer_country'}).text.lstrip().rstrip()
                            print 'reviewer_country: %s' % reviewer_country
                        except Exception, e:
                            print 'Error in getting reviewer_country - %s' % (str(e))
			try:
                            reviewer_review_count = review.find('div', attrs={'class':'review_item_reviewer'}).find('div', attrs={'class':'review_item_user_review_count'}).text.lstrip().rstrip()
                            print 'reviewer_review_count: %s' % reviewer_review_count
                        except Exception, e:
                            print 'Error in getting reviewer_review_count - %s' % (str(e))
			try:
                            reviewer_age_group = review.find('div', attrs={'class':'review_item_reviewer'}).find('div', attrs={'class':'user_age_group'}).text.lstrip().rstrip()
                            print 'reviewer_age_group: %s' % reviewer_age_group
                        except Exception, e:
                            print 'Error in getting reviewer_age_group - %s' % (str(e))
			try:
                            manager_response_text = review.find('div', attrs={'class':'review_item_response_container'}).get('data-full-response').lstrip().rstrip()
			    has_manager_response  = True
                            print 'manager_response_text: %s' % manager_response_text
                        except Exception, e:
                            print 'Error in getting manager_response_text - %s' % (str(e))

			response_data['reviewid'] = reviewid
			response_data['rating'] = rating
			response_data['title'] = title
			response_data['review_pos'] = review_pos
			response_data['review_neg'] = review_neg
			response_data['rating_list'] = rating_list
			response_data['review_date'] = review_date
			response_data['review_date_format'] = review_date_format
			response_data['reviewer_name'] = reviewer_name
			response_data['reviewer_country'] = reviewer_country
			response_data['reviewer_review_count'] = reviewer_review_count
			response_data['reviewer_age_group'] = reviewer_age_group
			response_data['has_manager_response'] = has_manager_response
			response_data['manager_response_text'] = manager_response_text

			try:
			    tlist = reviewer_review_count.rstrip().lstrip().split(" ")
			    if len(tlist) > 0:
				tint = int((tlist[0]).replace(',',''))
			        reviewer_review_count = tint
			except Exception, e:
			    print 'Error in extracting reviewer_review_count from tlist: %s' % (str(e))

                        try:
			    upserted_review_id = None
                            mongo_review = MongoReview()
                            find_param = {}
                            find_param['identifier'] = reviewid
                            find_param['hotel_id'] = hotel.hotel_id
                            find_param['source'] = 3 #booking
                            find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
                            update_param = OrderedDict()
                            find_count = mongo_review.count(find_param)
                            if find_count == 0:
                                print 'create new booking MongoReview'
                                update_param['_id'] = uuid.uuid4().hex[:16].lower()
                            else:
                                print 'existing booking MongoReview found'
                            update_param['title'] = title
                            update_param['comment'] = review_pos
                            update_param['comment_negative'] = review_neg
                            update_param['rating'] = rating
        		    rating_number = convert_rating_to_number_booking(rating)
        		    update_param['rating_number'] = rating_number
        		    update_param['rating_out_of_5'] = float(rating_number/2)
                            update_param['rating_list_text'] = rating_list
                            author = {}
                            author['name'] = reviewer_name
                            author['location'] = reviewer_country
                            author['total_reviews'] = reviewer_review_count
                            author['remarks'] = reviewer_age_group
                            update_param['author'] = author
                            if isinstance(review_dt, datetime):
                                update_param['review_date'] = review_dt
			    else:
				print 'booking No review_date found'
				alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('booking', hotel.hotel_id, reviewid, title, reviewer_name)
				mongo_log_alert(type='scrape', info=alert_msg)
                            update_param['has_manager_response'] = has_manager_response
                            update_param['manager_response'] = manager_response_text
                            if find_count == 0:
                                update_param['date_created'] = datetime.now()
                            else:
                                update_param['date_updated'] = datetime.now()
                            print 'Try saving booking MongoReview'
                            mongo_review.set_find_param(find_param)
                            print 'try setting update_param'
                            mongo_review.set_update_param(update_param)
                            mongo_result = mongo_review.update()
                            if mongo_result:
				upserted_review_id = mongo_result.upserted_id
                                print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
                                print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
                                print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
                            print 'booking MongoReview updated'
                        except Exception, e:
                            print 'Error in updating booking MongoReview - %s' % (str(e))

			#UPDATE POSTGRES
			try:
                            print 'Check in DB for the review'
                            reviews = Review.objects.filter(identifier=reviewid, hotel=hotel, is_unavailable=False).order_by('-date_created')
                            print 'reviews len: %s' % len(reviews)
                            if len(reviews) == 0:
                                print 'CREATING new reviewer and review'
                                reviewer = Reviewer.objects.create(source=sourceid)
				if len(reviewer_name) > 0:
				    reviewer.name = reviewer_name
				    reviewer.location = reviewer_country
				    #tlist = reviewer_review_count.rstrip().lstrip().split(" ")
				    #if len(tlist) > 0:
				#	tint = int((tlist[0]).replace(',',''))
				#        reviewer.total_reviews = tint
				    reviewer.total_reviews = reviewer_review_count
				    reviewer.remarks = reviewer_age_group
				    try:
					print 'Try saving reviewer'
					reviewer.save()
                                    	review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
					review.title = title
					review.comment = review_pos
					review.comment_negative = review_neg
					review.rating = rating
					review.rating_list_text = rating_list
					try:
					    review.review_date = review_dt
					except Exception, e:
					    print 'URGENT Error in review_dt assignment, skipping review - %s' % (str(e))
					    print 'deleteing reviewer'
                                            reviewer.delete()
                                            print 'reviewer deleted'
                                            continue
					review.has_manager_response = has_manager_response
					review.manager_response = manager_response_text
					review.response_posted_checkbox = False
					review.is_non_english = False
					review.is_partial = False
                                    	try:
					    print 'Try saving review'
                                            review.save()

					    #Update review_id in mongodb
                                            if upserted_review_id:
                                                try:
                                                    print 'Update review_id %s' % (review.review_id)
                                                    mongo_review = MongoReview()
                                                    find_param = {}
                                                    find_param['_id'] = upserted_review_id
                                                    update_param = {}
                                                    update_param['review_id'] = review.review_id
                                                    print 'Try saving review_id booking MongoReview'
                                                    mongo_review.set_find_param(find_param)
                                                    print 'try setting review_id update_param'
                                                    mongo_review.set_update_param(update_param)
                                                    mongo_result = mongo_review.update()
                                                    if mongo_result:
                                                        print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                                        print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                                        print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                                        print 'booking MongoReview review_id updated'
                                                except Exception, e:
                                                    print 'Error in updating review_id in mongodb: %s' % (str(e))
                                            else:
                                                print 'upserted_review_id is None'

                                    	except Exception, e:
                                            print 'Error in executing save of review - new record - %s' % (str(e))
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    continue
                                    except Exception, e:
                                        print 'Error in executing save of reviewer - %s' % (str(e))
                            else:
                                print 'UPDATING...Existing reviewer and review found'
                                review = reviews[0]
                                if len(reviews) > 1:
                                    print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
				review.title = title
				review.comment = review_pos
				review.comment_negative = review_neg
				review.rating = rating
				review.rating_list_text = rating_list
				review.has_manager_response = has_manager_response
				review.manager_response = manager_response_text
				try:
				    review.review_date = review_dt
				except Exception, e:
				    print 'Error in review_dt assignment, skipping updating record - %s' % (str(e))
				    continue
                                try:
				    print 'Try saving review'
                                    review.save()
                                except Exception, e:
                                    print 'Error in executing save of review - existing record - %s' % (str(e))
				    continue
                        except Exception, e:
                            print 'Error in checking in DB for the review - %s' % (str(e))
			    continue

			#For checking purposes - forced break
			#break

		    try:
			print 'Check for next url'
                        nexturl = soup.find('div', attrs={'class':'review_list_pagination'}).find('p', attrs={'class':'review_next_page'}).find('a', attrs={'id':'review_next_page_link'}).get('href')
			nexturl = nexturl.lstrip().rstrip()
			nexturl = 'http://www.booking.com' + nexturl
                        print 'nexturl: %s' % nexturl
                    except Exception, e:
                        print 'Error in getting nexturl - %s' % (str(e))
		    if firstrun == False and follownext == False:
			print 'firstrun is False and follownext is False. Clean Exit.'
			hotel.is_booking_update_running = False
			hotel.booking_last_update_status = ''
			hotel.booking_last_update_date = datetime.now()
			hotel.save()
			return
		    if len(nexturl) > 0:
			print 'Queue the next page'
			try:
			    timedelay = random.randrange(7,12)
                            api_root = 'http://localhost:5555/api'
                            task_api = '{}/task'.format(api_root)
                            args = {'args': [timedelay, uid, nexturl, follownext, firstrun, ischained, overall]}
                            url = '{}/async-apply/scrape.tasks.task_wrapper_booking_by_reviewlist_url'.format(task_api)
                            print url
                            resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                            print 'task post status code: %s' % (resp.status_code)
                        except Exception, e:
                            print 'Error in making celery web request - %s' % (str(e))
			    hotel.is_booking_update_running = False
			    hotel.booking_last_update_status = 'Error in making celery web request'
			    hotel.booking_last_update_date = datetime.now()
			    hotel.save()
			    return
		    else:
			print 'No nexturl. Clean exit'
			hotel.is_booking_update_running = False
			hotel.booking_last_update_status = ''
			hotel.booking_last_update_date = datetime.now()
			hotel.save()
			return
		except Exception, e:
		    print 'Error in getting reviews - %s' % (str(e))
		    hotel.is_booking_update_running = False
		    hotel.booking_last_update_status = 'error in getting reviews from soup'
	    except Exception, e:
		print 'Error in making soup - %s' % (str(e))
		hotel.is_booking_update_running = False
		hotel.booking_last_update_status = 'b1 - {0}'.format(str(e))
        except Exception, e:
            print 'Error in processing hotel - %s' % (str(e))
	    hotel.is_booking_update_running = False
	    hotel.booking_last_update_status = 'b2 - {0}'.format(str(e))
	hotel.booking_last_update_date = datetime.now()
	hotel.save()
	return
    except Exception, e:
	print 'Error in helper_scrape_booking_by_reviewlist_url - %s' %  (str(e))
	hotel.is_booking_update_running = False
	hotel.booking_last_update_status = 'Error in helper_scrape_booking_by_reviewlist_url'
	hotel.booking_last_update_date = datetime.now()
	hotel.save()
	return

## Get overall ratings from booking
def helper_scrape_booking_overall_hotel(uid, inputurl=None):
    print 'helper_scrape_booking_overall_hotel: %s - %s' % (uid, inputurl)
    source = 'booking'
    sourceid = 3
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
        try:
	    # m(1) - requests / m(2) - urllib2
            args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':1 }
            data_server_url = 'http://{0}/q/'.format(DATA_SERVER_1)
            print 'data_server_url: %s' % (data_server_url)
            connect_timeout, read_timeout = 5.0, 20.0
            response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
            page = response.content

	    #ua_string = ua_list[random.randrange(0,len(ua_list))]
            #headers = {'User-Agent': ua_string}
            #response = requests.get(inputurl, headers=headers)
            #html = response.content
            soup = BeautifulSoup(page, "html5lib")
            #if response.status_code != 200:
            #    print 'URGENT - Response code %s' % (response.status_code)
            #    return
            read_overall_booking(hotel, soup)
        except Exception, e:
            print 'URGENT Error in soup - %s' % (str(e))
    except Exception, e:
        print 'Error in getting hotel - %s' % (str(e))



def v_test_1():
    print 't1'
    for num in range(1,20):
        print 't1 - %s' % num
        time.sleep(2)


def v_test_2():
    print 't2'
    for num in range(1,20):
        print 't2 - %s' % num
        time.sleep(2)


#Tripadvisor- Get reviews and queue the next page for tripadvisor
def helper_scrape_tripadvisor_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'helper_scrape_tripadvisor_by_hotel_id: %s - %s - %s - %s - %s - %s' % (uid, inputurl, follownext, firstrun, ischained, overall)
    source = 'tripadvisor'
    sourceid = 2
    base = 'https://www.tripadvisor.com'
    temp_delay = 0
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
	#hotel.is_tripadvisor_update_running = True #ONLY FOR TEST
	hotel.tripadvisor_reviews_beyond_threshold = 0
	hotel.save()
        try:
	    if inputurl is None:
		inputurl = hotel.tripadvisor_url
	    print 'inputurl: %s' % inputurl
	    if len(inputurl) == 0:
		print 'Invalid input url. Returning...'
		hotel = Hotel.objects.get(hotel_id=uid)
		hotel.is_tripadvisor_update_running = False
		hotel.tripadvisor_last_update_status = 'url missing'
		hotel.tripadvisor_last_update_date = datetime.now()
                hotel.save()
                return
	    try:
		#opener = urllib2.build_opener()
		#opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		#response = opener.open(inputurl)
		#page = response.read()
		#soup = BeautifulSoup(page, "html5lib")
		#opener.close()

		# m(1) - requests / m(2) - urllib2
                args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':1 }
                data_server_url = 'http://{0}/q/'.format(DATA_SERVER_1)
                print 'data_server_url: %s' % (data_server_url)
                connect_timeout, read_timeout = 5.0, 20.0
                response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
                page = response.content

		soup = BeautifulSoup(page, "html5lib")
		#print 'title: %s' % soup.find('div', attrs={'class':'heading_name_wrapper'}).find('h1').text.lstrip().rstrip()
		print 'title: %s' % soup.find('div', attrs={'class':'ppr_priv_location_detail_header'}).find('h1').text.lstrip().rstrip()
		nexturl = ''
		if overall == True:
		    read_overall_tripadvisor(hotel, soup)
		    overall = False
		try:
		    inreviews = soup.findAll('div', attrs={'class':'reviewSelector'})
		    if len(inreviews) == 0:
			print 'No reviews found. Not a valid page. Returning...'
			hotel = Hotel.objects.get(hotel_id=uid)
			hotel.is_tripadvisor_update_running = False
			hotel.tripadvisor_last_update_status = 'not a valid url'
			hotel.tripadvisor_last_update_date = datetime.now()
			hotel.save()
			return
		    timedelay = 1
		    permalink_list = []
		    reviewid_list = []
		    for inreview in inreviews:
			response_data = {}
			reviewid = permalink = ''
			try:
			    reviewid = inreview.get('id').lstrip().rstrip()
			    print 'reviewid: %s' % reviewid
			except Exception, e:
			    print 'URGENT: Error in getting reviewid, Skipping - %s' % (str(e))
			    continue
			try:
			    tstr = inputurl
			    print tstr #http://www.tripadvisor.com/Hotel_Review-g33020-d81653-Reviews-Fontaine_Inn_Downtown_Fairgrounds-San_Jose_California.html
			    base = tstr[0:tstr.find("/Hotel_Review-")]
			    tstr = tstr[tstr.find("/Hotel_Review-"):]
			    print tstr #/Hotel_Review-g33020-d81653-Reviews-Fontaine_Inn_Downtown_Fairgrounds-San_Jose_California.html
			    tlist = tstr.split('-')
			    if tstr.find('-Reviews-o') > 0:
				ttstr = tstr.split('-Reviews-')[1] #or10-Fontaine_Inn_Downtown_Fairgrounds-San_Jose_California.html
				ttstr = ttstr[ttstr.find('-')+1:] #Fontaine_Inn_Downtown_Fairgrounds-San_Jose_California.html
			        permalink = '/ShowUserReviews-'+tlist[1]+'-'+tlist[2]+'-r'+reviewid.split('_')[1]+'-'+ttstr
			    else:
			        permalink = '/ShowUserReviews-'+tlist[1]+'-'+tlist[2]+'-r'+reviewid.split('_')[1]+'-'+tstr[tstr.find('-Reviews-')+len('-Reviews-'):]
				print tlist[1]
				print tlist[2]
				print tstr[tstr.find('-Reviews-')+len('-Reviews-'):]
			    print 'permalink1: %s' % permalink
			    permalink = base + permalink
			    print 'permalink2: %s' % permalink
			    permalink_list.append(permalink)
			    reviewid_list.append(reviewid)
			    try:
				process_partial_review(uid, inreview, reviewid, permalink)
			    except Exception, e:
			  	print 'Error in processing partial review: %s' % (str(e))
		        except Exception, e:
			    print 'URGENT: Error in getting permalink. Skipping... - %s' % (str(e))
			    continue
		    #End of for
		    try:
		        print 'tripadvisor -- Check for next url' #/Hotel_Review-g33020-d81653-Reviews-or10-Fontaine_Inn_Downtown_Fairgrounds-San_Jose_California.html#REVIEWS
		        nexturl = soup.find('div', attrs={'class':'pagination'}).find('a', attrs={'class':'next'}).get('href').lstrip().rstrip()
		        nexturl = nexturl[0:nexturl.find('#')]
		        print 'nexturl: %s' % nexturl
		        nexturl = base + nexturl
		        print 'nexturl: %s' % nexturl
		    except Exception, e:
		        print 'tripadvisor Error in getting nexturl - %s' % (str(e))
			nexturl = ''

		    if nexturl == '':
		        try:
                            print '- Check for next url using data-page-number and data-offset'
			    cur_page_number = soup.find('div',attrs={'class':'pageNumbers'}).find('span',attrs={'class':'current'}).get('data-page-number').lstrip().rstrip()
			    print 'cur_page_number: %s' % (cur_page_number)
			    cur_offset = soup.find('div',attrs={'class':'pageNumbers'}).find('span',attrs={'class':'current'}).get('data-offset').lstrip().rstrip()
			    print 'cur_offset: %s' % (cur_offset)
			    next_page_number = int(cur_page_number)+1
			    print 'next_page_number: %s' % (next_page_number)
			    #next_offset = soup.find('div',attrs={'class':'pageNumbers'}).find('a',attrs={'data-page-number':next_page_number}).get('data-offset').lstrip().rstrip()
			    next_offset = soup.find('div',attrs={'class':'pageNumbers'}).find('span',attrs={'data-page-number':next_page_number}).get('data-offset').lstrip().rstrip()
			    print 'next_offset: %s' % (next_offset)
			    #or_str = int(cur_offset)+int(next_offset)
			    or_str = int(next_offset)
			    print 'or_str: %s' % (or_str)
			    or_str = '-or{}'.format(or_str)
			    print 'or_str: %s' % (or_str)

			    t1 = inputurl
			    print 't1: %s' % (t1)
			    index1 = t1.find('-Reviews-or')
			    print 'index1: %s' % (index1)
			    if index1 == -1:
			        #'-or' not found
			        tlist = t1.split('-Reviews-')
			        nexturl = tlist[0]+'-Reviews'+or_str+'-'+tlist[1]
			    else:
			        index2 = t1.find('-',index1+len('-Reviews-or'))
			        print 'index2: %s' % (index2)
			        nexturl = t1[:index1]+'-Reviews'+or_str+t1[index2:]
                            print 'nexturl: %s' % nexturl
                        except Exception, e:
                            print 'tripadvisor -- Error in getting nexturl - %s' % (str(e))

		    print 'queue the task'
		    if len(permalink_list) == 0:
		        print 'permalink_list is empty. Returning...'
			hotel = Hotel.objects.get(hotel_id=uid)
			hotel.is_tripadvisor_update_running = False
			hotel.tripadvisor_last_update_status = 'permalink list is empty'
			hotel.tripadvisor_last_update_date = datetime.now()
		        hotel.save()
			return
                    try:
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
			timedelay = timedelay + random.randrange(2,5)

			args = {'args': [timedelay, uid, reviewid_list, permalink_list, nexturl, firstrun, follownext, ischained, overall]}
			url = '{}/async-apply/scrape.tasks.task_wrapper_tripadvisor_by_reviewlist'.format(task_api)
                        print url
                        print args
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'task post status code: %s' % resp.status_code
			if resp.status_code == 200:
			    hotel = Hotel.objects.get(hotel_id=uid)
			    hotel.is_tripadvisor_task_running_for_reviewlist = True
			    hotel.save()
			    print 'is_tripadvisor_task_running_for_reviewlist set to True'
        		    hotel = Hotel.objects.get(hotel_id=uid)
			    print 'after save check is_tripadvisor_task_running_for_reviewlist: %s' % (hotel.is_tripadvisor_task_running_for_reviewlist)
                    except Exception, e:
                        print 'Error in making celery web request for task_wrapper_scrape_tripadvisor_by_reviewlist - %s' % (str(e))
			hotel = Hotel.objects.get(hotel_id=uid)
		        hotel.is_tripadvisor_update_running = False
		        hotel.tripadvisor_last_update_status = 'error in queuing task'
		        hotel.tripadvisor_last_update_date = datetime.now()
		        hotel.save()
		        return



		except Exception, e:
		    print 'Error in processing reviews - %s' % (str(e))
		    hotel = Hotel.objects.get(hotel_id=uid)
		    hotel.is_tripadvisor_update_running = False
		    hotel.tripadvisor_last_update_status = 'error in processing reviews'
		    hotel.tripadvisor_last_update_date = datetime.now()
		    hotel.save()
		    return

		#if firstrun == False and follownext == False:
		#    print 'firstrun is False and follownext is False. Clean Exit.'
        	#    hotel = Hotel.objects.get(hotel_id=uid)
		#    hotel.is_tripadvisor_update_running = False
		#    hotel.tripadvisor_last_update_status = ''
		#    hotel.tripadvisor_last_update_date = datetime.now()
		#    hotel.save()
		#    return
		#if len(nexturl) > 0:
		#    print 'Queue the next page'
		#    try:
		#	timedelay = timedelay + 3
                #        api_root = 'http://localhost:5555/api'
                #        task_api = '{}/task'.format(api_root)
                #        args = {'args': [timedelay, uid, nexturl, follownext, firstrun, ischained, overall]}
                #        url = '{}/async-apply/scrape.tasks.task_wrapper_tripadvisor_by_hotel_id'.format(task_api)
                #        print url
                #        print args
                #        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                #        print 'POST request status: %s' % resp.status_code
                #    except Exception, e:
                #        print 'Error in making celery web request - %s' % (str(e))
		#	hotel = Hotel.objects.get(hotel_id=uid)
		#        hotel.is_tripadvisor_update_running = False
		#        hotel.tripadvisor_last_update_status = 'Error in making celery web request'
		#        hotel.tripadvisor_last_update_date = datetime.now()
		#        hotel.save()
		#        return
		#else:
        	#    print 'No nexturl. Clean exit'
		#    hotel = Hotel.objects.get(hotel_id=uid)
		#    hotel.is_tripadvisor_update_running = False
		#    hotel.tripadvisor_last_update_status = ''
		#    hotel.tripadvisor_last_update_date = datetime.now()
		#    hotel.save()
		#    return
	    except Exception, e:
		print 'Error in making soup - %s' % (str(e))
		hotel = Hotel.objects.get(hotel_id=uid)
	        hotel.is_tripadvisor_update_running = False
	        hotel.tripadvisor_last_update_status = 't1 - {0}'.format(str(e))
	except Exception, e:
	    print 'Error in processing hotel - %s' % (str(e))
	    hotel = Hotel.objects.get(hotel_id=uid)
	    hotel.is_tripadvisor_update_running = False
	    hotel.tripadvisor_last_update_status = 't2 - {0}'.format(str(e))
        hotel.tripadvisor_last_update_date = datetime.now()
	hotel.save()
	return
    except Exception, e:
	print 'Error in helper_scrape_tripadvisor_by_hotel_id - %s' % (str(e))
	hotel = Hotel.objects.get(hotel_id=uid)
	hotel.is_tripadvisor_update_running = False
	hotel.tripadvisor_last_update_status = 'Error in helper_scrape_tripadvisor_by_hotel_id'
	hotel.tripadvisor_last_update_date = datetime.now()
	hotel.save()
	return


def helper_scrape_tripadvisor_by_reviewlist(uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall):
    print 'helper_scrape_tripadvisor_by_reviewlist: %s -- [[[]]]%s - [[[]]]%s - %s - %s - %s - %s' % (uid, len(reviewid_list), len(inputurl_list), firstrun, follownext, ischained, overall)
    source = 'tripadvisor'
    sourceid = 2
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
        try:
	    print 'inputurl_list length: %s' % (len(inputurl_list))
            if len(inputurl_list) == 0:
                print 'inputurl_list is empty. Returning...'
                #hotel.is_tripadvisor_task_running_for_reviewlist = False
                #hotel.save()
                return
            inputurl = inputurl_list[0]
            reviewid = reviewid_list[0]
	    print 'inputurl: %s' % inputurl
	    print 'reviewid: %s' % reviewid
	    if len(inputurl) > 0:
	        try:
		    completed = helper_scrape_tripadvisor_by_review_id(uid, reviewid, inputurl, firstrun)
                    if completed == 'error':
                        print 'URGENT: helper_scrape_tripadvisor_by_review_id returned False. Returning...'
			hotel = Hotel.objects.get(hotel_id=uid)
                        hotel.is_tripadvisor_task_running_for_reviewlist = False
                    	hotel.is_tripadvisor_update_running = False
                    	hotel.tripadvisor_last_update_status = 'error'
                    	hotel.tripadvisor_last_update_date = datetime.now()
                        hotel.save()
                        return
                    if completed == 'beyond':
                        print 'BEYOND UDPATE DATE. No need to go check nexturl. Returning...'
			hotel = Hotel.objects.get(hotel_id=uid)
                        hotel.is_tripadvisor_task_running_for_reviewlist = False
                    	hotel.is_tripadvisor_update_running = False
                    	hotel.tripadvisor_last_update_status = ''
                    	hotel.tripadvisor_last_update_date = datetime.now()
                        hotel.save()
                        return
		    print 'queue the next reviewid task by removing the completed inputurl'
                    if len(inputurl_list) == 1:
                        print 'inputurl_list is fully processed. Returning...'
                        #hotel.is_tripadvisor_task_running_for_reviewlist = False
                        #hotel.save()
                        #return
			if firstrun == False and follownext == False:
                    	    print 'firstrun is False and follownext is False. Clean Exit.'
                    	    hotel = Hotel.objects.get(hotel_id=uid)
                    	    hotel.is_tripadvisor_update_running = False
                    	    hotel.tripadvisor_last_update_status = ''
                    	    hotel.tripadvisor_last_update_date = datetime.now()
                    	    hotel.save()
			    return
			print 'CHECK NEXT URL - %s' % (nexturl)
			if len(nexturl) > 0:
                    	    print 'Queue the next page'
                    	    try:
                                timedelay = random.randrange(2,5)
                                api_root = 'http://localhost:5555/api'
                                task_api = '{}/task'.format(api_root)
                                args = {'args': [timedelay, uid, nexturl, follownext, firstrun, ischained, overall]}
                                url = '{}/async-apply/scrape.tasks.task_wrapper_tripadvisor_by_hotel_id'.format(task_api)
                                print url
                                print args
                                resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                                print 'POST request status: %s' % resp.status_code
				return
                            except Exception, e:
                                print 'Error in making celery web request - %s' % (str(e))
                                hotel = Hotel.objects.get(hotel_id=uid)
                                hotel.is_tripadvisor_update_running = False
                                hotel.tripadvisor_last_update_status = 'Error in making celery web request'
                                hotel.tripadvisor_last_update_date = datetime.now()
                                hotel.save()
                                return
                        else:
                            print 'No nexturl. Clean exit'
                            hotel = Hotel.objects.get(hotel_id=uid)
                            hotel.is_tripadvisor_task_running_for_reviewlist = False
                            hotel.is_tripadvisor_update_running = False
                            hotel.tripadvisor_last_update_status = ''
                            hotel.tripadvisor_last_update_date = datetime.now()
                            hotel.save()
                            return


		    inputurl_list = inputurl_list[1:]
		    reviewid_list = reviewid_list[1:]
                    try:
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
                        timedelay = random.randrange(2,5)
                        args = {'args': [timedelay, uid, reviewid_list, inputurl_list, nexturl, firstrun, follownext, ischained, overall]}
                        url = '{}/async-apply/scrape.tasks.task_wrapper_tripadvisor_by_reviewlist'.format(task_api)
                        print url
                        print args
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'task post status code: %s' % resp.status_code
                    except Exception, e:
                        print 'Error in making celery web request for task_wrapper_scrape_tripadvisor_by_reviewlist - %s' % (str(e))
                        return
	        except Exception, e:
		    print 'Error in invoking helper_scrape_tripadvisor_by_reviewlist - %s' % (str(e))
	    else:
		print 'URGENT - Invalid input url. Returning...'
                #hotel.is_tripadvisor_task_running_for_reviewlist = False
                #hotel.save()
		return
	except:
	    print 'Error in processing reviewlist'
    except:
	print 'helper_scrape_tripadvisor_by_reviewlist'

#process_partial_review(inreview, reviewid, permalink)
def process_partial_review(uid, inreview, reviewid, permalink):
    print 'process_partial_review: %s - %s' % (reviewid, permalink)
    source = 'tripadvisor'
    sourceid = 2
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
        try:
	    try:
		if inreview is None:
		    print 'No review found. Not a valid block. Returning...'
		    return 'error'
		try:
		    response_data = {}
		    rating = title = review_text = review_location = review_date = review_date_format = review_dt = ''
		    reviewer_name = reviewer_location = reviewer_c_level = reviewer_total_reviews = reviewer_hotel_reviews = reviewer_helpful_votes = ''
		    manager_response_header = manager_response_text = ''
		    reviewer_c_level = None
		    has_manager_response = False
		    try:
		        reviewer_name = inreview.find('div', attrs={'class':'member_info'}).find('div', attrs={'class':'username'}).find('span').text.lstrip().rstrip()
			print 'reviewer_name: %s' % reviewer_name
		    except Exception, e:
			print 'Error in getting reviewer_name span - %s' % (str(e))
		    try:
		        reviewer_location = inreview.find('div', attrs={'class':'member_info'}).find('div', attrs={'class':'location'}).text.lstrip().rstrip()
			print 'reviewer_location: %s' % reviewer_location
		    except Exception, e:
			print 'Error in getting reviewer_location - %s' % (str(e))
		    try:
			tlist = inreview.find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'levelBadge'}).get('class')
			for t in tlist:
			    if t.find('lvl_') >= 0:
			        reviewer_c_level = str(int(t[len('lvl_'):]))
				break
			print 'reviewer_c_level: %s' % reviewer_c_level
		    except Exception, e:
			print 'Error in getting reviewer_c_level - %s' % (str(e))
		    try:
			reviewer_total_reviews = inreview.find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'reviewerBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			#reviewer_total_reviews = reviewer_total_reviews.split(' ')[0]
			#reviewer_total_reviews = int(reviewer_total_reviews.replace(',',''))
			print 'reviewer_total_reviews: %s' % reviewer_total_reviews
		    except Exception, e:
			print 'Error in getting reviewer_total_reviews - %s' % (str(e))
		    try:
			reviewer_hotel_reviews = inreview.find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'contributionReviewBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			#reviewer_hotel_reviews = reviewer_hotel_reviews.split(' ')[0]
			#reviewer_hotel_reviews = int(reviewer_hotel_reviews.replace(',',''))
			print 'reviewer_hotel_reviews: %s' % reviewer_hotel_reviews
		    except Exception, e:
			print 'Error in getting reviewer_hotel_reviews - %s' % (str(e))
		    try:
			reviewer_helpful_votes = inreview.find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'helpfulVotesBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			#reviewer_helpful_votes = reviewer_helpful_votes.split(' ')[0]
			#reviewer_helpful_votes = int(reviewer_helpful_votes.replace(',',''))
			print 'reviewer_helpful_votes: %s' % reviewer_helpful_votes
		    except Exception, e:
			print 'Error in getting reviewer_helpful_votes - %s' % (str(e))
		    try:
		        tstr = inreview.find('div', attrs={'class':'quote'}).text.lstrip().rstrip()
			#title = tstr[1:len(tstr)-1].lstrip().rstrip()
			title = tstr.lstrip().rstrip()
			print 'title: %s' % title
		    except Exception, e:
			print 'Error in getting title - %s' % (str(e))
		    try:
			#review_text = inreview.find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			review_text = inreview.find('div', attrs={'class':'prw_rup prw_reviews_text_summary_hsx'}).find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			print 'review_text: %s' % review_text
		    except Exception, e:
			print 'Error in getting review_text - %s' % (str(e))
		    try:
			rating = inreview.find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ui_bubble_rating'}).get('class')
			print 'rating tripadvisor partial: %s' % rating
			tlist = rating
			for t in tlist:
			    if t.find('bubble_10') == 0:
				rating = '1 of 5 bubbles'
				break
			    if t.find('bubble_20') == 0:
				rating = '2 of 5 bubbles'
				break
			    if t.find('bubble_30') == 0:
				rating = '3 of 5 bubbles'
				break
			    if t.find('bubble_40') == 0:
				rating = '4 of 5 bubbles'
				break
			    if t.find('bubble_50') == 0:
				rating = '5 of 5 bubbles'
				break
			print 'rating: %s' % rating
		    except Exception, e:
			print 'Error in getting rating - %s' % (str(e))
		    try:
			review_date = inreview.find('span', attrs={'class':'ratingDate relativeDate'}).get('title').lstrip().rstrip()
			review_date_format = "fm1" #November 3, 2015
			print 'review_date: %s' % review_date
			try:
                    	    tlist =  review_date.rstrip().lstrip().split(" ")
                    	    if len(tlist) == 3:
                        	tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                        	print tstr
                        	review_dt = datetime.strptime(tstr, '%Y-%B-%d')
				print '-------------------------'
                        	print 'REVIEW_DT: %s' % review_dt
				print '-------------------------'
                	except Exception, e:
                    	    print 'Error in review date coversion fm1 - %s' % (str(e))
		    except Exception, e:
			print 'Error in getting review_date1 - %s' % (str(e))
			try:
			    review_date = inreview.find('span', attrs={'class':'ratingDate relativeDate'}).get('title').lstrip().rstrip()
			    review_date_format = "fm2" #2015-09-29
			    print 'review_date: %s' % review_date
			    try:
                    		tlist =  review_date.rstrip().lstrip().split("-")
                    		if len(tlist) == 3:
                        	    tstr = tlist[0] + "-" + tlist[1] + "-" + tlist[2]
                        	    print tstr
                        	    review_dt = datetime.strptime(tstr, '%Y-%m-%d')
				    print '-------------------------'
                        	    print 'REVIEW_DT: %s' % review_dt
				    print '-------------------------'
                	    except Exception, e:
                    		print 'Error in review date coversion fm2 - %s' % (str(e))
			except Exception, e:
			    print 'Error in getting review_date2. - %s' % (str(e))
			    try:
				print 'final try'
				review_date = inreview.find('span', attrs={'class':'ratingDate relativeDate'}).get('title').lstrip().rstrip()
				review_date_format = "fm3"
				print 'review_date: %s' % review_date
				try:
				    tlist =  review_date.rstrip().lstrip().split(" ")
				    if len(tlist) == 4:
					tstr = tlist[3] + "-" + tlist[1] + "-" + tlist[2].rstrip(',')
					print tstr
					review_dt = datetime.strptime(tstr, '%Y-%B-%d')
					print '-------------------------'
					print 'REVIEW_DT: %s' % review_dt
					print '-------------------------'
				except Exception, e:
				    print 'Error in review date coversion fm3 - %s' % (str(e))
			    except Exception, e:
				print 'URGENT: Error in getting review_date3. Skipping... - %s' % (str(e))
		    try:
			manager_response_header = inreview.find('div',attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).text.lstrip().rstrip()
			print 'manager_response_header: %s' % manager_response_header
		    except Exception, e:
			print 'Error in getting manager_response_header - %s' % (str(e))
		    try:
			#manager_response_text = inreview.find('div',attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			manager_response_text_overall = inreview.find('div',attrs={'class':'mgrRspnInline'}).text.lstrip().rstrip()
			manager_response_date_text = inreview.find('div',attrs={'class':'mgrRspnInline'}).find('span', attrs={'class':'responseDate'}).text.lstrip().rstrip()
			print 'manager_response_date_text: %s' % (manager_response_date_text)
			if manager_response_date_text:
			    tlist = manager_response_text_overall.split(manager_response_date_text)
			    manager_response_text = ''.join(tlist)
			else:
			    manager_response_text = manager_response_text_overall
			print 'manager_response_text: %s' % manager_response_text
			if len(manager_response_text) > 0:
			    has_manager_response = True
		    except Exception, e:
			print 'Error in getting manager_response_text - %s' % (str(e))

		    try:
			if len(reviewer_total_reviews.rstrip().lstrip()) > 0:
			    tlist = reviewer_total_reviews.rstrip().lstrip().split(" ")
			    if len(tlist) > 0:
			        tint = int((tlist[0]).replace(',',''))
			        reviewer_total_reviews = tint
			if len(reviewer_hotel_reviews.rstrip().lstrip()) > 0:
			    tlist = reviewer_hotel_reviews.rstrip().lstrip().split(" ")
			    if len(tlist) > 0:
				tint = int((tlist[0]).replace(',',''))
			        reviewer_hotel_reviews = tint
			if len(reviewer_helpful_votes.rstrip().lstrip()) > 0:
			    tlist = reviewer_helpful_votes.rstrip().lstrip().split(" ")
			    if len(tlist) > 0:
				tint = int((tlist[0]).replace(',',''))
			        reviewer_helpful_votes = tint
		    except Exception, e:
			print 'Error in getting partial reviewer_total_reviews reviewer_hotel_reviews reviewer_helpful_votes'
		    print 'reviewer_total_reviews: %s' % (reviewer_total_reviews)
		    print 'reviewer_hotel_reviews: %s' % (reviewer_hotel_reviews)
		    print 'reviewer_helpful_votes: %s' % (reviewer_helpful_votes)

		    response_data['rating'] = rating
		    response_data['title'] = title
		    response_data['review_text'] = review_text
		    response_data['review_date'] = review_date
		    response_data['review_date_format'] = review_date_format
		    response_data['reviewer_name'] = reviewer_name
		    response_data['reviewer_location'] = reviewer_location
		    response_data['reviewer_c_level'] = reviewer_c_level
		    response_data['reviewer_total_reviews'] = reviewer_total_reviews
		    response_data['reviewer_hotel_reviews'] = reviewer_hotel_reviews
		    response_data['reviewer_helpful_votes'] = reviewer_helpful_votes
		    response_data['has_manager_response'] = has_manager_response
		    response_data['manager_response_header'] = manager_response_header
		    response_data['manager_response_text'] = manager_response_text


		    print response_data


                    # UPDATE MONGODB
                    try:
			upserted_review_id = None
                        mongo_review = MongoReview()
                        find_param = {}
                        find_param['identifier'] = reviewid
                        find_param['hotel_id'] = hotel.hotel_id
                        find_param['source'] = 2 #Tripadvisor
                        find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
                        update_param = OrderedDict()
                        find_count = mongo_review.count(find_param)
                        if find_count == 0:
                            print 'partial create new tripadvisor MongoReview'
                            update_param['_id'] = uuid.uuid4().hex[:16].lower()
                        else:
                            print 'partial existing tripadvisor MongoReview found'
                        update_param['title'] = title
                        update_param['comment'] = review_text
                        update_param['rating'] = rating
        		rating_number = convert_rating_to_number_tripadvisor(rating)
        		update_param['rating_number'] = rating_number
        		update_param['rating_out_of_5'] = rating_number
                        update_param['url'] = permalink
                        author = {}
                        author['name'] = reviewer_name
                        author['location'] = reviewer_location
                        author['contributor_level'] = reviewer_c_level
			author['total_reviews'] = reviewer_total_reviews
		 	author['hotel_reviews'] = reviewer_hotel_reviews
		 	author['helpful_votes'] = reviewer_helpful_votes
                        update_param['author'] = author
                        if isinstance(review_dt, datetime):
                            update_param['review_date'] = review_dt
                        else:
                            print 'partial tripadvisor No review_date'
                            alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('tripadvisor', hotel.hotel_id, reviewid, title, reviewer_name)
                            mongo_log_alert(type='scrape', info=alert_msg)
                        update_param['has_manager_response'] = has_manager_response
                        update_param['manager_response'] = manager_response_header + ' # ' + manager_response_text
                        update_param['is_partial'] = True
                        if find_count == 0:
                            update_param['date_created'] = datetime.now()
                        else:
                            update_param['date_updated'] = datetime.now()
                        print 'partial Try saving tripadvisor MongoReview'
                        mongo_review.set_find_param(find_param)
                        print 'try setting update_param'
                        mongo_review.set_update_param(update_param)
                        mongo_result = mongo_review.update()
                        if mongo_result:
			    upserted_review_id = mongo_result.upserted_id
                            print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
                            print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
                            print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
                            print 'tripadvisor MongoReview updated'
                    except Exception, e:
                        print 'partial Error in updating tripadvisor MongoReview - %s' % (str(e))

		    # UPDATE POSTGRES
		    try:
                        print 'Check in DB for the review'
                        reviews = Review.objects.filter(identifier=reviewid, hotel=hotel, is_unavailable=False).order_by('-date_created')
                        print 'reviews len: %s' % len(reviews)
                        if len(reviews) == 0:
                            print 'CREATING PARTIAL new reviewer and review'
			    if len(reviewer_name) > 0:
                                reviewer = Reviewer.objects.create(source=sourceid)
				reviewer.name = reviewer_name
				reviewer.location = reviewer_location
				if reviewer_c_level:
				    reviewer.contributor_level = reviewer_c_level
				if reviewer_total_reviews:
			 	    reviewer.total_reviews = reviewer_total_reviews
				if reviewer_hotel_reviews:
			 	    reviewer.hotel_reviews = reviewer_hotel_reviews
				if reviewer_helpful_votes:
			 	    reviewer.helpful_votes = reviewer_helpful_votes
				try:
				    print 'save reviewer'
				    reviewer.save()
				    print 'reviewer saved'
                                    review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
				    review.title = title
				    review.comment = review_text
				    review.rating = rating
                                    review.url = permalink
				    try:
					if isinstance(review_dt, datetime):
					    review.review_date = review_dt
					else:
					    print 'URGENT: ERROR review_dt missing'
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    try:
						review.delete()
						print 'review deleted'
					    except Exception, e:
						print 'Error in deleting review - %s' % (str(e))
					    return 'error'
				    except Exception, e:
					print 'Error in review_dt assignment - %s' % (str(e))
					print 'deleteing reviewer'
					reviewer.delete()
					print 'reviewer deleted'
					try:
					    review.delete()
					    print 'review deleted'
					except Exception, e:
					    print 'Error in deleting review - %s' % (str(e))
					return 'error'
				    review.has_manager_response = has_manager_response
				    review.manager_response = manager_response_header + ' # ' + manager_response_text
				    review.response_posted_checkbox = False
				    review.is_non_english = False
				    review.is_partial = True
                                    try:
                                        review.save()
				    	print 'review saved'

					#Update review_id in mongodb
                                        if upserted_review_id:
                                            try:
                                                print 'Update review_id %s' % (review.review_id)
                                                mongo_review = MongoReview()
                                                find_param = {}
                                                find_param['_id'] = upserted_review_id
                                                update_param = {}
                                                update_param['review_id'] = review.review_id
                                                print 'Try saving review_id tripadvisor MongoReview'
                                                mongo_review.set_find_param(find_param)
                                                print 'try setting review_id update_param'
                                                mongo_review.set_update_param(update_param)
                                                mongo_result = mongo_review.update()
                                                if mongo_result:
                                                    print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                                    print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                                    print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                                    print 'tripadvisor MongoReview review_id updated'
                                            except Exception, e:
                                                print 'Error in updating review_id in mongodb: %s' % (str(e))
                                        else:
                                            print 'upserted_review_id is None'

					return 'success'
                                    except Exception, e:
                                        print 'Error in executing save of review - new record - %s' % (str(e))
					print 'deleteing reviewer'
					reviewer.delete()
					print 'reviewer deleted'
					try:
					    review.delete()
					    print 'review deleted'
					except Exception, e:
					    print 'Error in deleting review - %s' % (str(e))
                                except Exception, e:
                                    print 'Error in executing save of reviewer - %s' % (str(e))
			    else:
				print 'reviewer_name is empty'
				return 'error'
                        else:
                            print 'EXISTING reviewer and review found'
                            review = reviews[0]
                            if len(reviews) > 1:
                                print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
			    print 'review.is_partial: %s' % (review.is_partial)
			    if review.is_partial == True or review.is_partial == False:
				review.title = title
                                review.comment = review_text
                                review.rating = rating
                                review.url = permalink
                                try:
                                    if isinstance(review_dt, datetime):
                                        review.review_date = review_dt
                                    else:
                                        print 'URGENT: ERROR review_dt missing'
                                except Exception, e:
                                    print 'Error in review_dt assignment - %s' % (str(e))
                                review.has_manager_response = has_manager_response
                                review.manager_response = manager_response_header + ' # ' + manager_response_text
                                try:
                                    review.save()
				    print 'review updated'
				    return 'success'
                                except Exception, e:
                                    print 'URGENT: Error in executing save of review - existing record - %s' % (str(e))
				    return 'error'
			    #else:
			#	print 'Review found with is_partial as False IS FULL'
                    except Exception, e:
                        print 'Error in checking in DB for the review - %s' % (str(e))
		except Exception, e:
		    print 'Errrrr - %s' % (str(e))
	    except Exception, e:
		print 'Error1 - %s' % (str(e))
	except Exception, e:
	    print 'Error2 - %s' % (str(e))
    except Exception, e:
	print 'process_partial_review - %s' % (str(e))
    return 'error'

def helper_scrape_tripadvisor_by_review_id(uid, reviewid, inputurl, firstrun):
    print 'helper_scrape_tripadvisor_by_review_id: %s -- %s - %s - %s' % (uid, reviewid, inputurl, firstrun)
    source = 'tripadvisor'
    sourceid = 2
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
        try:
	    print 'inputurl: %s' % (inputurl)
	    if len(inputurl) == 0:
		print 'URGENT: Invalid input url. Returning...'
		return 'error'
	    try:
		#opener = urllib2.build_opener()
		#opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		#response = opener.open(inputurl)
		#page = response.read()
		#soup = BeautifulSoup(page, "html5lib")
		#opener.close()

		# m(1) - requests / m(2) - urllib2
                #args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':1 }
                #data_server_url = 'http://{0}/q/'.format(DATA_SERVER_1)
                #print 'data_server_url: %s' % (data_server_url)
                #connect_timeout, read_timeout = 5.0, 20.0
                #response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
                #page = response.content

		args = { 'auth' :'zc3wiu4e6z1nwgye', 'q': inputurl}
                data_server_url = 'http://{0}/bnuy6vwh89enjkyo/'.format(DATA_SERVER_3_SELENIUM)
                print 'data_server_url_3: %s' % (data_server_url)
                connect_timeout, read_timeout = 10.0, 30.0
                response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
		print response.url
                page = response.content

		soup = BeautifulSoup(page, "html5lib")

		try:
		    inreview = soup.find('div', attrs={'id':reviewid})
		    if inreview is None:
			print 'No review found. Not a valid page. Returning...'
			return 'error'
		    try:
			review_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			print 'review_text check: %s' % (review_text)
			if not review_text:
			    print 'review_text is not present, retry..'
			    id = reviewid.split('_')[1]
			    print 'retry id: %s' % (id)
			    retry_inputurl = 'https://www.tripadvisor.com/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS&metaReferer=ShowUserReviewsHotels&contextChoice=SUR&reviews={0}'.format(id)
			    print 'retry_inputurl: %s' % (retry_inputurl)
			    args = { 'auth' :'zc3wiu4e6z1nwgye', 'q': retry_inputurl}
                	    data_server_url = 'http://{0}/bnuy6vwh89enjkyo/'.format(DATA_SERVER_3_SELENIUM)
                	    print 'retry data_server_url_3: %s' % (data_server_url)
                	    connect_timeout, read_timeout = 10.0, 30.0
                	    response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
                	    print 'retry: %s' % (response.url)
                	    page = response.content
                	    soup = BeautifulSoup(page, "html5lib")

		    except Exception, e:
			print 'Error in checking review_text presence: %s' % (str(e))
		    try:
			response_data = {}
			rating = title = review_text = review_pos = review_neg = review_location = review_date = review_date_format = review_dt = room_tip = rating_list_title = rating_list_text = ''
			reviewer_name = reviewer_location = reviewer_c_level = reviewer_total_reviews = reviewer_hotel_reviews = reviewer_helpful_votes = ''
			manager_response_header = manager_response_text = manager_response_date = manager_response_date_format = manager_response_dt = ''
			has_manager_response = False
			try:
			    reviewer_name = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'member_info'}).find('div', attrs={'class':'username'}).find('span').text.lstrip().rstrip()
			    print 'reviewer_name: %s' % reviewer_name
			except Exception, e:
			    print 'Error in getting reviewer_name span - %s' % (str(e))
			    try:
				reviewer_name = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'member_info'}).find('div', attrs={'class':'username'}).text.lstrip().rstrip()
				print 'reviewer_name: %s' % reviewer_name
			    except Exception, e:
				print 'Error in getting reviewer_name - %s' % (str(e))
			try:
			    reviewer_location = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'member_info'}).find('div', attrs={'class':'location'}).text.lstrip().rstrip()
			    print 'reviewer_location: %s' % reviewer_location
			except Exception, e:
			    print 'Error in getting reviewer_location - %s' % (str(e))
			try:
			    tlist = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'levelBadge'}).get('class')
			    for t in tlist:
				if t.find('lvl_') >= 0:
				    reviewer_c_level = str(int(t[len('lvl_'):]))
				    break
			    print 'reviewer_c_level: %s' % reviewer_c_level
			except Exception, e:
			    print 'Error in getting reviewer_c_level - %s' % (str(e))
			try:
			    reviewer_total_reviews = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'reviewerBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			    #reviewer_total_reviews = reviewer_total_reviews.split(' ')[0]
			    #reviewer_total_reviews = int(reviewer_total_reviews.replace(',',''))
			    print 'reviewer_total_reviews: %s' % reviewer_total_reviews
			except Exception, e:
			    print 'Error in getting reviewer_total_reviews - %s' % (str(e))
			try:
			    reviewer_hotel_reviews = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'contributionReviewBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			    #reviewer_hotel_reviews = reviewer_hotel_reviews.split(' ')[0]
			    #reviewer_hotel_reviews = int(reviewer_hotel_reviews.replace(',',''))
			    print 'reviewer_hotel_reviews: %s' % reviewer_hotel_reviews
			except Exception, e:
			    print 'Error in getting reviewer_hotel_reviews - %s' % (str(e))
			try:
			    reviewer_helpful_votes = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'memberBadging'}).find('div', attrs={'class':'helpfulVotesBadge'}).find('span', attrs={'class':'badgeText'}).text.lstrip().rstrip()
			    #reviewer_helpful_votes = reviewer_helpful_votes.split(' ')[0]
			    #reviewer_helpful_votes = int(reviewer_helpful_votes.replace(',',''))
			    print 'reviewer_helpful_votes: %s' % reviewer_helpful_votes
			except Exception, e:
			    print 'Error in getting reviewer_helpful_votes - %s' % (str(e))
			try:
			    tstr = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'quote'}).text.lstrip().rstrip()
			    #title = tstr[1:len(tstr)-1].lstrip().rstrip()
			    title = tstr.lstrip().rstrip()
			    print 'title: %s' % title
			except Exception, e:
			    print 'Error in getting title - %s' % (str(e))
			try:
			    #review_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			    review_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'prw_rup prw_reviews_text_summary_hsx'}).find('div', attrs={'class':'entry'}).find('p').text.lstrip().rstrip()
			    print 'review_text: %s' % review_text
			except Exception, e:
			    print 'Error in getting review_text - %s' % (str(e))
			try:
			    rating = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'rate'}).find('img').get('alt').lstrip().rstrip()
			    #rating = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ui_bubble_rating'}).get('alt').lstrip().rstrip()
			    print 'rating tripadvisor full: %s' % rating
			except Exception, e:
			    print 'Error in getting rating tripadvisor - %s' % (str(e))
			    print 'retry for rating'
			    try:
			        rating = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ui_bubble_rating'}).get('alt').lstrip().rstrip()
			        print 'rating tripadvisor full: %s' % rating
			    except Exception, e:
			        print 'Error in getting rating tripadvisor - %s' % (str(e))
				try:
                        	    rating = inreview.find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ui_bubble_rating'}).get('class')
                        	    print 'rating tripadvisor partial: %s' % rating
                        	    tlist = rating
                        	    for t in tlist:
                            	        if t.find('bubble_10') == 0:
                                	    rating = '1 of 5 bubbles'
                                	    break
                            		if t.find('bubble_20') == 0:
                                	    rating = '2 of 5 bubbles'
                                	    break
                            		if t.find('bubble_30') == 0:
                                	    rating = '3 of 5 bubbles'
                                	    break
                            		if t.find('bubble_40') == 0:
                                	    rating = '4 of 5 bubbles'
                                	    break
                            		if t.find('bubble_50') == 0:
                                	    rating = '5 of 5 bubbles'
                                	    break
                        	    print 'rating tripadvisor full: %s' % rating
                    		except Exception, e:
                        	    print 'Error in getting rating tripadvisor  - %s' % (str(e))
				    rating = None

			try:
			    review_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ratingDate'}).get('title').lstrip().rstrip()
			    review_date_format = "fm1" #November 3, 2015
			    print 'review_date: %s' % review_date
			    try:
                    		tlist =  review_date.rstrip().lstrip().split(" ")
                    		if len(tlist) == 3:
                        	    tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                        	    print tstr
                        	    review_dt = datetime.strptime(tstr, '%Y-%B-%d')
				    print '-------------------------'
                        	    print 'REVIEW_DT: %s' % review_dt
				    print '-------------------------'
                	    except Exception, e:
                    		print 'Error in review date coversion fm1 - %s' % (str(e))
			except Exception, e:
			    print 'Error in getting review_date1 - %s' % (str(e))
			    try:
				review_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ratingDate'}).get('content').lstrip().rstrip()
				review_date_format = "fm2" #2015-09-29
				print 'review_date: %s' % review_date
				try:
                    		    tlist =  review_date.rstrip().lstrip().split("-")
                    		    if len(tlist) == 3:
                        		tstr = tlist[0] + "-" + tlist[1] + "-" + tlist[2]
                        		print tstr
                        		review_dt = datetime.strptime(tstr, '%Y-%m-%d')
					print '-------------------------'
                        		print 'REVIEW_DT: %s' % review_dt
					print '-------------------------'
                		except Exception, e:
                    		    print 'Error in review date coversion fm2 - %s' % (str(e))
			    except Exception, e:
				print 'Error in getting review_date2. - %s' % (str(e))
				try:
				    print 'final try'
				    review_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating'}).find('span', attrs={'class':'ratingDate'}).text.lstrip().rstrip()
				    review_date_format = "fm3"
				    print 'review_date: %s' % review_date
				    try:
				        tlist =  review_date.rstrip().lstrip().split(" ")
					if len(tlist) == 4:
					    tstr = tlist[3] + "-" + tlist[1] + "-" + tlist[2].rstrip(',')
					    print tstr
					    review_dt = datetime.strptime(tstr, '%Y-%B-%d')
					    print '-------------------------'
					    print 'REVIEW_DT: %s' % review_dt
					    print '-------------------------'
				    except Exception, e:
					print 'Error in review date coversion fm3 - %s' % (str(e))
				except Exception, e:
				    print 'URGENT: Error in getting review_date3. Skipping... - %s' % (str(e))
				    return 'error'
			try:
			    if firstrun == False: #update
                                if hotel.tripadvisor_update_window is None:
                                    dt_threshold = datetime.now() - timedelta(days=30)
                                else:
                                    dt_threshold = datetime.now() - timedelta(days=int(hotel.tripadvisor_update_window))
                                print 'spl dt_threshold: %s' % dt_threshold
				#count_beyond_date_tripadvisor = 2 #Forced setting
        			hotel = Hotel.objects.get(hotel_id=uid)
        			print hotel
				count_beyond_date_tripadvisor = hotel.tripadvisor_reviews_beyond_threshold
				print 'intital count_beyond_date_tripadvisor: %s' % (count_beyond_date_tripadvisor)
                                if review_dt >= dt_threshold:
                                    print 'REVIEW FOUND in update window'
                                else:
				    count_beyond_date_tripadvisor = count_beyond_date_tripadvisor + 1
				    print 'count_beyond_date_tripadvisor: %s' % (count_beyond_date_tripadvisor)
				    if count_beyond_date_tripadvisor >= 2:
                                        print '%s - BEYOND UPDATE WINDOW. RETURNING...' % (count_beyond_date_tripadvisor)
                                        return 'beyond'
				    else:
					#count_beyond_date_tripadvisor = count_beyond_date_tripadvisor + 1
					print 'CRAZY - old review found'
				    hotel.tripadvisor_reviews_beyond_threshold = count_beyond_date_tripadvisor
				    hotel.save()
				    print 'hotel tripadvisor_reviews_beyond_threshold updated with %s' % (count_beyond_date_tripadvisor)
			except Exception, e:
			    print 'URGENT Error in check dt_threshold for update. Returning...- %s' %(str(e))
			try:
			    tstr = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'entry'}).find('div', attrs={'class':'inlineRoomTip'}).text.lstrip().rstrip()
			    textra = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'entry'}).find('div', attrs={'class':'inlineRoomTip'}).find('div').text.lstrip().rstrip()
			    if tstr.find(textra) > 0:
				tstr = tstr[0:tstr.find(textra)]
			    textra = 'Room Tip:'
			    if tstr.find(textra) == 0:
				tstr = tstr[tstr.find(textra):]
			    room_tip = tstr
			    print 'room_tip: %s' % room_tip
			except Exception, e:
			    print 'Error in getting room_tip - %s' % (str(e))
			try:
			    rating_list_title = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating-list'}).find('span', attrs={'class':'recommend-titleInline'}).text.lstrip().rstrip()
			    print 'rating_list_title: %s' % rating_list_title
			except Exception, e:
			    print 'Error in getting rating_list_title - %s' % (str(e))
			try:
			     links =  soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'rating-list'}).findAll('li', attrs={'class':'recommend-answer'})
			     for l in links:
				rating_list_text = rating_list_text + l.find('div', attrs={'class':'recommend-description'}).text.lstrip().rstrip() + ': ' + l.find('span', attrs={'class':'rate'}).find('img').get('alt').lstrip().rstrip() + ' | '
			     print 'rating_list_text: %s' % rating_list_text
			except Exception, e:
			    print 'Errro in getting rating_list_text - %s' % (str(e))
			try:
			    #manager_response_header = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).text.lstrip().rstrip()
			    manager_response_header_overall = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).text.lstrip().rstrip()
			    manager_response_date_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('span', attrs={'class':'responseDate'}).text.lstrip().rstrip()
			    print 'manager_response_date_text: %s' % (manager_response_date_text)
			    if manager_response_date_text:
			        tlist = manager_response_header_overall.split(manager_response_date_text)
			        manager_response_header = ''.join(tlist)
			    else:
				manager_response_header = manager_response_header_overall
			    print 'manager_response_header: %s' % manager_response_header
			except Exception, e:
			    print 'Error in getting manager_response_header - %s' % (str(e))
			try:
			    #manager_response_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'displayText'}).text.lstrip().rstrip()
			    manager_response_text = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'prw_reviews_text_summary_hsx'}).text.lstrip().rstrip()
			    print 'manager_response_text: %s' % manager_response_text
			    if manager_response_text:
			        has_manager_response = True
			except Exception, e:
			    print 'Error in getting manager_response_text - %s' % (str(e))
			try:
			    #manager_response_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).find('span', attrs={'class':'relativeDate'}).get('title').lstrip().rstrip()
			    manager_response_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).find('span', attrs={'class':'res_date'}).get('title').lstrip().rstrip()
			    print 'manager_response_date: %s' % manager_response_date
			except Exception, e:
			    print 'Error in getting manager_response_date1 - %s' % (str(e))
			    try:
				manager_response_date = soup.find('div', attrs={'id':reviewid}).find('div', attrs={'class':'mgrRspnInline'}).find('div', attrs={'class':'header'}).find('span', attrs={'class':'res_date'}).text.lstrip().rstrip()
				print 'manager_response_date: %s' % manager_response_date
			    except Exception, e:
				print 'Error in getting manager_response_date2 - %s' % (str(e))
			try:
			    if manager_response_date.find(',') > 0:
				manager_response_date_format = "fm2" #June 15, 2011
				print 'manager_response_date_format: %s' % manager_response_date_format
				try:
                    		    tlist =  manager_response_date.rstrip().lstrip().split(" ")
                    		    if len(tlist) == 3:
                        		tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                        		print tstr
                        		manager_response_dt = datetime.strptime(tstr, '%Y-%B-%d')
                        		print 'manager_response_dt: %s' % manager_response_dt
					#has_manager_response = True
                		except Exception, e:
                    		    print 'Error in manager response date coversion fm2 - %s' % (str(e))
			    else:
				manager_response_date_format = "fm1" #15 June 2011
				print 'manager_response_date_format: %s' % manager_response_date_format
				try:
                    		    tlist =  manager_response_date.rstrip().lstrip().split(" ")
                    		    if len(tlist) == 3:
                        		tstr = tlist[2] + "-" + tlist[1] + "-" + tlist[0].rstrip(',')
                        		print tstr
                        		manager_response_dt = datetime.strptime(tstr, '%Y-%B-%d')
                        		print 'manager_response_dt: %s' % manager_response_dt
					#has_manager_response = True
                		except Exception, e:
                    		    print 'Error in manager response date coversion fm1 - %s' % (str(e))
			except Exception, e:
			    print 'Error in processing manager_response_date - %s' % (str(e))


			response_data['rating'] = rating
			response_data['title'] = title
			response_data['review_text'] = review_text
			response_data['review_date'] = review_date
			response_data['review_date_format'] = review_date_format
			response_data['rating_list_title'] = rating_list_title
			response_data['rating_list_text'] = rating_list_text
			response_data['room_tip'] = room_tip
			response_data['reviewer_name'] = reviewer_name
			response_data['reviewer_location'] = reviewer_location
			response_data['reviewer_c_level'] = reviewer_c_level
			response_data['reviewer_total_reviews'] = reviewer_total_reviews
			response_data['reviewer_hotel_reviews'] = reviewer_hotel_reviews
			response_data['reviewer_helpful_votes'] = reviewer_helpful_votes
			response_data['has_manager_response'] = has_manager_response
			response_data['manager_response_date'] = manager_response_date
			response_data['manager_response_date_format'] = manager_response_date_format
			response_data['manager_response_header'] = manager_response_header
			response_data['manager_response_text'] = manager_response_text


		 	print response_data

		        try:
			    if len(reviewer_total_reviews.rstrip().lstrip()) > 0:
			        tlist = reviewer_total_reviews.rstrip().lstrip().split(" ")
			        if len(tlist) > 0:
			            tint = int((tlist[0]).replace(',',''))
			            reviewer_total_reviews = tint
			    if len(reviewer_hotel_reviews.rstrip().lstrip()) > 0:
			        tlist = reviewer_hotel_reviews.rstrip().lstrip().split(" ")
			        if len(tlist) > 0:
				    tint = int((tlist[0]).replace(',',''))
			            reviewer_hotel_reviews = tint
			    if len(reviewer_helpful_votes.rstrip().lstrip()) > 0:
			        tlist = reviewer_helpful_votes.rstrip().lstrip().split(" ")
			        if len(tlist) > 0:
				    tint = int((tlist[0]).replace(',',''))
			            reviewer_helpful_votes = tint
		        except Exception, e:
			    print 'Error in getting partial reviewer_total_reviews reviewer_hotel_reviews reviewer_helpful_votes'


                        # UPDATE MONGODB
                        try:
			    upserted_review_id = None
                            mongo_review = MongoReview()
                            find_param = {}
                            find_param['identifier'] = reviewid
                            find_param['hotel_id'] = hotel.hotel_id
                            find_param['source'] = 2 #Tripadvisor
                            find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
                            update_param = OrderedDict()
                            find_count = mongo_review.count(find_param)
                            if find_count == 0:
                                print 'create new tripadvisor MongoReview'
                                update_param['_id'] = uuid.uuid4().hex[:16].lower()
                            else:
                                print 'existing tripadvisor MongoReview found'
                            update_param['title'] = title
                            update_param['comment'] = review_text
                            update_param['rating'] = rating
        		    rating_number = convert_rating_to_number_tripadvisor(rating)
        		    update_param['rating_number'] = rating_number
        		    update_param['rating_out_of_5'] = rating_number
                            update_param['rating_list_title'] = rating_list_title
                            update_param['rating_list_text'] = rating_list_text
                            update_param['room_tip'] = room_tip
                            update_param['url'] = inputurl
                            author = {}
                            author['name'] = reviewer_name
                            author['location'] = reviewer_location
                            author['contributor_level'] = reviewer_c_level
                            author['total_reviews'] = reviewer_total_reviews
                            author['hotel_reviews'] = reviewer_hotel_reviews
                            author['helpful_votes'] = reviewer_helpful_votes
                            update_param['author'] = author
                            if isinstance(review_dt, datetime):
                                update_param['review_date'] = review_dt
                            else:
                                print 'tripadvisor No review_date'
                                alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('tripadvisor', hotel.hotel_id, reviewid, title, reviewer_name)
                                mongo_log_alert(type='scrape', info=alert_msg)
                            update_param['has_manager_response'] = has_manager_response
                            if isinstance(manager_response_dt, datetime):
                                update_param['manager_response_date'] = manager_response_dt
                            update_param['manager_response'] = manager_response_header + ' # ' + manager_response_text
			    unset_param = {}
                            unset_param['is_partial'] = ''
                            if find_count == 0:
                                update_param['date_created'] = datetime.now()
                            else:
                                update_param['date_updated'] = datetime.now()
                            print 'Try saving tripadvisor MongoReview'
                            mongo_review.set_find_param(find_param)
                            mongo_review.set_update_param(update_param)
                            mongo_review.set_unset_param(unset_param)
                            mongo_result = mongo_review.update()
                            if mongo_result:
				upserted_review_id = mongo_result.upserted_id
                                print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
                                print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
                                print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
                                print 'tripadvisor MongoReview updated'
                        except Exception, e:
                            print 'Error in updating tripadvisor MongoReview - %s' % (str(e))

			# UPDATE POSTGRES
			try:
                            print 'Check in DB for the review'
                            reviews = Review.objects.filter(identifier=reviewid, hotel=hotel, is_unavailable=False).order_by('-date_created')
                            print 'reviews len: %s' % len(reviews)
                            if len(reviews) == 0:
                                print 'CREATING new reviewer and review'
				if len(reviewer_name) > 0:
                                    reviewer = Reviewer.objects.create(source=sourceid)
				    reviewer.name = reviewer_name
				    reviewer.location = reviewer_location
				    reviewer.contributor_level = reviewer_c_level
			 	    reviewer.total_reviews = reviewer_total_reviews
			 	    reviewer.hotel_reviews = reviewer_hotel_reviews
			 	    reviewer.helpful_votes = reviewer_helpful_votes
				    try:
					print 'save reviewer'
					reviewer.save()
					print 'reviewer saved'
                                    	review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
					review.title = title
					review.comment = review_text
					review.rating = rating
					review.rating_list_title = rating_list_title
					review.rating_list_text = rating_list_text
					review.room_tip = room_tip
					review.url = inputurl
					try:
					    if isinstance(review_dt, datetime):
					        review.review_date = review_dt
					    else:
						print 'URGENT: ERROR review_dt missing'
					        print 'deleteing reviewer'
					        reviewer.delete()
					        print 'reviewer deleted'
						try:
						    review.delete()
						    print 'review deleted'
						except Exception, e:
						    print 'Error in deleting review - %s' % (str(e))
						return 'error'
					except Exception, e:
					    print 'Error in review_dt assignment - %s' % (str(e))
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    try:
						review.delete()
						print 'review deleted'
					    except Exception, e:
						print 'Error in deleting review - %s' % (str(e))
					    return 'error'
					review.has_manager_response = has_manager_response
					review.manager_response = manager_response_header + ' # ' + manager_response_text
					review.response_posted_checkbox = False
					review.is_non_english = False
					review.is_partial = False
					try:
                                            if isinstance(manager_response_dt, datetime):
                                                review.manager_response_date = manager_response_dt
                                            else:
                                                print 'URGENT: ERROR manager_response_dt missing'
                                        except Exception, e:
                                            print 'Error in manager_response_dt assignment - %s' % (str(e))
                                    	try:
                                            review.save()
				    	    print 'review saved'

					    #Update review_id in mongodb
                                            if upserted_review_id:
                                                try:
                                                    print 'Update review_id %s' % (review.review_id)
                                                    mongo_review = MongoReview()
                                                    find_param = {}
                                                    find_param['_id'] = upserted_review_id
                                                    update_param = {}
                                                    update_param['review_id'] = review.review_id
                                                    print 'Try saving review_id tripadvisor MongoReview'
                                                    mongo_review.set_find_param(find_param)
                                                    print 'try setting review_id update_param'
                                                    mongo_review.set_update_param(update_param)
                                                    mongo_result = mongo_review.update()
                                                    if mongo_result:
                                                        print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                                        print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                                        print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                                        print 'tripadvisor MongoReview review_id updated'
                                                except Exception, e:
                                                    print 'Error in updating review_id in mongodb: %s' % (str(e))
                                            else:
                                                print 'upserted_review_id is None'

					    return 'success'
                                    	except Exception, e:
                                            print 'Error in executing save of review - new record - %s' % (str(e))
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    try:
						review.delete()
						print 'review deleted'
					    except Exception, e:
						print 'Error in deleting review - %s' % (str(e))
                                    except Exception, e:
                                        print 'Error in executing save of reviewer - %s' % (str(e))
				else:
				    print 'reviewer_name is empty'
				    return 'error'
                            else:
                                print 'EXISTING reviewer and review found'
                                review = reviews[0]
                                if len(reviews) > 1:
                                    print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
				review.title = title
                                review.comment = review_text
                                review.rating = rating
                                review.rating_list_title = rating_list_title
                                review.rating_list_text = rating_list_text
                                review.room_tip = room_tip
                                review.url = inputurl
                                try:
                                    if isinstance(review_dt, datetime):
                                        review.review_date = review_dt
                                    else:
                                        print 'URGENT: ERROR review_dt missing'
                                except Exception, e:
                                    print 'Error in review_dt assignment - %s' % (str(e))
                                review.has_manager_response = has_manager_response
                                review.manager_response = manager_response_header + ' # ' + manager_response_text
				review.is_partial = False
                                try:
                                    if isinstance(manager_response_dt, datetime):
                                        review.manager_response_date = manager_response_dt
                                    else:
                                        print 'URGENT: ERROR manager_response_dt missing'
                                except Exception, e:
                                    print 'Error in manager_response_dt assignment - %s' % (str(e))
                                try:
                                    review.save()
				    print 'review updated'
				    return 'success'
                                except Exception, e:
                                    print 'URGENT: Error in executing save of review - existing record - %s' % (str(e))
				    return 'error'
                        except Exception, e:
                            print 'Error in checking in DB for the review - %s' % (str(e))
		    except Exception, e:
			print 'Erorr in processing review - %s' % (str(e))
		except Exception, e:
		    print 'Errrrr - %s' % (str(e))
	    except Exception, e:
		print 'Error in making soup - %s' % (str(e))
	except Exception, e:
	    print 'Error in processing hotel - %s' % (str(e))
    except Exception, e:
	print 'helper_scrape_tripadvisor_by_review_id - %s' % (str(e))
    return 'error'

def helper_scrape_google_by_hotel_id(uid):
    print 'helper_scrape_google_by_hotel_id'
    source = 'google'
    sourceid = 5
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print hotel
        #hotel.is_google_update_running = True
        #hotel.save()
        try:
            if hotel.is_gmb_enabled is False:
		print 'location is not gmb enabled - %s' % (hotel)
		return
            if hotel.review_location_id is None or len(hotel.review_location_id) == 0:
                print 'review_location_id missing. Returning...'
                hotel.google_last_update_status = 'review_location_id missing'
                hotel.is_google_update_running = False
                hotel.google_last_update_date = datetime.now()
                hotel.save()
                return
            try:
                data_server_url = ''.format(hotel.review_location_id)
                print 'data_server_url: %s' % (data_server_url)
                connect_timeout, read_timeout = 5.0, 20.0
                response = requests.get(data_server_url, timeout=(connect_timeout, read_timeout))
                print 'Status code: %s' % (response.status_code)
                print 'JSON: %s' % (response.json())

		jobject = response.json()
		if 'status' in jobject:
		    if jobject['status'] != 'success':
			print 'status failure: %s. Returning...' % jobject['status']
		        hotel.is_google_update_running = False
        	        hotel.google_last_update_status = 'status failure'
        	        hotel.google_last_update_date = datetime.now()
        	        hotel.save()
			return

		else:
		    print 'Invalid json. Returning...'
		    hotel.is_google_update_running = False
        	    hotel.google_last_update_status = 'Invalid json'
        	    hotel.google_last_update_date = datetime.now()
        	    hotel.save()
		    return
		try:
		    reviews = jobject['data']['reviews']
		    for review in reviews:
			reviewid = rating = title = comment = review_date = ''
                        reviewer_name = ''
                        manager_response_text = manager_response_date = ''
                        has_manager_response = False
			try:
			    reviewid = review['reviewId']
			    if len(reviewid) == 0:
                                print 'URGENT - ID not found. skipping'
                                continue
                            print 'REVIEWID: %s' % reviewid
			except Exception, e:
			    print 'URGENT - Error in getting reviewid (Skipping...): %s' % (str(e))
			    continue
			try:
			    review_date_str = review['updateTime']
			    #review_date = datetime.strptime(review_date_str, '%Y-%m-%dT%H:%M:%SZ')
			    review_date = dateutil.parser.parse(review_date_str)
			    print 'review_date: %s' % (review_date)
			except Exception, e:
			    print 'URGENT - Error in getting review date: %s' % (str(e))
			    continue
			try:
			    rating = review['starRating']
			    print 'rating: %s' % (rating)
			except Exception, e:
			    print 'Error in getting rating: %s' % (str(e))
			try:
			    if 'comment' in review:
			        comment = review['comment']
			    else:
				print 'No comment..only rating'
			    print 'comment: %s' % (comment)
			except Exception, e:
			    print 'Error in getting comment: %s' % (str(e))
			try:
			    if 'displayName' in review['reviewer']:
			        reviewer_name = review['reviewer']['displayName']
			    else:
				print 'reviewer_name not available. setting it to google-anonymous'
				reviewer_name = 'google-anonymous'
			    print 'reviewer_name: %s' % (reviewer_name)
			except Exception, e:
			    print 'Error in getting reviewer_name: %s' % (str(e))
			try:
			    manager_response_text = review['reviewReply']['comment']
			    print 'manager_response_text: %s' % (manager_response_text)
			    if len(manager_response_text) > 0:
				has_manager_response = True
			except Exception, e:
			    print 'Error in getting manager_response_text: %s' % (str(e))
			try:
			    manager_response_date_str = review['reviewReply']['updateTime']
			    #manager_response_date = datetime.strptime(manager_response_date_str, '%Y-%m-%dT%H:%M:%SZ')
			    #manager_response_date = datetime.strptime(manager_response_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
			    manager_response_date = dateutil.parser.parse(manager_response_date_str)
			    print 'manager_response_date: %s' % (manager_response_date)
			except Exception, e:
			    print 'Error in getting manager_response_date: %s' % (str(e))
			print 'has_manager_response: %s' % (has_manager_response)


                        # UPDATE MONGODB
                        try:
			    upserted_review_id = None
                            mongo_review = MongoReview()
                            find_param = {}
                            find_param['identifier'] = reviewid
                            find_param['hotel_id'] = hotel.hotel_id
                            find_param['source'] = 5 #Google
                            find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
                            update_param = OrderedDict()
                            find_count = mongo_review.count(find_param)
                            if find_count == 0:
                                print 'create new google MongoReview'
                                update_param['_id'] = uuid.uuid4().hex[:16].lower()
                            else:
                                print 'existing google MongoReview found'
                            update_param['comment'] = comment
                            update_param['rating'] = rating
        		    rating_number = convert_rating_to_number_google(rating)
        		    update_param['rating_number'] = rating_number
        		    update_param['rating_out_of_5'] = rating_number
                            author = {}
                            author['name'] = reviewer_name
                            update_param['author'] = author
                            if isinstance(review_date, datetime):
                                update_param['review_date'] = review_date
                            else:
                                print 'google No review_date'
                                alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('google', hotel.hotel_id, reviewid, title, reviewer_name)
                                mongo_log_alert(type='scrape', info=alert_msg)
                            update_param['has_manager_response'] = has_manager_response
                            if isinstance(manager_response_date, datetime):
                                update_param['manager_response_date'] = manager_response_date
                            update_param['manager_response'] = manager_response_text
                            if find_count == 0:
                                update_param['date_created'] = datetime.now()
                            else:
                                update_param['date_updated'] = datetime.now()
                            print 'Try saving google MongoReview'
                            mongo_review.set_find_param(find_param)
                            print 'try setting update_param'
                            mongo_review.set_update_param(update_param)
                            mongo_result = mongo_review.update()
                            if mongo_result:
				upserted_review_id = mongo_result.upserted_id
                                print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
                                print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
                                print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
                            print 'google MongoReview updated'
                        except Exception, e:
                            print 'Error in updating google MongoReview - %s' % (str(e))

			# UPDATE POSTGRES
			try:
                            print 'Check in DB for the review'
                            reviews = Review.objects.filter(identifier=reviewid, hotel=hotel, is_unavailable=False).order_by('-date_created')
                            print 'reviews len: %s' % len(reviews)
                            if len(reviews) == 0:
                                print 'CREATING new reviewer and review'
                                reviewer = Reviewer.objects.create(source=sourceid)
                                if len(reviewer_name) > 0:
                                    reviewer.name = reviewer_name
                                    try:
                                        print 'Try saving reviewer'
                                        reviewer.save()
                                        review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
                                        review.comment = comment
                                        review.rating = rating
                                        try:
                                            review.review_date = review_date
                                        except Exception, e:
                                            print 'URGENT Error in review_date assignment, skipping review - %s' % (str(e))
                                            print 'deleteing reviewer'
                                            reviewer.delete()
                                            print 'reviewer deleted'
                                            continue
                                        review.has_manager_response = has_manager_response
                                        review.response_posted_checkbox = False
                                        review.is_non_english = False
                                        review.is_partial = False
					if has_manager_response is True:
                                            review.manager_response = manager_response_text
					    try:
                                                if isinstance(manager_response_date, datetime):
                                                    review.manager_response_date = manager_response_date
                                                else:
                                                    print 'URGENT: ERROR manager_response_date missing'
                                            except Exception, e:
                                                print 'Error in manager_response_date assignment - %s' % (str(e))
                                        try:
                                            print 'Try saving review'
                                            review.save()

					    #Update review_id in mongodb
                                            if upserted_review_id:
                                                try:
                                                    print 'Update review_id %s' % (review.review_id)
                                                    mongo_review = MongoReview()
                                                    find_param = {}
                                                    find_param['_id'] = upserted_review_id
                                                    update_param = {}
                                                    update_param['review_id'] = review.review_id
                                                    print 'Try saving review_id google MongoReview'
                                                    mongo_review.set_find_param(find_param)
                                                    print 'try setting review_id update_param'
                                                    mongo_review.set_update_param(update_param)
                                                    mongo_result = mongo_review.update()
                                                    if mongo_result:
                                                        print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                                        print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                                        print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                                        print 'google MongoReview review_id updated'
                                                except Exception, e:
                                                    print 'Error in updating review_id in mongodb: %s' % (str(e))
                                            else:
                                                print 'upserted_review_id is None'

                                        except Exception, e:
                                            print 'Error in executing save of review - new record - %s' % (str(e))
                                            print 'deleteing reviewer'
                                            reviewer.delete()
                                            print 'reviewer deleted'
                                            continue
                                    except Exception, e:
                                        print 'Error in executing save of reviewer - %s' % (str(e))
				else:
				    print 'reviewer_name is empty'
                            else:
                                print 'UPDATING...Existing reviewer and review found'
                                review = reviews[0]
                                if len(reviews) > 1:
                                    print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
                                review.comment = comment
                                review.rating = rating
                                try:
                                    review.review_date = review_date
                                except Exception, e:
                                    print 'Error in review_date assignment, skipping updating record - %s' % (str(e))
                                    continue
                                review.has_manager_response = has_manager_response
				if has_manager_response is True:
                                    review.manager_response = manager_response_text
				    try:
                                        if isinstance(manager_response_date, datetime):
                                            review.manager_response_date = manager_response_date
                                        else:
                                            print 'URGENT: ERROR manager_response_date missing'
                                    except Exception, e:
                                        print 'Error in manager_response_date assignment - %s' % (str(e))
                                try:
                                    print 'Try saving review'
                                    review.save()
                                except Exception, e:
                                    print 'Error in executing save of review - existing record - %s' % (str(e))
                                    continue
                        except Exception, e:
                            print 'Error in checking in DB for the review - %s' % (str(e))
                            continue
		    #End of for
		    print 'All well. Returning...'
		    hotel.is_google_update_running = False
        	    hotel.google_last_update_status = ''
        	    hotel.google_last_update_date = datetime.now()
        	    hotel.save()
		    return
		except Exception, e:
		    print 'Error in processing reviews: %s' % (str(e))
                    hotel.is_google_update_running = False
                    hotel.google_last_update_status = 'Error in processing reviews'
	    except Exception, e:
		print 'Error in gmb get: %s' % (str(e))
                hotel.is_google_update_running = False
                hotel.google_last_update_status = 'Error in gmb get'
	except Exception, e:
	    print 'Error in processing hotel: %s' % (str(e))
            hotel.is_google_update_running = False
            hotel.google_last_update_status = 'Error in processing hotel'
        hotel.google_last_update_date = datetime.now()
        hotel.save()
    except Exception, e:
	print 'Error in helper_scrape_google_by_hotel_id: %s' % (str(e))
        hotel.is_google_update_running = False
        hotel.google_last_update_status = 'Error in helper_scrape_google_by_hotel_id'
        hotel.google_last_update_date = datetime.now()
        hotel.save()
        return


def helper_scrape_hotelscom_by_hotel_id(uid, inputurl=None, follownext=False, firstrun=False, ischained=False, overall=False):
    print 'helper_scrape_hotelscom_by_hotel_id: uid(%s) - url(%s) - follownext(%s) - firstrun(%s) - ischained(%s) - overall(%s)' % (uid, inputurl, follownext, firstrun, ischained, overall)
    source = 'hotelscom'
    sourceid = 6
    try:
        statuscode = 0
        hotel = Hotel.objects.get(hotel_id=uid)
        print 'hotels.com-- %s' % hotel
	#if hotel.is_hotelscom_update_running == True:
	#    print 'Hotels.com Update is already running. Quitting...'
	#    return
	#hotel.is_hotelscom_update_running = True
	#hotel.save()
        try:
	    if inputurl is None:
		inputurl = hotel.hotelscom_url
		#inputurl = 'https://hotels.com/hotel/details.html?display=reviews&reviewOrder=date_newest_first&hotelId=196360&tripTypeFilter=all'
	    print 'hotels.com-- inputurl: %s' % inputurl
	    if len(inputurl) == 0:
		print 'Invalid input url. Returning...'
		hotel.is_hotelscom_update_running = False
		hotel.hotelscom_last_update_status = 'url is empty.'
		hotel.hotelscom_last_update_date = datetime.now()
                hotel.save()
                return
	    try:
		# m(1) - requests / m(2) - urllib2
		args = { 'u' :inputurl, 'a': settings.DATA_SERVER_AUTH, 'm':2 }
		data_server_url = 'http://{0}/q/'.format(DATA_SERVER_1)
		print 'data_server_url: %s' % (data_server_url)
		connect_timeout, read_timeout = 5.0, 20.0
		response = requests.post(data_server_url, data=args, timeout=(connect_timeout, read_timeout))
		page = response.content

                soup = BeautifulSoup(page, "html5lib")
                print 'hotels.com-- title: %s' % soup.find('div', attrs={'class':'property-description'}).find('h1', attrs={'itemprop':'name'}).find('a').text.lstrip().rstrip()
                nexturl = ''
                if overall == True:
                    read_overall_hotelscom(hotel, soup)
                    overall = False
                try:
                    #inreviews = soup.find('div', attrs={'class':'reviews-list'}).findAll('div', attrs={'class':'review-card'})
                    inreviews = soup.findAll('div', attrs={'class':'review-card'})
		    if len(inreviews) == 0:
			print 'No reviews found. Not a valid page. Returning...'
			hotel.hotelscom_last_update_status = 'Invalid url.'
			hotel.is_hotelscom_update_running = False
			hotel.hotelscom_last_update_date = datetime.now()
        		hotel.save()
			return
		    print 'hotels.com-- inreviews len: %s' % (len(inreviews))
		    #for inreview in inreviews[0:1]:
		    for inreview in inreviews:
			response_data = {}
			reviewid = rating = rating_list_text = title = review_text = review_pos = review_neg = review_location = review_date = review_date_format = review_dt = ''
			reviewer_name = reviewer_location = reviewer_recommendation = ''
			manager_response_header = manager_response_text = manager_response_date = manager_response_date_format = manager_response_dt = ''
			has_manager_response = False
			try:
			    rating = inreview.get('data-review-rating')
			    print 'rating: %s' % rating
			except Exception, e:
			    print 'Error in getting rating - %s' %(str(e))
			try:
                            tstr = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-tt'}).text.lstrip().rstrip()
                            to_remove_tstr = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-tt'}).find('span', attrs={'class':'date'}).text.lstrip().rstrip()
                            print tstr
                            rating_list_text = tstr.split(to_remove_tstr)[0].lstrip().rstrip()
                            print 'rating_list_text: %s' % rating_list_text
                        except Exception, e:
                            print 'Error in getting rating_list_text - %s' %(str(e))
			try:
			    tstr = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-reviewer'}).text.lstrip().rstrip()
			    to_remove_tstr = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-reviewer'}).find('div',attrs={'class':'reviewer-data'}).text.lstrip().rstrip()
			    print tstr
			    reviewer_name = tstr.split(to_remove_tstr)[0].lstrip().rstrip()
			    reviewer_location = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-reviewer'}).find('span',attrs={'class':'locality'}).text.lstrip().rstrip()
			    reviewer_location = reviewer_location.upper()
			    print 'reviewer_name: %s' % reviewer_name
			    print 'reviewer_location: %s' % reviewer_location
			except Exception, e:
			    print 'Error in getting reviewer info - %s' %(str(e))
			try:
			    title = inreview.find('div', attrs={'class':'review-card-header'}).find('div', attrs={'class':'review-summary'}).text.lstrip().rstrip()
			    print 'title: %s' % title
			except Exception, e:
			    print 'Error in getting title - %s' %(str(e))
			try:
                            review_pos = inreview.find('div', attrs={'class':'review-content'}).find('blockquote').text.lstrip().rstrip()
                            print 'review_pos: %s' % review_pos
                        except Exception, e:
                            print 'Error in getting review_pos - %s' %(str(e))
			try:
			    tstr = inreview.find('div', attrs={'class':'review-card-meta'}).find('div', attrs={'class':'review-card-meta-tt'}).find('span', attrs={'class':'date'}).text.lstrip().rstrip()
			    print tstr
			    if tstr.find(',') > 0: #Mar 27, 2017
                    		review_date_format = "fm2" # Aug 15, 2015
                    		tarr = tstr.split(' ') #Remove Posted
                    		if len(tarr) == 3:
                        	    review_date = tstr
			    print 'review_date: %s' % review_date
			    print 'review_date_format: %s' % review_date_format
			    if review_date_format == "fm2": #Aug 18, 2015
                                try:
                                    tlist =  review_date.split(" ")
                                    if len(tlist) == 3:
                                        tstr = tlist[2] + "-" + tlist[0] + "-" + tlist[1].rstrip(',')
                                        print tstr
                                        review_dt = datetime.strptime(tstr, '%Y-%b-%d')
                                        print review_dt
                                except Exception, e:
                                    print 'Error in review date coversion fm2 - %s' %(str(e))
			    print 'review_dt: %s' % review_dt
			    try:
                                if firstrun == False: #update
                                    #dt_threshold = datetime.now() - timedelta(days=30)
                                    if hotel.hotelscom_update_window is None:
                                        dt_threshold = datetime.now() - timedelta(days=30)
                                    else:
                                        dt_threshold = datetime.now() - timedelta(days=int(hotel.hotelscom_update_window))
				    print 'spl dt_threshold: %s' % dt_threshold
                                    if review_dt >= dt_threshold:
                                        print 'REVIEW FOUND in update window'
                                    else:
                                        print 'BEYOND UPDATE WINDOW. RETURNING...'
                                        hotel.is_hotelscom_update_running = False
					hotel.hotelscom_last_update_status = ''
					hotel.hotelscom_last_update_date = datetime.now()
                                        hotel.save()
                                        return
                            except Exception, e:
                                print 'URGENT Error in check dt_threshold for update. Returning...- %s' %(str(e))
                                hotel.is_hotelscom_update_running = False
				hotel.hotelscom_last_update_status = 'Error in check dt_threshold for update.'
				hotel.hotelscom_last_update_date = datetime.now()
                                hotel.save()
                                return
			except Exception, e:
			    print 'Error in getting review date - %s' %(str(e))
			try:
                            manager_response_header = inreview.find('div', attrs={'class':'review-card-response-bubble'}).find('cite').text.lstrip().rstrip()
                            print 'manager_response_header: %s' % manager_response_header
                        except Exception, e:
                            print 'Error in getting manager_response_header - %s' %(str(e))
			try:
                            manager_response_text = inreview.find('div', attrs={'class':'review-card-response-bubble'}).find('blockquote').text.lstrip().rstrip()
			    has_manager_response  = True
                            print 'manager_response_text: %s' % manager_response_text
                        except Exception, e:
                            print 'Error in getting manager_response_text - %s' %(str(e))
			response_data['rating'] = rating
			response_data['rating_list_text'] = rating_list_text
			response_data['title'] = title
			response_data['review_pos'] = review_pos
			response_data['review_date'] = review_date
			response_data['review_date_format'] = review_date_format
			response_data['reviewer_name'] = reviewer_name
			response_data['reviewer_location'] = reviewer_location
			response_data['has_manager_response'] = has_manager_response
			response_data['manager_response_text'] = manager_response_text
			response_data['manager_response_header'] = manager_response_header

			try:
			    reviewid = '{0}#{1}'.format(hotel.hotel_id, inreview.get('data-review-date'))
			    print 'hotels.com-- reviewid: %s' % reviewid
			except Exception, e:
			    print 'Error in making reviewid. Skipping... - %s' % (str(e))
			    continue

			print 'response_data: %s' % (response_data)

                        # UPDATE MONGODB
                        try:
			    upserted_review_id = None
                            mongo_review = MongoReview()
                            find_param = {}
                            find_param['identifier'] = reviewid
                            find_param['hotel_id'] = hotel.hotel_id
                            find_param['source'] = 6 #Hotels.com
                            find_param['$or'] = [ {'is_unavailable':False}, {'is_unavailable':{'$exists':False}} ]
                            update_param = OrderedDict()
                            find_count = mongo_review.count(find_param)
                            if find_count == 0:
                                print 'create new hotelscom MongoReview'
                                update_param['_id'] = uuid.uuid4().hex[:16].lower()
                            else:
                                print 'existing hotelscom MongoReview found'
                            update_param['title'] = title
                            update_param['comment'] = review_pos
                            update_param['rating'] = rating
        		    rating_number = convert_rating_to_number_hotelscom(rating)
        		    update_param['rating_number'] = rating_number
        		    update_param['rating_out_of_5'] = rating_number
                            update_param['rating_list_text'] = rating_list_text
                            author = {}
                            author['name'] = reviewer_name
                            author['location'] = reviewer_location
                            update_param['author'] = author
                            if isinstance(review_dt, datetime):
                                update_param['review_date'] = review_dt
                            else:
                                print 'hotelscom No review_date'
                                alert_msg = 'review date not found for {} - hotel({}) - identifier({}) - title({}) - author({})'.format('hotelscom', hotel.hotel_id, reviewid, title, reviewer_name)
                                mongo_log_alert(type='scrape', info=alert_msg)
                            update_param['has_manager_response'] = has_manager_response
                            #if isinstance(manager_response_dt, datetime):
                            #    update_param['manager_response_date'] = manager_response_dt
                            update_param['manager_response'] = manager_response_text
                            if find_count == 0:
                                update_param['date_created'] = datetime.now()
                            else:
                                update_param['date_updated'] = datetime.now()
                            print 'Try saving hotelscom MongoReview'
                            mongo_review.set_find_param(find_param)
                            print 'try setting update_param'
                            mongo_review.set_update_param(update_param)
                            mongo_result = mongo_review.update()
                            if mongo_result:
				upserted_review_id = mongo_result.upserted_id
                                print 'mongo_result upserted_id: %s' % (mongo_result.upserted_id)
                                print 'mongo_result matched_count: %s' % (mongo_result.matched_count)
                                print 'mongo_result modified_count: %s' % (mongo_result.modified_count)
                            print 'hotelscom MongoReview updated'
                        except Exception, e:
                            print 'Error in updating hotelscom MongoReview - %s' % (str(e))

			# UPDATE POSTGRES
			try:
			    create = False
			    update = False
			    print 'hotels.com-- Check in DB for the review'
			    print 'reviewid: %s' % reviewid
			    reviews = Review.objects.filter(identifier=reviewid, source=6, hotel=hotel, is_unavailable=False).order_by('-date_created')
			    print 'reviews len: %s' % len(reviews)
			    if len(reviews) == 0:
				create = True
			    else:
				print ' exisiting review found.'
			    	print 'reviews len: %s' % len(reviews)
				if len(reviews) > 1:
                                    print 'URGENT - DUPLICATE FOUND FOR %s' % reviewid
				review = reviews[0]
				update = True
				print 'update set to True'
			    if create == True:
                                print 'CREATING new reviewer and review'
                                reviewer = Reviewer.objects.create(source=sourceid)
				if len(reviewer_name) > 0:
				    reviewer.name = reviewer_name
				    reviewer.location = reviewer_location
				    try:
				  	reviewer.save()
					print 'Reviewer saved successfully'
					review = Review.objects.create(identifier=reviewid, hotel=hotel, author=reviewer, source=sourceid)
					review.title = title
					review.comment = review_pos
					review.rating = rating
					review.rating_list_text = rating_list_text
					try:
					    if isinstance(review_dt, datetime):
					        review.review_date = review_dt
					    else:
						print 'ERROR review_dt missing'
					except Exception, e:
					    print 'Error in review_dt assignment - %s' % (str(e))
					review.has_manager_response = has_manager_response
					review.response_posted_checkbox = False
					review.is_non_english = False
					review.partial = False
					#try:
					#    if isinstance(manager_response_dt, datetime):
					#        review.manager_response_date = manager_response_dt
					#    else:
					#	print 'manager_response_dt missing'
					#except Exception, e:
					#    print 'Error in manager_response_dt assignment - %s' % (str(e))
					review.manager_response = manager_response_text
					try:
					    review.save()
					    print 'review saved'

					    #Update review_id in mongodb
                                            if upserted_review_id:
                                                try:
                                                    print 'Update review_id %s' % (review.review_id)
                                                    mongo_review = MongoReview()
                                                    find_param = {}
                                                    find_param['_id'] = upserted_review_id
                                                    update_param = {}
                                                    update_param['review_id'] = review.review_id
                                                    print 'Try saving review_id hotelscom MongoReview'
                                                    mongo_review.set_find_param(find_param)
                                                    print 'try setting review_id update_param'
                                                    mongo_review.set_update_param(update_param)
                                                    mongo_result = mongo_review.update()
                                                    if mongo_result:
                                                        print 'mongo_result review_id upserted_id: %s' % (mongo_result.upserted_id)
                                                        print 'mongo_result review_id matched_count: %s' % (mongo_result.matched_count)
                                                        print 'mongo_result review_id modified_count: %s' % (mongo_result.modified_count)
                                                        print 'hotelscom MongoReview review_id updated'
                                                except Exception, e:
                                                    print 'Error in updating review_id in mongodb: %s' % (str(e))
                                            else:
                                                print 'upserted_review_id is None'

					except Exception, e:
					    print 'Error in executing save of review - new record. Skipping..  - %s' % (str(e))
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					    continue
				    except Exception, e:
					print 'Erorr in saving reviewer and review. Skipping - %s' % (str(e))
					try:
					    print 'deleteing reviewer'
					    reviewer.delete()
					    print 'reviewer deleted'
					except Exception, e:
					    print 'Errro in deleting reviewer, may be it doesnt exists - %s' % (str(e))
					continue
			    else:
				if update == True:
				    print 'UPDATING existing one....'
				    review.title = title
				    review.comment = review_pos
				    review.rating = rating
				    review.rating_list_text = rating_list_text
				    try:
					if isinstance(review_dt, datetime):
					    review.review_date = review_dt
					else:
					    print 'ERROR review_dt missing'
				    except Exception, e:
					print 'Error in review_dt assignment - %s' % (str(e))
				    review.has_manager_response = has_manager_response
				    #try:
				#	if isinstance(manager_response_dt, datetime):
				#	    review.manager_response_date = manager_response_dt
				#	else:
				#	    print 'manager_response_dt missing'
				#    except Exception, e:
				#	print 'Error in manager_response_dt assignment - %s' % (str(e))
				    review.manager_response = manager_response_text
				    try:
					review.save()
					print 'review updated'
				    except Exception, e:
					print 'Error in executing save of review - existing record. Skipping.. - %s' % (str(e))
					continue

			except Exception, e:
			    print 'Error in checking in DB for the review. Skipping... - %s' % (str(e))
			    continue

		    #End of for


		except Exception, e:
		    print 'Error in processing reviews - %s' % (str(e))
		try:
		    print 'hotels.com-- Check for next url'
		    li_list = soup.find('div',attrs={'class':'review-pagination'}).findAll('li')
		    print 'li_list: %s' % (li_list)
		    for li in li_list:
			#print 'li: %s' % (li)
			if li.text.find('Next') >= 0:
			    if li.find('a') and li.find('a').get('href'):
				nexturl = '{0}{1}'.format('https://hotels.com',li.find('a').get('href'))
		    nexturl = nexturl.lstrip().rstrip()
		    print 'hotels.com-- nexturl: %s' % nexturl
		except Exception, e:
		    print 'Error in getting nexturl - %s' % (str(e))

		if firstrun == False and follownext == False:
		    hotel.is_hotelscom_update_running = False
		    hotel.hotelscom_last_update_status = ''
		    hotel.hotelscom_last_update_date = datetime.now()
        	    hotel.save()
		    return
		if len(nexturl) > 0:
		    print 'hotels.com-- Queue the next page'
		    try:
			timedelay = random.randrange(5,10)
                        api_root = 'http://localhost:5555/api'
                        task_api = '{}/task'.format(api_root)
                        args = {'args': [timedelay, uid, nexturl, follownext, firstrun, ischained, overall]}
                        url = '{}/async-apply/scrape.tasks.task_wrapper_hotelscom_by_hotel_id'.format(task_api)
                        print url
                        resp = requests.post(url, data=json.dumps(args), auth=HTTPBasicAuth(settings.CELERY_AUTH_USERNAME, settings.CELERY_AUTH_PASSWORD))
                        print 'hotels.com-- task post status code: %s' % (resp.status_code)
        		hotel.is_hotelscom_update_running = True
                    except Exception, e:
                        print 'Error in making celery web request - %s' % (str(e))
       			hotel.is_hotelscom_update_running = False
        		hotel.hotelscom_last_update_status = 'Error in making celery web request'
        		hotel.hotelscom_last_update_date = datetime.now()
        		hotel.save()
			return
		else:
        	    hotel.is_hotelscom_update_running = False

                hotel.hotelscom_last_update_status = ''
	    except Exception, e:
		print 'Error in making soup - %s' % (str(e))
        	hotel.is_hotelscom_update_running = False
                hotel.hotelscom_last_update_status = 'error in soup'
	except Exception, e:
	    print 'Error in processing hotel - %s' % (str(e))
       	    hotel.is_hotelscom_update_running = False
            hotel.hotelscom_last_update_status = 'error in processing'
        hotel.hotelscom_last_update_date = datetime.now()
        hotel.save()
	return
    except Exception, e:
	print 'Error in helper_scrape_hotelscom_by_hotel_id - %s' % (str(e))
       	hotel.is_hotelscom_update_running = False
        hotel.hotelscom_last_update_status = 'error in helper_scrape_hotelscom_by_hotel_id'
        hotel.hotelscom_last_update_date = datetime.now()
        hotel.save()
	return



