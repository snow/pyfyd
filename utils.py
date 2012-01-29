from django.contrib.auth.backends import ModelBackend

class ThirdpartyAuthBackend(ModelBackend):
    '''
    This backend get a thirdpart account model, consider it as trusted
    and return the account's owner
    '''
    CID = 'pyfyd.utils.ThirdpartyAuthBackend'
    
    def authenticate(self, CID, account):
        # we only want to auth those that explicitly named this backend
        if CID == self.CID:
            return account.owner
        else:
            return