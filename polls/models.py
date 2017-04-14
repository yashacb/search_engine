# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Question(models.Model):
	question_text = models.CharField(max_length = 200)
	pub_date = models.DateTimeField('date published')

class Choice(models.Model):
	question = models.ForeignKey(Question , on_delete = models.CASCADE)
	choice_text = models.CharField(max_length = 200)
	votes = models.IntegerField(default = 0)

class LinkMap(models.Model):
	global_link = models.CharField(max_length = 500)
	local_link = models.CharField(max_length = 500)

class UserClick(models.Model):
	word = models.CharField(max_length = 50)
	video_id = models.CharField(max_length = 50)
	count = models.IntegerField(default = 0)
	username = models.CharField(max_length = 100)

	class Meta:
		unique_together = (('word' , 'video_id' , 'username'))

