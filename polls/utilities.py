import re , datetime

from .models import UserClick
from stemming.porter2 import stem

from .models import LinkMap , UserClick , UserBlacklist
from py2neo import Graph , NodeSelector
from pymongo import MongoClient


ZERO = datetime.timedelta(0)

class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO

utc = UTC()

def sanitize(string , anchors=True):
	if anchors :
		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
		for url in urls :
			string = string.replace(url , '<a class="ui link" href="'+url+'">' + url + '</a>')
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

def sort_dict(d): # in descending order of value !
	res = []
	for key in d:
		res.append({'id' : key , 'score' : d[key]})
	res.sort(key = lambda x : x['score'] , reverse = True)
	return res ;

def get_hist(username,this_video=''):
	videos={}
	clicked = UserClick.objects.filter(username = username)
	reference = datetime.datetime.now(utc)
	for click in clicked :
		c=reference-click.recenttime
		value=divmod(c.days * 86400 + c.seconds, 60)
		if videos.get(click.video_id , -1) == -1:
			videos[click.video_id] = value
		elif videos[click.video_id] > value : 
			videos[click.video_id] = value
	sorted_hist=[]
	sorted_hist=sort_dict(videos)
	mc = MongoClient()
	db = mc.videos
	ids_list = [x['id'] for x in sorted_hist]	
	results = []
	for id1 in ids_list:
		doc = db.videos.find({"videoInfo.id" : id1})[0]
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = a
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.filter(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url'])[0].local_link
		res['score'] = videos[res['video_id']]
		results.append(res)
	# raise TypeError('sad')
	return results

def get_trend(username,this_video=''):
	videos={}
	clicked = UserClick.objects.all()
	reference = datetime.datetime.now(utc)
	for click in clicked :
		value= 2*click.count-(reference-click.recenttime).seconds/60	
		if videos.get(click.video_id , -1) == -1:
			videos[click.video_id] = value
		else: 
			videos[click.video_id] = videos[click.video_id]+value
	sorted_trend=[]
	sorted_trend=sort_dict(videos)
	mc = MongoClient()
	db = mc.videos
	ids_list = [x['id'] for x in sorted_trend]	
	results = []
	for id1 in ids_list:
		doc = db.videos.find({"videoInfo.id" : id1})[0]
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = a
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.filter(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url'])[0].local_link
		res['score'] = videos[res['video_id']]
		if not is_blacklisted(username , res['video_id']):
			results.append(res)
	# raise TypeError('sad')
	return results

def get_channel_videos(username , channel_title):
	results = [] 
	mc = MongoClient()
	db = mc.videos
	cursor = db.videos.find({ "videoInfo.snippet.channelTitle" : channel_title }) 
	for doc in cursor :
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = a
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.filter(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url'])[0].local_link
		res['score'] = doc['videoInfo']['statistics']['viewCount']
		if not is_blacklisted(username , res['video_id']):
			results.append(res)
	mc.close() 
	return results

def get_blacklist(username):
	clicked = UserBlacklist.objects.filter(username = username)
	
	mc = MongoClient()
	db = mc.videos
	ids_list = [x.video_id for x in clicked]	
	results = []
	for id1 in ids_list:
		doc = db.videos.find({"videoInfo.id" : id1})[0]
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = a
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.filter(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url'])[0].local_link
		results.append(res)
	# raise TypeError('sad')
	return results

def get_recos(username , this_video='') :
	types = ["COMMON_DESC" , "COMMON_TAGS" , "SAME_CHANNEL" , "COMMON_TITLE"]
	weight = {"COMMON_DESC" : 1.5 , "COMMON_TAGS" : 2.5 , "COMMON_TITLE" : 4.5}	
	videos = {} 
	if this_video == '' : # get recos for history
		clicked = UserClick.objects.filter(username = username)
		for click in clicked :
			if videos.get(click.video_id , -1) == -1:
				videos[click.video_id] = 0
			videos[click.video_id] = videos[click.video_id] + click.count
	else : # get recos only for this query .
		videos[this_video] = 1
	graph = Graph(password = 'password')
	selector = NodeSelector(graph)
	all_recos = {}
	for video in videos:
		this_recos = {} # recos of this video
		selected = list(selector.select("Video" , id = video))[0]
		for t in types :
			rels = graph.match(start_node = selected , rel_type = t)
			# one direction .
			for rel in rels :
				enode = rel.end_node()
				other_id = enode['id']
				if t == "SAME_CHANNEL":
					this_recos[other_id] = this_recos.get(other_id , 0) + 1
				else:
					this_recos[other_id] = this_recos.get(other_id , 0) + weight[t] *  rel['no_common_words']
			# other direction .
			rels = graph.match(end_node = selected , rel_type = t)
			for rel in rels :
				snode = rel.start_node()
				other_id = snode['id']
				if t == "SAME_CHANNEL":
					this_recos[other_id] = this_recos.get(other_id , 0) + 1
				else:
					this_recos[other_id] = this_recos.get(other_id , 0) + rel['no_common_words']
		for a in this_recos :
			all_recos[a] = all_recos.get(a , 0.0) + videos[video]*this_recos[a] # consider the no. of times this video has been watched .

	if this_video == '' :
		sorted_recos = sort_dict(all_recos)[0:40]
	else :
		sorted_recos = sort_dict(all_recos)[0:10]
	mc = MongoClient()
	db = mc.videos
	ids_list = [x['id'] for x in sorted_recos]	
	results = []
	for id1 in ids_list:
		doc = db.videos.find({"videoInfo.id" : id1})[0]
		res = {}
		res['video_id'] = doc['videoInfo']['id']
		res['title'] = doc['videoInfo']['snippet']['title']
		res['description'] = doc['videoInfo']['snippet']['description']
		a = res['description'].encode('utf-8').strip()
		a = ''.join([i if ord(i) < 128 else '' for i in a])
		res['description'] = a
		res['channel'] = doc['videoInfo']['snippet']['channelTitle']
		res['date'] = readable_date(doc['videoInfo']['snippet']['publishedAt'].split('T')[0])
		res['url'] = LinkMap.objects.filter(global_link = doc['videoInfo']['snippet']['thumbnails']['default']['url'])[0].local_link
		res['score'] = all_recos[res['video_id']]
		if not is_blacklisted(username , res['video_id']) :
			results.append(res)
	# raise TypeError('sad')
	return results

def is_blacklisted(username , video_id):
	return 1 if len(UserBlacklist.objects.filter(username = username , video_id = video_id)) > 0 else 0