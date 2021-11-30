from __future__ import unicode_literals

from django.db import models

from datetime import datetime

# Create your models here.

class Hotel(models.Model):
    hotel_id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    gt_location_id = models.CharField(max_length=256, null=True, blank=True, default=None)
    tripadvisor_url = models.CharField(max_length=256, null=True, blank=True)
    booking_url = models.CharField(max_length=256, null=True, blank=True)
    expedia_url = models.CharField(max_length=256, null=True, blank=True)
    hotelscom_url = models.CharField(max_length=256, null=True, blank=True)
    is_gmb_enabled = models.BooleanField(default=False)
    tripadvisor_hotel_id = models.CharField(max_length=64, null=True, blank=True, default=None)
    booking_hotel_id = models.CharField(max_length=64, null=True, blank=True, default=None)
    expedia_hotel_id = models.CharField(max_length=64, null=True, blank=True, default=None)
    hotelscom_hotel_id = models.CharField(max_length=64, null=True, blank=True, default=None)
    tripadvisor_update_window = models.CharField(max_length=256, null=True, blank=True, default='30', help_text='In days')
    booking_update_window = models.CharField(max_length=256, null=True, blank=True, default='30', help_text='In days')
    expedia_update_window = models.CharField(max_length=256, null=True, blank=True, default='30', help_text='In days')
    hotelscom_update_window = models.CharField(max_length=256, null=True, blank=True, default='30', help_text='In days')
    is_tripadvisor_update_running  = models.BooleanField(default=False)
    tripadvisor_last_update_status = models.CharField(max_length=256, null=True, blank=True)
    tripadvisor_last_update_date = models.DateTimeField(null=True, blank=True)
    is_tripadvisor_task_running_for_reviewlist  = models.BooleanField(default=False)
    tripadvisor_reviews_beyond_threshold = models.IntegerField(null=True, blank=True, default=0, help_text='Current number of TripAdvisor reviews which are beyond update window threshold.')
    is_booking_update_running  = models.BooleanField(default=False)
    booking_last_update_status = models.CharField(max_length=256, null=True, blank=True)
    booking_last_update_date = models.DateTimeField(null=True, blank=True)
    is_expedia_update_running  = models.BooleanField(default=False)
    expedia_last_update_status = models.CharField(max_length=256, null=True, blank=True)
    expedia_last_update_date = models.DateTimeField(null=True, blank=True)
    is_google_update_running  = models.BooleanField(default=False)
    google_last_update_status = models.CharField(max_length=256, null=True, blank=True)
    google_last_update_date = models.DateTimeField(null=True, blank=True)
    is_hotelscom_update_running  = models.BooleanField(default=False)
    hotelscom_last_update_status = models.CharField(max_length=256, null=True, blank=True)
    hotelscom_last_update_date = models.DateTimeField(null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- (T)%s -- (B)%s -- (E)%s -- (H)%s -- %s/%s/%s/%s' % (self.hotel_id, self.identifier, self.name, self.is_tripadvisor_update_running, self.is_booking_update_running, self.is_expedia_update_running, self.is_hotelscom_update_running, self.tripadvisor_update_window, self.booking_update_window, self.expedia_update_window, self.hotelscom_update_window)


class Reviewer(models.Model):
    reviewer_id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    location = models.CharField(max_length=256, null=True, blank=True)
    source = models.IntegerField(choices=((1,'NOT AVAILABLE'),(2,'TRIPADVISOR'),(3, 'BOOKING.COM'),(4,'EXPEDIA'),(5,'GOOGLE'),(6,'HOTELS.COM')), default=1, null=True, blank=True)
    contributor_level = models.CharField(max_length=8, null=True, blank=True, help_text='For TripAdvisor')
    total_reviews = models.IntegerField(null=True, blank=True, help_text='For TripAdvisor. Booking. Total count of reviews including hotel, restaurants, etc')
    hotel_reviews = models.IntegerField(null=True, blank=True, help_text='For TripAdvisor. Total count of only hotel reviews')
    helpful_votes = models.IntegerField(null=True, blank=True, help_text='For TripAdvisor. Number of people voted this as helpful')
    remarks = models.CharField(max_length=256, null=True, blank=True, help_text='For Booking.com, age group is stored here.')
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.reviewer_id, self.name, self.location, self.date_created.strftime('%d-%b-%Y %H:%M:%S'))

    def __unicode__(self):
        return u'Reviewer for: %s' % self.reviewer_id

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=256, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, null=False)
    source = models.IntegerField(choices=((1,'NOT AVAILABLE'),(2,'TRIPADVISOR'),(3, 'BOOKING.COM'),(4,'EXPEDIA'),(5,'GOOGLE'),(6,'HOTELS.COM')), default=1, null=True, blank=True)
    title = models.CharField(max_length=256, null=True, blank=True)
    comment = models.TextField(blank=True, null=True, default=None)
    comment_negative = models.TextField(blank=True, null=True, default=None, help_text='For Expedia, remarks such as Pros/Cons/Location/Etc are stored here.')
    comment_pro = models.TextField(blank=True, null=True, default=None, help_text='Only for Expedia.')
    comment_location = models.TextField(blank=True, null=True, default=None, help_text='Only for Expedia.')
    rating = models.CharField(max_length=64, null=True, blank=True)
    rating_list_title = models.CharField(max_length=256, null=True, blank=True, help_text='For Expedia, reviewer recommendation for everyone/business is stored here.')
    rating_list_text = models.CharField(max_length=256, null=True, blank=True, help_text='For Booking.com, review bullets are stored here.')
    room_tip = models.CharField(max_length=256, null=True, blank=True)
    author = models.ForeignKey(Reviewer, null=True)
    review_date = models.DateTimeField(null=True, blank=True)
    url = models.CharField(max_length=256, null=True, blank=True)
    has_manager_response  = models.BooleanField(default=False)
    suggested_response = models.TextField(blank=True, null=True, default=None)
    suggested_response_date = models.DateTimeField(null=True, blank=True)
    suggested_response_signature = models.TextField(blank=True, null=True, default=None)
    response_posted_checkbox  = models.BooleanField(default=False)
    level_1_username = models.CharField(max_length=64, null=True, blank=True, default=None)
    level_2_username = models.CharField(max_length=64, null=True, blank=True, default=None)
    manager_response = models.TextField(blank=True, null=True, default=None)
    manager_response_date = models.DateTimeField(null=True, blank=True)
    is_ready_to_be_posted  = models.BooleanField(default=False)
    approval_key = models.CharField(max_length=256, blank=True, null=True, default=None)
    is_sent_for_approval  = models.BooleanField(default=False)
    sent_for_approval_date = models.DateTimeField(null=True, blank=True)
    is_auto_approved = models.BooleanField(default=False)
    is_approved  = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    edited_response = models.TextField(blank=True, null=True, default=None)
    edited_response_date = models.DateTimeField(null=True, blank=True)
    more_info_key = models.CharField(max_length=256, blank=True, null=True, default=None)
    is_sent_for_more_info  = models.BooleanField(default=False)
    sent_for_more_info_date = models.DateTimeField(null=True, blank=True)
    more_info_received_date = models.DateTimeField(null=True, blank=True)
    more_info_msg = models.TextField(blank=True, null=True, default=None)
    more_info_response = models.TextField(blank=True, null=True, default=None)
    is_sentiment_processed  = models.BooleanField(default=False)
    is_non_english = models.BooleanField(default=False)
    removed_at_source = models.BooleanField(default=False)
    is_partial  = models.BooleanField(default=False)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
	return '%s(%s) -- %s -- %s -- %s -- %s -- %s' % (self.review_id, self.identifier, self.source, self.hotel.name, self.rating, self.has_manager_response, self.review_date)

    def __unicode__(self):
        return u'Review for: %s' % self.review_id

