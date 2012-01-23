# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login

class AuthStartMixin(object):
    '''Provide common business logic in auth start'''
    def get_callback(self):
        '''expecting service pass back all query params'''
        if not self.callback:
            raise NotImplementedError('Subclass must provide oauth_callback')
        
        self.callback = '{}?{}'.format(self.callback, 
                                       self.request.GET.urlencode())
                        
        return self.callback
    
class AuthenticateReturnMixin(object):
    '''Provide common business logic in auth return'''
    success_uri = None
    
    def authenticate(self):
        raise NotImplemented('Subclass provide actual authenticate logic')
    
    def get_success_uri(self):
        '''handle django convernon 'next' and 'redirect_field_name' param'''
        get = self.request.GET
        
        if 'redirect_field_name' in get and get['redirect_field_name'] in get:
            return get[get['redirect_field_name']]
        elif 'next' in get:
            return get['next'] 
        elif self.success_uri:            
            return self.success_uri
        else:
            return False
        
    def success(self, user):
        '''
        Called after authenticate success and logged user in.
        
        Subclass should override this method to provide actual business
        '''
        success_uri = self.get_success_uri()
        if success_uri:
            return HttpResponseRedirect(success_uri)
        else:
            # should be override
            return HttpResponse('linked with {}'.format(user.username))
        
    def failed(self):
        '''
        Called after authenticate failed.
        
        Subclass should override this method to provide actual business
        '''
        return HttpResponse('authenticate failed')
