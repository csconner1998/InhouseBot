from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import hello.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", hello.views.index, name="index"),
    path("leaderboard/", hello.views.leaderboard, name="leaderboard"),
    path("matchhistory/", hello.views.matchhistory, name="matchhistory"),
    path("admin/", admin.site.urls),
]
