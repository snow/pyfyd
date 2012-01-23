from django.conf import settings
from tweepy import OAuthHandler, API

from pyfyd.models import TwitterAccount
from pyfyd.common.utils import BaseBackend

class TwitterBackend(BaseBackend):
    '''Twitter auth backend'''
    CID = 'pyfyd.twitter.utils.TwitterBackend'
    account_cls = TwitterAccount
    attribute_keys = ['key', 'secret', 'username', 'fullname']
    
    @classmethod
    def get_account_from_token(cls, key, secret):
        oauth = OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                             settings.TWITTER_CONSUMER_SECRET,
                             secure=True)
        oauth.set_access_token(key, secret)
        twitter_user = API(auth_handler=oauth).verify_credentials()
        
        return TwitterAccount(id=twitter_user.id, 
                              key=key,
                              secret=secret,
                              username=twitter_user.screen_name,
                              fullname=twitter_user.name)
