import webapp2
import json
import main
import unittest
from utils import APIUtils, NamingGenerator
from google.appengine.ext import testbed


class AppEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        self.INVALID_ID = "9999999999999"
        super(AppEngineTest, self).__init__(*args)

    def setUp(self):
        super(AppEngineTest, self).setUp()
        self.endpoint = ''
        self.method = 'GET'
        self.response = ''
        self.params = {}
        self.response_data = ''

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def send(self):
        if self.method == 'POST':
            request = webapp2.Request.blank(self.endpoint, POST=self.params)
        #GET, PUT, DELETE methods here
        else:
            endpoint_with_params = self.endpoint + "?"
            prefix = ""
            for key,value in self.params.items():
                endpoint_with_params += prefix + key + "=" + value
                prefix = "&"
            request = webapp2.Request.blank(endpoint_with_params)
            request.method = self.method

        self.response = request.get_response(main.app)

        try:
            self.response_data = json.loads(self.response.body)
        except ValueError:
            self.response_data = {}

    def expect_resp_code(self, code):
        self.assertEqual(self.response.status_int, code)

    def expect_resp_param(self, name, value=None):
        if value is None:
            self.assertIsNotNone(self.response_data[name])
        else:
            self.assertEqual(self.response_data[name], value)

    def expect_resp_conforms(self, contract):
        APIUtils.check_contract_conforms(contract, self.response_data, self.assertTrue)

    @staticmethod
    def set_up_naming():
        NamingGenerator.initialize_ds_names(local_dir="../data/")
