from ScrapiEngine import ScrapiEngine

class DataTrailsScrapiEngine(ScrapiEngine):

    def __init__(
        self,
        ts_args
    ):
        self._url = ts_args['url']
        self._client_id = ts_args['client_id']
        self._client_secret = ts_args['client_secret']
        self._initialized = True

    def __str__(self) -> str:
        return f"DataTrails Scrapi Engine ({self._url})"

    def initialized(self):
        #TODO: need to check more status for emergent errors
        return self._initialized
    
    def getConfiguration(self):
        raise NotImplementedError('getConfiguration')
    
    def registerSignedStatement(self, statement):
        raise NotImplementedError('registerSignedStatement')

    def checkRegistration(self, registration_id):
        raise NotImplementedError('checkRegistration')
    
    def resolveReceipt(self, receipt_id):
        raise NotImplementedError('resolveReceipt')

