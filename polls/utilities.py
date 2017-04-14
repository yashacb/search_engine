import re , datetime

from .models import UserClick
from stemming.porter2 import stem

def sanitize(string):
	urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
	for url in urls :
		string = string.replace(url , '<a class="ui link">' + url + '</a>')
	string = re.sub('[\n]+' , '<br />' , string)
	return string

def get_urls(string):
	urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
	return urls

def readable_date(string):
	d = datetime.datetime.strptime(string, '%Y-%m-%d').date() # %Y-%m-%%d
	return d.strftime('%b %d , %Y')

def get_videos(q , uname):
	vids = {}
	words = re.sub("[^\w]+" , " " , q).split()
	stemmed_words = [stem(word) for word in words]
	for word in stemmed_words:
		videos = UserClick.objects.filter(username = uname , word = word)		
		for v in videos:
			vids[v.video_id] = vids.get(v.video_id , 0) + v.count*len(word) # need to change this
	return vids