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
            "id": "123456",
            #"name": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["3603153324"]),
        }
        self.send()

    def test_signup_valid(self):
        self.method = 'POST'
        self.params = {
            "id": "123456",
            "name": "John Doe",
            "email": "john@gmail.com",
            "emails": json.dumps(["john@gmail.com", "jane@gmail.com"]),
            "phoneNumbers": json.dumps(["3603153324"]),
        }
        self.send()
        self.expect_resp_conforms(view_models.User.view_contract())

        self.expect_resp_param("id", "123456")
        self.expect_resp_param("email", "john@gmail.com")
        self.expect_resp_param("emails", json.dumps(["john@gmail.com", "jane@gmail.com"]))
        self.expect_resp_param("phoneNumbers", json.dumps(["3603153324"]))
        new_user_id = self.response_data["id"]
        user = models.User.get_by_id(new_user_id)
        self.assertIsNotNone(user)

    def test_signup_malformed_param(self):
        self.method = 'POST'
        self.params = {
            "id": "123456",
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
            "id": "123456",
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
        self.user_id = "123456"
        user = models.User(id=self.user_id, name="Kate Barns")
        user.put()

    def test_basic(self):
        self.endpoint = "/v1/user/" + self.user_id
        self.method = 'GET'
        self.send()
        self.expect_resp_param("id", self.user_id)
        self.expect_resp_param("name", "Kate Barns")

    def test_invalid_user(self):
        self.endpoint = "/v1/user/" + self.INVALID_ID
        self.method = 'GET'
        self.send()
        self.expect_resp_code(422)


class TestUserNotificationsHandler(AppEngineTest):
    def setUp(self):
        super(TestUserNotificationsHandler, self).setUp()
        self.endpoint += "/v1/user/"
        self.method = "PUT"

        self.user = models.User(id="12345")
        self.user.put()

    def test_basic(self):
        self.endpoint += self.user.get_id() + "/notifications"
        self.params["pushRegKey"] = "push-reg-key"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Default.view_contract())
        self.assertEqual(self.user.pushRegKey, "push-reg-key")

    def test_valid_multiple(self):
        self.endpoint += self.user.get_id() + "/notifications"
        self.params["pushRegKey"] = "push-reg-key"
        self.send()
        self.send()
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Default.view_contract())
        self.assertEqual(self.user.pushRegKey, "push-reg-key")