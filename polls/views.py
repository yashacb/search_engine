# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render , redirect
from django.contrib.auth.models import User
from django.http import HttpResponse , Http404
from django.contrib.auth import authenticate , login , logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from pymongo import MongoClient
from .models import LinkMap , UserClick
from stemming.porter2 import stem

import re , datetime
import utilities

# Create your views here.
@login_required(login_url='/polls/index')
def home(request):
	return render(request , 'polls/home.html' , { 'name' : request.user.username })

@login_required(login_url='/polls/index')
def search(request):	
	if request.GET.get('q' , '') != '':
		if int(request.GET.get('page' , '-1')) < 0 or int(request.GET.get('page' , '-1')) > 3:
			return redirect('/polls/search?q=' + request.GET.get('q' , '') + '&page=0')
		results = []
		if request.GET.get('q' , '') != request.session.get('c_query' , ''):
			#results from mongodb
			client = MongoClient()
			db = client['videos']
			pipeline = [
			    { "$match" : { "$text" : { "$search" : request.GET.get('q' , '') } } } ,
			    { "$project" : { "score": { "$meta": "textScore" } , "title" : "$videoInfo.snippet.title" , "description" : "$videoInfo.snippet.description" 
			    , "thumbnail" : "$videoInfo.snippet.thumbnails.default.url" , "channel" : "$videoInfo.snippet.channelTitle" 
			    , "published" : "$videoInfo.snippet.publishedAt" , "video_id" : "$videoInfo.id" } } ,
			    { "$sort" : { "score" : -1 } },
			    { "$limit" : 20 } 
			]
			cursor = db.videos.aggregate(pipeline)
			rank = 1 
			for doc in cursor:
				a = doc['description'].encode('utf-8').strip()
				a = ''.join([i if ord(i) < 128 else '' for i in a])
				one = {}
				one['rank'] = rank
				rank = rank + 1 
				one['title'] = doc['title']
				one['description'] = utilities.sanitize(str(a[:400] + '....' if len(a) > 400 else len(a)))
				one['channel'] = doc['channel']				
				one['url'] = LinkMap.objects.get(global_link = doc['thumbnail']).local_link
				one['date'] = utilities.readable_date(doc['published'].split('T')[0])
				one['video_id'] = doc['video_id']
				one['score'] = doc['score']
				results.append(one)
			client.close()
			request.session['c_query'] = request.GET.get('q' , '') # cache the current result
			request.session['c_results'] = results
			#end
		else :
			results = request.session['c_results']
		p = int(request.GET.get('page' , '0'))
		
		#adding scores of history
		hist = utilities.get_videos(request.GET.get('q' , '') , request.user.username)
		for res in results :
			res['score'] = res['score'] + hist.get(res['video_id'] , 0.0)

		#sorting part
		sort_by = request.GET.get('sort' , 'rank_desc')
		if sort_by == 'rank_desc':
			results.sort(key=lambda r : r['score'] , reverse=True)
		elif sort_by == 'rank_asc':
			results.sort(key=lambda r : r['score'])
		elif sort_by == 'date_asc':
			results.sort(key=lambda r : datetime.datetime.strptime(r['date'], '%b %d , %Y').date())
		elif sort_by == 'date_desc':
			results.sort(key=lambda r : datetime.datetime.strptime(r['date'], '%b %d , %Y').date() , reverse=True)
		#sorting part
		lower = p*5
		upper = lower + 5 ;
		return render(request , 'polls/search.html' , { 'results' : results[lower:upper] , 'query' : request.GET.get('q' , '') , 
			'page' : p , 'sort' : request.GET.get('sort' , 'rank_desc') , 'name' : request.user.username})
	return redirect('/polls/home')

@login_required(login_url='/polls/index')
def video(request):
	if request.GET.get('video_id' , '') != '':		
		client = MongoClient()
		db = client['videos']
		doc = db.videos.find({"videoInfo.id" : request.GET.get('video_id' , '')})[0]
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		res['tags'] = ' , '.join(doc['videoInfo']['snippet']['tags'])
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = utilities.sanitize(a)
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = utilities.readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.get(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url']).local_link

		q = request.GET.get('q' , '')
		if q != '':
			words = re.sub("[^\w]+" , " " , q).split()
			stemmed_words = [stem(word) for word in words]
			for word in stemmed_words:
				try:
					r = UserClick.objects.get(username = request.user.username , word = word , video_id = request.GET.get('video_id' , ''))
					r.count = r.count + 1 
				except ObjectDoesNotExist:
					r = UserClick(username = request.user.username , word = word , video_id = request.GET.get('video_id' , '') , count = 1)			
				r.save()

		client.close()
		return render(request , 'polls/video.html' , { 'query' : request.GET.get('q' , '') , 'result' : res , 'name' : request.user.username} )
	return redirect('/polls/home')

def login_view(request):
	user = authenticate(username = request.POST.get('username' , '') , password = request.POST.get('password' , ''))
	if user is not None:
		login(request , user)
		if request.GET.get('next' , '') != '':
			return redirect(request.GET.get('next' , ''))
		return redirect('/polls/home')
	else:
		request.session['l_username'] = request.POST.get('username' , '')
		request.session['l_password'] = request.POST.get('password' , '')
		return redirect('/polls/index')

def logout_view(request):
	logout(request)
	return redirect('/polls/index')

def register(request):
	try:
		user = User.objects.get(username = request.POST.get('username' , ''))
		request.session['username'] = request.POST.get('username' , '')
		request.session['password'] = request.POST.get('password' , '')
		return redirect('/polls/index')
	except User.DoesNotExist:
		user = User.objects.create_user(request.POST.get('username' , '') , '' , request.POST.get('password' , ''))
		user = authenticate(username = request.POST.get('username' , '') , password = request.POST.get('password' , ''))
		login(request , user)
		if request.GET.get('next' , '') != '':
			return redirect(request.GET.get('next' , '') , { 'name' : request.POST.get('username' , '') })
		return redirect('/polls/home' , { 'name' : request.POST.get('username' , '') })

def index(request):
	if request.user.is_authenticated():
		return redirect('/polls/home')
	username = request.session.get('username' , '')
	password = request.session.get('password' , '')
	l_username = request.session.get('l_username' , '')
	l_password = request.session.get('l_password' , '')
	if username != '' or password != '':
		del request.session['username']
		del request.session['password']
	if l_username != '' or l_password != '':
		del request.session['l_username']
		del request.session['l_password']
	follow = request.GET.get('next')
	return render(request , 'polls/index.html' , { 'username' : username , 'password' : password , 
		'l_username' : l_username , 'l_password' : l_password , 'follow' : follow})
