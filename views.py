from django.template import RequestContext
from django.shortcuts import render, render_to_response
from django.shortcuts import get_list_or_404, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
import requests
from datetime import datetime, timedelta
import json
from array import *
import math
import hashlib
import time
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django import  forms

from django.contrib.auth.models import User
from scrape.models import *
from scrape.tasks import *


def index(request):
    return HttpResponse('--')


@login_required(login_url = '', redirect_field_name = 'next_url')
def api_run_update_scrape_retry(request):
    print 'api_run_update_scrape_retry'
    response_data = {}
    try:
        user = get_object_or_404(User, username=request.user.username)
        print user.first_name.encode("utf-8")
        if user.is_superuser == False:
            raise Http404("You Dont Belong Here")
        if user.is_superuser == True:
            try:
                index = str(request.POST['index'])
                print index
                type = str(request.POST['type'])
                print type
                print 'index: %s, type: %s' % (index, type)
                hotel = Hotel.objects.get(hotel_id=index)
                print hotel
		status = 'failure'
		msg = 'Data Missing'
		if type == 'tripadvisor':
		    if hotel.is_tripadvisor_update_running == False:

			hotel.is_tripadvisor_update_running = True
                        hotel.save()
			interval = 1
			task_tripadvisor_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
                        status = 'success'
                        msg = 'Queued the task'
                    else:
                        status = 'failure'
                        msg = 'Update is already running. New task has not been started.'
                if type == 'booking':
                    if hotel.is_booking_update_running == False:

			hotel.is_booking_update_running = True
                        hotel.save()
			interval = 1
                        task_booking_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)

                        status = 'success'
                        msg = 'Queued the task'
                    else:
                        status = 'failure'
                        msg = 'Update is already running. New task has not been started.'
                if type == 'expedia':
                    if hotel.is_expedia_update_running == False:
                        #task_scrape_expedia_by_hotel_id.apply_async(args=[index, None, True, False], countdown=1)

			hotel.is_expedia_update_running = True
                        hotel.save()
			interval = 1
                        task_expedia_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)

                        status = 'success'
                        msg = 'Queued the task'
                    else:
                        status = 'failure'
                        msg = 'Update is already running. New task has not been started.'
                response_data['status'] = status
                response_data['msg'] = msg
                return HttpResponse(json.dumps(response_data), content_type="application/json")
            except:
                response_data['status'] = 'failure'
                response_data['msg'] = 'Keyword Not Found'
                return HttpResponse(json.dumps(response_data), content_type="application/json")
    except:
        raise Http404("You Dont Belong Here")

@csrf_exempt
def api_task_by_hotel_id(request):
    print 'api_task_by_hotel_id'
    response_data = {}
    try:
	if request.POST:
	    key = request.POST['key']
	    print 'key: %s' % (key)
	    if key != settings.GT_SCRAPE_API_KEY:
		print 'wrong key'
		response_data['status'] = 'failure'
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	    source = request.POST['source']
	    print 'source: %s' % (source)
	    if source != 'tripadvisor' and source != 'booking' and source != 'expedia' and source != 'google' and source != 'hotelscom':
		response_data['status'] = 'failure'
		print 'wrong source (%s) value'% (source)
		return HttpResponse(json.dumps(response_data), content_type="application/json")
	    hotel_id = request.POST['id']
	    print 'hotel_id: %s' % (hotel_id)
	    first_run = request.POST['first_run']
	    print 'first_run: %s' % (first_run)
	    if first_run == 'true' or first_run == 'false':
		hotel = Hotel.objects.get(hotel_id=int(hotel_id))
		print 'hotel: %s' % (hotel)
		if source == 'tripadvisor':
		    if hotel.is_tripadvisor_update_running == False:
                        hotel.is_tripadvisor_update_running = True
                        hotel.save()
                        interval = 1
		        if first_run == 'true':
                            task_tripadvisor_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, True, False, True], countdown=interval)
		        if first_run == 'false':
                            task_tripadvisor_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
		if source == 'booking':
		    if hotel.is_booking_update_running == False:
                        hotel.is_booking_update_running = True
                        hotel.save()
                        interval = 1
		        if first_run == 'true':
                            task_booking_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, True, False, True], countdown=interval)
		        if first_run == 'false':
                            task_booking_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
		if source == 'expedia':
		    if hotel.is_expedia_update_running == False:
                        hotel.is_expedia_update_running = True
                        hotel.save()
                        interval = 1
		        if first_run == 'true':
                            task_expedia_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, True, False, True], countdown=interval)
		        if first_run == 'false':
                            task_expedia_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)
		if source == 'google':
                    if hotel.is_google_update_running == False:
                        hotel.is_google_update_running = True
                        hotel.save()
                        interval = 1
                        if first_run == 'true':
                            task_google_by_hotel_id.apply_async(args=[hotel.hotel_id], countdown=interval)
                        if first_run == 'false':
                            task_google_by_hotel_id.apply_async(args=[hotel.hotel_id], countdown=interval)
		if source == 'hotelscom':
                    if hotel.is_hotelscom_update_running == False:
                        hotel.is_hotelscom_update_running = True
                        hotel.save()
                        interval = 1
                        if first_run == 'true':
                            task_hotelscom_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, True, False, True], countdown=interval)
                        if first_run == 'false':
                            task_hotelscom_by_hotel_id.apply_async(args=[hotel.hotel_id, None, True, False, False, True], countdown=interval)

	        response_data['status'] = 'success'
	    else:
		print 'wrong first_run (%s) value'% (first_run)
	        response_data['status'] = 'failure'
	else:
	    response_data['status'] = 'failure'
    except Exception, e:
	print 'Error in api_task_tripadvisor_by_hotel_id: %s' % (str(e))
	response_data['status'] = 'failure'
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@csrf_exempt
def api_send_alert_email(request):
    print 'api_send_alert_email'
    response_data = {}
    try:
	if request.body:
	    injson = json.loads(request.body)
	    if 'm' in injson:
		email_msg = injson['m']
	    else:
	        email_msg = 'malformed request for send alert email'
	    print 'email_msg: %s' % (email_msg)
            subject = 'Response System Alert - {0}'.format(datetime.now())
            key = settings.MAILGUN_KEY
            sandbox = settings.MAILGUN_SANDBOX

            recipient = 'email_id'
            request_url = 'https://api.mailgun.net/v3/{0}/messages'.format(sandbox)
            print request_url
            from_email = 'email_id'
            print from_email
            print 'recipient: %s' % (recipient)
            try:
                request = requests.post(request_url, auth=('api', key), data={ 'from': from_email, 'to': recipient, 'subject': subject, 'html': email_msg})
                print 'Status: {0}'.format(request.status_code)
                print 'Body:   {0}'.format(request.text)
		response_data['status'] = 'success'
            except Exception, e:
                print 'Error in invoking mailgun post: %s' % (str(e))
		response_data['status'] = 'failure'
	else:
	    print 'No body'
	    response_data['status'] = 'failure'
    except Exception, e:
	print 'Error in api_send_alert_email: %s' % (str(e))
	response_data['status'] = 'failure'
    return HttpResponse(json.dumps(response_data), content_type="application/json")

