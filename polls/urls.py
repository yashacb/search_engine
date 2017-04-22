from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^index$' , views.index , name = 'index') ,
	url(r'^home$' , views.home , name = 'home') ,
	url(r'^recos$' , views.reco , name = 'recos') ,
	url(r'^hist$' , views.history , name = 'hist') ,
	url(r'^search$' , views.search , name = 'search') ,
	url(r'^video$' , views.video , name = 'video') ,
	url(r'^login$' , views.login_view , name = 'login') ,
	url(r'^logout$' , views.logout_view , name = 'login') ,
	url(r'^register$' , views.register , name = 'register')  ,
	url(r'^blacklist$' , views.blacklist , name = 'blacklist')  ,
	url(r'^addbl$' , views.add_blacklist , name = 'all_bl') ,
	url(r'^delbl$' , views.delete_blacklist , name = 'del_bl') 
]