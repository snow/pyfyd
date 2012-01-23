import json

from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.conf import settings

from pyfyd.models import DuplicatedUsername

class BaseBackend(ModelBackend):
    '''base class for all openid auth backend'''
    CID = False
    attribute_keys = ['key', 'secret']
    account_cls = False
    
    @classmethod
    def get_account_from_token(cls, key, secret, *args, **kwargs):
        '''
        Subclass should override this
        '''
        raise NotImplemented()
    
    @classmethod
    def update_account(cls, old, new):
        updated = False      
        # update key and secret if changed
        for key in cls.attribute_keys:
            if old.__dict__[key] != new.__dict__[key]:
                old.__dict__[key] = new.__dict__[key]
                updated = True
        
        if updated:
            old.save()
            
        return old
    
    @classmethod
    def find_linked(cls, account):
        '''Find exists linked account'''
        return cls.account_cls.objects.filter(id=account.id)
    
    @classmethod
    def link_external(cls, key, secret, user, **kwargs):
        '''
        fetch douban account info by given access token, 
        then link it with given user
        '''
        account = cls.get_account_from_token(key, secret, **kwargs)        
        linked = cls.find_linked(account)
        
        if linked.exists():
            account = cls.update_account(linked.get(), account)
            
        account.owner = user
        account.save()
    
    def authenticate(self, cid, key, secret, **kwargs):
        if False == self.CID:
            raise NotImplemented('CID must be configured in subclass')
        
        if self.CID != cid:
            return None
            
        account = self.get_account_from_token(key, secret, **kwargs)        
        linked = self.find_linked(account)
        
        if linked.exists():
            account = self.update_account(linked.get(), account)
        elif User.objects.filter(username=account.username).exists():
            raise DuplicatedUsername(account.username)
        else:
            if 'email' in account.__dict__:                
                email = account.email
            else:
                email = '{}@n.cc'.format(account.username)
                
            account.owner = User.objects.create_user(account.username, email)
            account.save()
            
        return account.owner
        