from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

import flickrapi
from pyfyd.models import FlickrAccount
from pyfyd.common.views import AuthStartMixin

class BaseV(View):
    '''Base class for all views that will use douban oauth client'''
    def __init__(self, *args, **kwargs):
        super(BaseV, self).__init__(*args, **kwargs)
        
        self.client = flickrapi.FlickrAPI(settings.FLICKR_CONSUMER_KEY,
                                          settings.FLICKR_CONSUMER_SECRET,
                                          store_token=False)
        
class AuthStartV(AuthStartMixin, BaseV):        
    '''
    start from here.
    
    flickr legacy auth doesnt allow pass callback at call-time
    '''
    #callback = False
    
    def get(self, request):
        return HttpResponseRedirect(self.client.web_login_url('write'))
    
    
class AuthReturnV(BaseV):        
    '''
    flickr redirect user to here after authorize
    
    Subclass MUST override get() to provide actual business logic.
    DO call super get() first to make self.account available
    '''
    account = None
    
    def get(self, request):
        try:
            frob = request.GET['frob']
        except IndexError:
            raise Exception('frob not found')        
        else:
            rsp = self.client.auth_getToken(frob=frob)
            rsp = rsp.find('auth')            
            user = rsp.find('user')
            
            self.account = FlickrAccount(nsid=user.attrib['nsid'],
                                         username = user.attrib['username'],
                                         fullname = user.attrib['fullname'],
                                         token = rsp.find('token').text)               
            
            
class AuthorizeReturnV(AuthReturnV):
    def get(self, request):
        '''
        Update access key and other info to user account
        '''
        # get self.account available
        super(AuthorizeReturnV, self).get(request)
        
        try:
            linked_account = FlickrAccount.objects.get(nsid=self.account.nsid)
        except FlickrAccount.DoesNotExist:
            self.account.owner = request.user
            self.account.save()
        else:
            linked_account.username = self.account.username
            linked_account.fullname = self.account.fullname
            linked_account.token = self.account.token
            linked_account.owner = request.user
            linked_account.save()