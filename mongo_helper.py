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


reviewdb = ''

class MongoCollection:

    def __init__(self):
	self.find_param = {}
	self.update_param = {}
	self.unset_param = {}
	self.insert_param = {}
	self.data = OrderedDict()

    def add_param(self, var_name, var_value):
	self.data[var_name] = var_value

    def add_params(self, ordereddict):
	self.data = ordereddict

    def set_find_param(self, find_param):
	self.find_param = find_param

    def set_update_param(self, update_param):
	self.update_param = update_param

    def set_unset_param(self, unset_param):
	self.unset_param = unset_param

    def set_insert_param(self, insert_param):
	self.insert_param = insert_param

    def show(self):
	print '%s - %s' % (self.__class__.__name__, self.data)


class MongoAlert(MongoCollection):

    def insert(self):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        if '_id' not in self.insert_param:
            self.insert_param['_id'] = uuid.uuid4().hex[:16].lower()
        result = db.alert.insert_one(self.insert_param)
        print 'result inserted_id: %s' % (result.inserted_id)
        client.close()
        print 'inserted %s - %s' % (self.__class__.__name__, self.insert_param['_id'])


class MongoBookingOverallRating(MongoCollection):

    def save(self):
	client = MongoClient(reviewdb)
	db = client.reviewdb
	if '_id' not in self.data:
	    self.data['_id'] = uuid.uuid4().hex[:16].lower()
	result = db.overall_booking_rating.insert_one(self.data)
	print 'result inserted_id: %s' % (result.inserted_id)
	client.close()
	print 'saved %s - %s' % (self.__class__.__name__, self.data['_id'])

class MongoExpediaOverallRating(MongoCollection):

    def save(self):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        if '_id' not in self.data:
            self.data['_id'] = uuid.uuid4().hex[:16].lower()
        result = db.overall_expedia_rating.insert_one(self.data)
        print 'result inserted_id: %s' % (result.inserted_id)
        client.close()
        print 'saved %s - %s' % (self.__class__.__name__, self.data['_id'])


class MongoTripadvisorOverallRating(MongoCollection):

    def save(self):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        if '_id' not in self.data:
            self.data['_id'] = uuid.uuid4().hex[:16].lower()
        result = db.overall_tripadvisor_rating.insert_one(self.data)
        print 'result inserted_id: %s' % (result.inserted_id)
        client.close()
        print 'saved %s - %s' % (self.__class__.__name__, self.data['_id'])


class MongoHotelscomOverallRating(MongoCollection):

    def save(self):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        if '_id' not in self.data:
            self.data['_id'] = uuid.uuid4().hex[:16].lower()
        result = db.overall_hotelscom_rating.insert_one(self.data)
        print 'result inserted_id: %s' % (result.inserted_id)
        client.close()
        print 'saved %s - %s' % (self.__class__.__name__, self.data['_id'])


class MongoReview(MongoCollection):

    def find_one(self, find_param):
        client = MongoClient(reviewdb)
        db = client.reviewdb
	result = None
        results = db.review.find(find_param, limit=1, sort=[('date_created',-1)])
        print 'results: %s' % (results.count())
	if results.count() > 0:
	    result = results[0]
        client.close()
        return result

    def count(self, find_param):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        result = db.review.count(find_param)
        print 'result count: %s' % (result)
        client.close()
	return result


    def save1(self):
        client = MongoClient(reviewdb)
        db = client.reviewdb
        if '_id' not in self.data:
            self.data['_id'] = uuid.uuid4().hex[:16].lower()
        result = db.overall_hotelscom_rating.insert_one(self.data)
        print 'result inserted_id: %s' % (result.inserted_id)
        client.close()
        print 'saved %s - %s' % (self.__class__.__name__, self.data['_id'])


    def update(self):
	try:
            client = MongoClient(reviewdb)
            db = client.reviewdb
	    result = None
            if self.find_param and self.update_param:

                self.update_param['entry_source'] = 'scrape'
		if self.unset_param:
		    print 'use unset_param: %s' % (self.unset_param)
                    result = db.review.update_many(self.find_param, {'$set': self.update_param, '$unset': self.unset_param}, upsert=True)
		else:
                    result = db.review.update_many(self.find_param, {'$set': self.update_param}, upsert=True)
                print 'result : %s' % (result)
                print 'updated %s - %s' % (self.__class__.__name__, self.find_param)
            client.close()
	except Exception, e:
	    print 'Error in MongoReview update: %s' % (str(e))
	    client.close()
	    raise
	return result



def mongo_log_alert(type='scrape', info='error'):
    print 'mongo_log_alert: type(%s) - info(%s)' % (type, info)
    try:
        mongo_alert = MongoAlert()
        insert_param = OrderedDict()
        insert_param['_id'] = uuid.uuid4().hex[:16].lower()
        insert_param['type'] = type
        insert_param['info'] = info
        insert_param['date_created'] = datetime.now()
        print 'Try saving MongoAlert'
        mongo_alert.set_insert_param(insert_param)
        mongo_alert.insert()
        print 'MongoAlert updated'
    except Exception, e:
        print 'Error in updating MongoAlert - %s' % (str(e))


