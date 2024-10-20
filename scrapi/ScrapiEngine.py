# -*- coding: utf-8 -*-
"""Pure virtual class to define legal shape of TS Engines for SCRAPI

This module contains the base class which defines the standard
interactions that any implementation should support. These are then
overridden in specific engine files for each Transparency Service
implementation.
"""

from abc import ABC
from abc import abstractmethod

class ScrapiEngine(ABC):
    @abstractmethod
    def initialized(self):
        pass
    
    @abstractmethod
    def getConfiguration(self):
        pass
    
    @abstractmethod
    def registerSignedStatement(self, statement):
        pass

    @abstractmethod
    def checkRegistration(self, registration_id):
        pass
    
    @abstractmethod
    def resolveReceipt(self, receipt_id):
        pass