class TripadvisorOverallRating(models.Model):
    tor_id = models.AutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, null=False)
    total_reviews = models.CharField(max_length=64, null=True, blank=True)
    hotel_rank = models.CharField(max_length=256, null=True, blank=True)
    rating_overall = models.CharField(max_length=64, null=True, blank=True)
    rating_excellent = models.CharField(max_length=64, null=True, blank=True)
    rating_very_good = models.CharField(max_length=64, null=True, blank=True)
    rating_average = models.CharField(max_length=64, null=True, blank=True)
    rating_poor = models.CharField(max_length=64, null=True, blank=True)
    rating_terrible = models.CharField(max_length=64, null=True, blank=True)
    for_families = models.CharField(max_length=64, null=True, blank=True)
    for_couples = models.CharField(max_length=64, null=True, blank=True)
    for_solo = models.CharField(max_length=64, null=True, blank=True)
    for_business = models.CharField(max_length=64, null=True, blank=True)
    for_friends = models.CharField(max_length=64, null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- (%s)%s -- %s -- %s' % (self.tor_id, self.hotel.hotel_id, self.hotel.name, self.total_reviews, self.date_created.strftime('%d-%b-%Y %H:%M:%S'))

class BookingOverallRating(models.Model):
    bor_id = models.AutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, null=False)
    total_reviews_for_score = models.CharField(max_length=64, null=True, blank=True)
    hotel_stars = models.CharField(max_length=64, null=True, blank=True)
    hotel_rank = models.CharField(max_length=256, null=True, blank=True)
    rating_overall = models.CharField(max_length=64, null=True, blank=True)
    rating_cleanliness = models.CharField(max_length=64, null=True, blank=True)
    rating_comfort = models.CharField(max_length=64, null=True, blank=True)
    rating_location = models.CharField(max_length=64, null=True, blank=True)
    rating_facilities = models.CharField(max_length=64, null=True, blank=True)
    rating_staff = models.CharField(max_length=64, null=True, blank=True)
    rating_value_for_money = models.CharField(max_length=64, null=True, blank=True)
    rating_free_wifi = models.CharField(max_length=64, null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.bor_id, self.hotel.name, self.total_reviews_for_score, self.date_created.strftime('%d-%b-%Y %H:%M:%S'))

