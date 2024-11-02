# -*- coding: utf-8 -*-
"""Portable SCRAPI connection interface

This module contains the core SCRAPI calls which should be
portable for any client integration.
"""

#TODO next
#
#Start calling functions
#Unknowns:
# - How to return COSE/JSON _and_ indicate errors?
# - Use old emulator code for read/return of COSE. Minimal processing in here

# Standard imports
import cbor2
from copy import deepcopy
import logging
from time import time
from typing import Any, BinaryIO

# Scrapi imports
import rfc9290


# All Engines go here
from DataTrailsScrapiEngine import DataTrailsScrapiEngine

LOGGER = logging.getLogger(__name__)


class ScrapiException(Exception):
    """Indicate SCRAPI-specific errors
    """


class Scrapi():  # pylint: disable=too-many-instance-attributes
    
    """Portable class for all Scrapi implementations.

    args:
        ts_type (str): Type of transparency service
        ts_args (dict): TS-specific initialization params

    """
    def __init__(
        self,
        ts_type: str,
        ts_args: dict
    ):
        match ts_type:
            case 'DataTrails':
                self.engine = DataTrailsScrapiEngine(ts_args)
            
            case _:
                raise ScrapiException(f"Unknown engine type: {ts_type}'") 

    def __str__(self) -> str:
        if self.engine:
            return self.engine.__str__()
        else:
            return f"Scrapi (uninitialized)"

    # The following methods require a Transparency Service and so require the
    # engine to be initialized

    """Helper to protect all calls that need a valid TS connection"""
    def checkEngine(self):
        logging.debug("Scrapi checking engine liveness...")

        if not self.engine:
            raise ScrapiException("No Transparency Service engine specified")
        
        if not self.engine.initialized():
            raise ScrapiException("Transparency Service engine malfunction")
        
        logging.debug("Scrapi engine check SUCCESS")

    """Wrapper for SCRAPI Transparency Configuration call

    args:
        none
    
    returns:
        application/json
    """
    def getConfiguration(self):
        self.checkEngine()

        return self.engine.getConfiguration()
        
    """Wrapper for SCRAPI Register Signed Statement call

    args:
        Content-Type: application/cose

        18([                            / COSE Sign1         /
          h'a1013822',                  / Protected Header   /
          {},                           / Unprotected Header /
          null,                         / Detached Payload   /
          h'269cd68f4211dffc...0dcb29c' / Signature          /
        ])
    
    returns:
        application/json
    """
    def registerSignedStatement(self, statement):
        self.checkEngine()

        err, result = self.engine.registerSignedStatement(statement)
        if err:
            # Decode and log the RFC9290 Problem Details. 
            problem_details = rfc9290.decode_problem_details(result)
            print(problem_details)
            return None
        else:
            # Pull the registration ID out
            operation = cbor2.loads(result)

            # Check for common errors
            if not 'status' in operation or operation['status'] == 'failed':
                raise Exception(f"Statement Registration Failed")
        
            if not 'operationID' in operation:
                raise Exception(f"No Operation ID for Statement")
            
            # Seems legit, send it back
            return operation['operationID']

    """Wrapper for SCRAPI Check Registration call

    args:
        registration_id (str): 
    
    returns:
        application/json
    """
    def checkRegistration(self, registration_id):
        self.checkEngine()

        err, result = self.engine.checkRegistration(registration_id)
        if err:
            # Decode and log the RFC9290 Problem Details. 
            problem_details = rfc9290.decode_problem_details(result)
            print(problem_details)
            return None
        else:
            # Pull the registration ID out
            operation = cbor2.loads(result)

            # Check for common errors
            if not 'operationID' in operation:
                raise Exception(f"Operation ID link lost")

            if not 'status' in operation:
                raise Exception(f"No LRO status for Operation ID")

            # Seems legit, send it back
            return cbor2.loads(result)
                                                   
    """Wrapper for SCRAPI Resolve Receipt call

    args:
        entry_id (str): 
    
    returns:
        application/cose
    """
    def resolveReceipt(self, entry_id):
        self.checkEngine()

        err, result = self.engine.resolveReceipt(entry_id)

        if err:
            # Decode and log the RFC9290 Problem Details. 
            problem_details = rfc9290.decode_problem_details(result)
            print(problem_details)
            return None
        else:
            return result

    """Utility function for synchronous receipt generation.
    
    CAUTION! On some Transparency Service implementations this call may block
    for a *very* long time!
    
    args:
        Content-Type: application/cose

        18([                            / COSE Sign1         /
          h'a1013822',                  / Protected Header   /
          {},                           / Unprotected Header /
          null,                         / Detached Payload   /
          h'269cd68f4211dffc...0dcb29c' / Signature          /
        ])
    
    returns:
        application/cose
    """
    def registerSignedStatementSync(self, statement):
        res = self.registerSignedStatement(statement)
        rid = res['registration_id']
        while True:
            res = self.checkRegistration(rid)
            if res['status'] == 'running':
                # Wait a moment then go back around
                logging.info(f"Registration operation {rid} still running. Waiting...")
                time.sleep(2)
            elif res['status'] == 'failed':
                # Fatal. Return
                logging.info(f"Registration operation {rid} FAILED.")
                return None
            elif res['status'] == 'success':
                # All done. Extract COSE and returtn the receipt
                logging.info(f"Registration operation {rid} SUCCESS.")
                return "COSE goes here!"
            else:
                logging.error(f"Malformed response from checkRegistration: {res}")
                return None
