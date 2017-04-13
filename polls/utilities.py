import re , datetime

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