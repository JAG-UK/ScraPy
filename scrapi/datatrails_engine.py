# -*- coding: utf-8 -*-
"""DataTrails SCRAPI Engine implementation
"""

import logging
from pprint import pprint

from archivist.archivist import Archivist
from archivist.logger import set_logger

import cbor2
from pycose.messages import Sign1Message
import requests

from scrapi_engine import ScrapiEngine
from scrapi_exception import ScrapiException

LOGGER = logging.getLogger(__name__)


class DatatrailsEngine(ScrapiEngine):
    """DataTrails SCRAPI Engine implementation"""

    def __init__(self, ts_args):
        self._url = ts_args["url"]
        self._client_id = ts_args["client_id"]
        self._client_secret = ts_args["client_secret"]

        self._archivist = Archivist(self._url, (self._client_id, self._client_secret))
        set_logger(ts_args["log_level"] or "INFO")

        self._initialized = True

    def __str__(self) -> str:
        return f"DataTrails Scrapi Engine ({self._url})"

    def initialized(self):
        # TODO: need to check more status for emergent errors. Maybe send a NoOp?
        return self._initialized

    def get_configuration(self):
        raise NotImplementedError("get_configuration")

    def register_signed_statement(self, statement):
        # DataTrails SDK doesn't have native SCITT support yet
        # but we can still use the Archivist object to look after our
        # authenticated connection to the server
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK
        headers = self._archivist._add_headers({})
        response = requests.post(
            f"{self._url}/archivist/v1/publicscitt/entries",
            data=statement,
            headers=headers,
            timeout=20000,
        )

        # Three main failure modes:
        # - General network or API error: non-200 return
        # - Malformed statement or general errors will not return an operation ID
        # - Failure of registration policy or somesuch will return a failed operation
        if response.status_code != 200:
            logging.debug("%s", str(response))
            raise ScrapiException(f"Failed to register statement: {response}")

        # The DataTrails implementation currently returns JSON.
        # Fake up CBOR response here so that common code doesn't need to change
        return None, cbor2.dumps(response.json())

    def check_registration(self, registration_id):
        logging.debug("checking on operation %s", registration_id)
        # DataTrails SDK doesn't have native SCITT support yet
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
            headers=headers,
            timeout=20000,
        )
        if response.status_code == 400:
            # Note: The Public SCITT endpoint returns 400 for Events that have not
            # made it across the sharing boundary yet. Bodge in a non-fatal fix
            # here but this needs to be made better.
            # We're not in any position to know if this is just running or a
            # permanent problem, so return 'unspecified' and let the client app
            # sort it out for now.
            logging.debug("Suspected temporary propagation 400 error")
            return None, cbor2.dumps(
                {"operationID": registration_id, "status": "running"}
            )

        if response.status_code not in [200, 202]:
            logging.debug("FAILED to get operation status: %s", response.status_code)
            return response.content, None

        # As things stand DataTrails returns JSON. This will change in future releases.
        # Fake up CBOR response here so that common code doesn't need to change
        return None, cbor2.dumps(response.json())

    def resolve_receipt(self, entry_id):
        logging.debug("resolving receipt %s", entry_id)
        # DataTrails SDK can't process non-JSON responses yet
        # but we can still use the Archivist object to look after our
        # authenticated connection to the server then call out to requests
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK
        headers = headers = self._archivist._add_headers({})
        response = requests.get(
            f"{self._url}/archivist/v1/publicscitt/entries/{entry_id}/receipt",
            headers=headers,
            timeout=20000,
        )
        if response.status_code != 200:
            logging.debug("FAILED to get receipt: %s", response.status_code)
            return response.content, None

        return None, response.content

    def resolve_signed_statement(self, entry_id):
        logging.debug("resolving entry %s", entry_id)
        # DataTrails SDK can't process non-JSON responses yet
        # but we can still use the Archivist object to look after our
        # authenticated connection to the server then call out to requests
        # When the SCRAPI standard settles this code will migrate to the
        # core DataTrails SDK
        headers = headers = self._archivist._add_headers({})
        response = requests.get(
            f"{self._url}/archivist/v1/publicscitt/entries/{entry_id}",
            headers=headers,
            timeout=20000,
        )
        if response.status_code != 200:
            logging.debug("FAILED to get entry: %s", response.status_code)
            return response.content, None

        # Note: DataTrails currently returns the _counter_SignedStatement
        # but SCRAPI wants the original SignedStatement exactly as submitted
        # by the Issuer, so strip off the outer envelope
        decoded_statement = Sign1Message.decode(response.content)
        inner_statement = Sign1Message.decode(decoded_statement.payload)

        print("\ncbor decoded cose sign1 statement:\n")
        print("protected headers:")
        pprint(inner_statement.phdr)
        print("\nunprotected headers: ")
        pprint(inner_statement.uhdr)
        print("\npayload: ", inner_statement.payload)
        print("payload hex: ", inner_statement.payload.hex())

        return None, inner_statement

    def issue_signed_statement(self, statement):
        return (None, None)
