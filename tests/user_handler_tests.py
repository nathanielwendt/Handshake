import json
import models
from test_utils import AppEngineTest
import view_models
from models import getUUID, IDTYPE

class TestUserCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestUserCreationHandler, self).setUp()
        self.endpoint = "/v1/user"

    def test_basic(self):
        self.method = 'POST'
        self.params = {
            #"name": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["3603153324"]),
        }
        self.send()

    def test_signup_valid(self):
        self.method = 'POST'
        self.params = {
            "name": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["3603153324"]),
        }
        self.send()
        self.expect_resp_conforms(view_models.User.view_contract())

        new_user_id = self.response_data["userId"]
        user = models.User.get_by_id(new_user_id)
        self.assertIsNotNone(user)

        self.assertEqual(self.response_data["name"], "John Doe")
        self.assertEqual(self.response_data["email"], "john@gmail.com")
        self.assertEqual(self.response_data["emails"], json.dumps(["john@gmail.com", "jane@gmail.com"]))
        self.assertEqual(self.response_data["phoneNumbers"], json.dumps(["3603153324"]))

    def test_signup_malformed_param(self):
        self.method = 'POST'
        self.params = {
            "nameXXXXX": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["3603153324"]),
        }
        self.send()
        self.expect_resp_code(400)
        self.assertEqual(True, bool(self.response_data["has_meta_data"]))

    def test_signup_malformed_value(self):
        self.method = 'POST'
        self.params = {
            "name": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["NOT A NUMBER"]),
        }
        self.send()
        self.expect_resp_code(400)
        self.assertEqual(True, bool(self.response_data["has_meta_data"]))


class TestUserHandler(AppEngineTest):
    def setUp(self):
        super(TestUserHandler, self).setUp()
        self.user_id = getUUID(IDTYPE.USER)
        user = models.User(id=self.user_id, name="Kate Barns")
        user.put()

    def test_basic(self):
        self.endpoint = "/v1/user/" + self.user_id
        self.method = 'GET'
        self.send()
        self.expect_resp_param("userId", self.user_id)
        self.expect_resp_param("name", "Kate Barns")

    def test_invalid_user(self):
        self.endpoint = "/v1/user/" + self.INVALID_ID
        self.method = 'GET'
        self.send()
        self.expect_resp_code(422)