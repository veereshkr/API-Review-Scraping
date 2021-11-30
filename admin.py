from django.contrib import admin

from scrape.models import Hotel
from scrape.models import Reviewer
from scrape.models import Review
from scrape.models import TripadvisorOverallRating
from scrape.models import BookingOverallRating
from scrape.models import ExpediaOverallRating
from scrape.models import SntReviewAspect
from scrape.models import SntReviewSentence
from scrape.models import SntReviewSentenceAspect

class ReviewAdmin(admin.ModelAdmin):
    search_fields = ['review_id', 'identifier', 'title']
class SntReviewAspectAdmin(admin.ModelAdmin):
    search_fields = ['r_id']
class SntReviewSentenceAdmin(admin.ModelAdmin):
    search_fields = ['r_id']
class SntReviewSentenceAspectAdmin(admin.ModelAdmin):
    search_fields = ['r_id']


admin.site.register(Hotel)
admin.site.register(Reviewer)
admin.site.register(Review, ReviewAdmin)
admin.site.register(TripadvisorOverallRating)
admin.site.register(BookingOverallRating)
admin.site.register(ExpediaOverallRating)
admin.site.register(SntReviewAspect, SntReviewAspectAdmin)
admin.site.register(SntReviewSentence, SntReviewSentenceAdmin)
admin.site.register(SntReviewSentenceAspect, SntReviewSentenceAspectAdmin)