class ExpediaOverallRating(models.Model):
    eor_id = models.AutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, null=False)
    total_reviews_for_score = models.CharField(max_length=64, null=True, blank=True)
    hotel_stars = models.CharField(max_length=64, null=True, blank=True)
    rating_overall = models.CharField(max_length=64, null=True, blank=True)
    rating_cleanliness = models.CharField(max_length=64, null=True, blank=True)
    rating_comfort = models.CharField(max_length=64, null=True, blank=True)
    rating_staff = models.CharField(max_length=64, null=True, blank=True)
    rating_hotel_condition = models.CharField(max_length=64, null=True, blank=True)
    recommendation_percentage = models.CharField(max_length=64, null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.eor_id, self.hotel.name, self.total_reviews_for_score, self.date_created.strftime('%d-%b-%Y %H:%M:%S'))

class HotelsComOverallRating(models.Model):
    hcor_id = models.AutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, null=False)
    hotel_stars = models.CharField(max_length=16, null=True, blank=True)
    total_reviews = models.CharField(max_length=16, null=True, blank=True)
    reviews_with_5_star = models.CharField(max_length=16, null=True, blank=True)
    reviews_with_4_star = models.CharField(max_length=16, null=True, blank=True)
    reviews_with_3_star = models.CharField(max_length=16, null=True, blank=True)
    reviews_with_2_star = models.CharField(max_length=16, null=True, blank=True)
    reviews_with_1_star = models.CharField(max_length=16, null=True, blank=True)
    total_reviews_business = models.CharField(max_length=16, null=True, blank=True)
    total_reviews_romance = models.CharField(max_length=16, null=True, blank=True)
    total_reviews_family = models.CharField(max_length=16, null=True, blank=True)
    total_reviews_friends = models.CharField(max_length=16, null=True, blank=True)
    total_reviews_other = models.CharField(max_length=16, null=True, blank=True)
    rating_overall = models.CharField(max_length=16, null=True, blank=True)
    rating_location = models.CharField(max_length=16, null=True, blank=True)
    rating_location_text = models.CharField(max_length=32, null=True, blank=True)
    rating_cleanliness = models.CharField(max_length=16, null=True, blank=True)
    rating_cleanliness_text = models.CharField(max_length=32, null=True, blank=True)
    rating_service = models.CharField(max_length=16, null=True, blank=True)
    rating_service_text = models.CharField(max_length=32, null=True, blank=True)
    rating_room = models.CharField(max_length=16, null=True, blank=True)
    rating_room_text = models.CharField(max_length=32, null=True, blank=True)
    rating_comfort = models.CharField(max_length=16, null=True, blank=True)
    rating_comfort_text = models.CharField(max_length=32, null=True, blank=True)
    rating_vibe = models.CharField(max_length=16, null=True, blank=True)
    rating_vibe_text = models.CharField(max_length=32, null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.eor_id, self.hotel.name, self.total_reviews, self.date_created.strftime('%d-%b-%Y %H:%M:%S'))

