import json

from django.conf import settings

from pyfyd.models import DoubanAccount
from pyfyd.common.utils import BaseBackend
from client import OAuthClient 

_PROFILE_URI_BASE = 'http://api.douban.com/people/{}?alt=json'
class DoubanBackend(BaseBackend):
    '''Douban auth backend'''
    CID = 'pyfyd.douban.utils.DoubanBackend'
    account_cls = DoubanAccount
    attribute_keys = ['key', 'secret', 'username', 'fullname']
    
    @classmethod
    def get_account_from_token(cls, key, secret, uid):
        client = OAuthClient(key=settings.DOUBAN_CONSUMER_KEY,
                             secret=settings.DOUBAN_CONSUMER_SECRET)
        client.login(key, secret)
        
        resp = client.access_resource('GET', _PROFILE_URI_BASE.format(uid))
        resp = json.loads(resp.read())
        
        id = resp['uri']['$t'].split('/')[-1]
        username = resp['db:uid']['$t']
        fullname = resp['title']['$t']
        
        return DoubanAccount(id=id, 
                             username=username,
                             key=key,
                             secret=secret,
                             fullname=fullname)    