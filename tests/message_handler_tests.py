import unittest
import json
import urllib
import models
from test_utils import AppEngineTest
import datetime
from models import getUUID, IDTYPE

class TestMessageCreationHandler(AppEngineTest):
    pass


class TestMessageNativeCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestMessageNativeCreationHandler, self).setUp()
        self.endpoint = "/v1/message/native"
        self.now = datetime.datetime.utcnow()

    def test(self):
        self.method = 'POST'
        self.params["senderUserId"] = "sender001"
        #self.params["memberName"] = "Ant"
        #self.params["routeName"] = "Green Leaf"
        self.params["message"] = "Yo dude you have to check this out!"
        self.send()
        self.expect_resp_code(422)