class SntReviewAspect(models.Model):
    sra_id = models.AutoField(primary_key=True)
    r_id = models.IntegerField(null=False, blank=False)
    aspect = models.CharField(max_length=64, null=True, blank=True)
    polarity = models.CharField(max_length=32, null=True, blank=True)
    p_conf = models.FloatField(null=True, blank=True)
    a_conf = models.FloatField(null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.sra_id, self.r_id, self.aspect, self.last_modified.strftime('%d-%b-%Y %H:%M:%S'))

class SntReviewSentence(models.Model):
    srs_id = models.AutoField(primary_key=True)
    r_id = models.IntegerField(null=False, blank=False)
    text = models.TextField(null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s' % (self.srs_id, self.r_id, self.text[0:30], self.last_modified.strftime('%d-%b-%Y %H:%M:%S'))

class SntReviewSentenceAspect(models.Model):
    srsa_id = models.AutoField(primary_key=True)
    r_id = models.IntegerField(null=False, blank=False)
    srs_id = models.IntegerField(null=False, blank=False)
    aspect = models.CharField(max_length=64, null=True, blank=True)
    polarity = models.CharField(max_length=32, null=True, blank=True)
    p_conf = models.FloatField(null=True, blank=True)
    a_conf = models.FloatField(null=True, blank=True)
    is_unavailable  = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s -- %s' % (self.srsa_id, self.r_id, self.srs_id, self.aspect, self.last_modified.strftime('%d-%b-%Y %H:%M:%S'))

class ReviewStat(models.Model):
    rs_id = models.AutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, null=False)
    year = models.IntegerField(null=True, blank=True, default=None)
    month = models.IntegerField(null=True, blank=True, default=None)
    tripadvisor_reviews = models.IntegerField(null=True, blank=True, default=None)
    tripadvisor_reviews_responded = models.IntegerField(null=True, blank=True, default=None)
    booking_reviews = models.IntegerField(null=True, blank=True, default=None)
    booking_reviews_responded = models.IntegerField(null=True, blank=True, default=None)
    expedia_reviews = models.IntegerField(null=True, blank=True, default=None)
    expedia_reviews_responded = models.IntegerField(null=True, blank=True, default=None)
    google_reviews = models.IntegerField(null=True, blank=True, default=None)
    google_reviews_responded = models.IntegerField(null=True, blank=True, default=None)
    hotelscom_reviews = models.IntegerField(null=True, blank=True, default=None)
    hotelscom_reviews_responded = models.IntegerField(null=True, blank=True, default=None)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s -- %s -- %s -- %s -- T(%s/%s) --B(%s/%s) -- E(%s/%s) -- G(%s/%s) -- H(%s/%s)  -- %s' % (self.rs_id, self.hotel.name, self.year, self.month, self.tripadvisor_reviews, self.tripadvisor_reviews_responded, self.booking_reviews, self.booking_reviews_responded, self.expedia_reviews, self.expedia_reviews_responded, self.google_reviews, self.google_reviews_responded, self.hotelscom_reviews, self.hotelscom_reviews_responded, self.last_modified.strftime('%d-%b-%Y %H:%M:%S'))

