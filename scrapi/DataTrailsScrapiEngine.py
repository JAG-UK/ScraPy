# -*- coding: utf-8 -*-
"""DataTrails SCRAPI Engine implementation
"""
from ScrapiEngine import ScrapiEngine

from archivist.archivist import Archivist
from archivist.errors import ArchivistBadRequestError
from archivist.logger import set_logger

import cbor2
import logging
import requests

LOGGER = logging.getLogger(__name__)

class DataTrailsScrapiEngine(ScrapiEngine):

    def __init__(
        self,
        ts_args
    ):
        self._url = ts_args['url']
        self._client_id = ts_args['client_id']
        self._client_secret = ts_args['client_secret']

        self._archivist = Archivist(
            self._url,
            (self._client_id, self._client_secret)
        )
        set_logger(ts_args['log_level'] or "INFO")

        self._initialized = True

    def __str__(self) -> str:
        return f"DataTrails Scrapi Engine ({self._url})"

    def initialized(self):
        #TODO: need to check more status for emergent errors. Maybe send a NoOp?
        return self._initialized
    
    def getConfiguration(self):
        raise NotImplementedError('getConfiguration')
    
    def registerSignedStatement(self, statement):
        # TODO: DataTrails SDK doesn't have native SCITT support yet
        # but we can still use the Archivist object to look after our
        # authenticated connection to the server
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK
        headers = self._archivist._add_headers({})
        response = requests.post(
            f"{self._url}/archivist/v1/publicscitt/entries",
            data=statement,
            headers=headers
        )

        # Three main failure modes:
        # - General network or API error: non-200 return
        # - Malformed statement or general errors will not return an operation ID
        # - Failure of registration policy or somesuch will return a failed operation
        if response.status_code != 200:
            logging.debug({response})
            raise Exception(f"Failed to register statement: {response}")

        # FIXME: The DataTrails implementation currently returns JSON.
        # Fake up CBOR response here so that common code doesn't need to change
        return None, cbor2.dumps(response.json())

    def checkRegistration(self, registration_id):
        logging.debug(f'checking on operation {registration_id}')
        # TODO: DataTrails SDK doesn't have native SCITT support yet
        # but we can still use the general robust machinery to submit
        # calls to the REST endpoint.
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK.
        # Worth using the DataTrails SDK rather than raw requests for
        # this one because it includes generic error handling like 429s
        # internally
        headers = headers = self._archivist._add_headers({})
        response = requests.get(
            f"{self._url}/archivist/v1/publicscitt/operations/{registration_id}",
            headers=headers
        )
        if response.status_code == 400:
            # TODO The Public SCITT endpoint returns 400 for Events that have not
            # made it across the sharing boundary yet. Bodge in a non-fatal fix
            # here but this needs to be made better.
            # We're not in any position to know if this is just running or a
            # permanent problem, so return 'unspecified' and let the client app
            # sort it out for now.
            logging.debug(f"Suspected temporary propagation 400 error")
            return None, cbor2.dumps({'operationID': registration_id, 'status': 'running'})
        elif response.status_code not in [200, 202]:
            logging.debug(f"FAILED to get operaiton status: {response.status_code}")
            return response.content, None

        # FIXME: The DataTrails implementation currently returns JSON.
        # Fake up CBOR response here so that common code doesn't need to change
        return None, cbor2.dumps(response.json())

    def resolveReceipt(self, entry_id):
        logging.debug(f'resolving receipt {entry_id}')
        # TODO: DataTrails SDK can't process non-JSON responses yet
        # but we can still use the Archivist object to look after our
        # authenticated connection to the server then call out to requests
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK
        headers = headers = self._archivist._add_headers({})
        response = requests.get(
            f"{self._url}/archivist/v1/publicscitt/entries/{entry_id}/receipt",
            headers=headers
        )
        if response.status_code != 200:
            logging.debug(f"FAILED to get receipt: {response.status_code}")
            return response.content, None
        
        return None, response.content
