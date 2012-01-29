import json

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from tweepy import OAuthHandler, API
from douban import OAuthClient2 
        
class AccountUtilsMixin(object):
    '''Set of util methods for external account'''
    def update(self, new):
        updated = False      
        # update key and secret if changed
        for key in self.attribute_keys:
            if self.__dict__[key] != new.__dict__[key]:
                self.__dict__[key] = new.__dict__[key]
                updated = True
        
        if updated:
            self.save()
            
        return self
    
    @classmethod
    def find_linked(cls, account):
        '''Find exists linked account queryset'''
        return cls.objects.filter(id=account.id)
    
    @classmethod
    def get_linked(cls, account):
        '''get single existing linked account'''
        return cls.objects.get(id=account.id)
    
    @classmethod
    def get_from_token(cls, **kwargs):
        '''
        Subclass should override this
        '''
        raise NotImplemented()
    
    @classmethod
    def link_external(cls, user, **kwargs):
        '''
        fetch douban account info by given access token, 
        then link it with given user
        '''
        account = cls.get_from_token(**kwargs)
                
        try:
            existing = cls.get_linked(account)
        except cls.DoesNotExist:
            pass
        else:        
            account = existing.update(account)
            
        account.owner = user
        account.save()
        
        return account
    

class TwitterAccount(models.Model):
    '''A twitter account that linked with a django user'''
    # override default AutoField pk to force id to be assigned
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255)
    
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    owner = models.ForeignKey(User, unique=True)
    
            
class GoogleAccount(models.Model):
    '''A google account that linked with a django user'''
    username = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255, blank=True)
    
    language = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    owner = models.ForeignKey(User, unique=True)
    
    
class DoubanAccount(models.Model, AccountUtilsMixin):
    '''A douban account that linked with a django user'''
    # override default AutoField pk to force id to be assigned
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255)
    
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    owner = models.ForeignKey(User, unique=True)
    
    _PROFILE_URI = 'http://api.douban.com/people/%40me?alt=json'
    @classmethod
    def get_from_token(cls, key, secret, uid):
        client = OAuthClient2(key, secret)
        
        resp, content = client.request(cls._PROFILE_URI)
        if 200 == int(resp['status']):
            resp = json.loads(content)
        else:
            raise Exception('{}: {}'.format(resp['status'], content))
        
        id = resp['uri']['$t'].split('/')[-1]
        username = resp['db:uid']['$t']
        fullname = resp['title']['$t']
        
        return cls(id=id, username=username, fullname=fullname,
                   key=key, secret=secret)    
    
class FlickrAccount(models.Model):
    '''A flickr account that linked with a django user'''
    nsid = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255)
    
    token = models.CharField(max_length=255)
    
    owner = models.ForeignKey(User, unique=True)