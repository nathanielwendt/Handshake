import unittest
import json
import urllib

import models
from test_utils import AppEngineTest
import view_models
import datetime
from handler_utils import getUUID, IDTYPE
from utils import APIUtils

class TestGeneral(AppEngineTest):
    def test_malformed1(self):
        self.endpoint = "/v1/bad/endpoint/not/real"
        self.params["userId"] = "user001"
        self.method = 'POST'
        self.send()
        self.expect_resp_code(404)

class TestAccessSlot(AppEngineTest):
    def setUp(self):
        super(TestAccessSlot, self).setUp()

        self.now = datetime.datetime.now()
        self.slot_id = getUUID(IDTYPE.ACCESS_SLOT)
        data = {
            "id": self.slot_id,
            "routeId": "route001",
            "active": True,
            "start": self.now,
            "end": self.now + datetime.timedelta(hours=2),
            "repeatInterval": 60 * 60 * 24,
            "cutoff": self.now + datetime.timedelta(days=3),
            "currStart": self.now,
            "currEnd": self.now + datetime.timedelta(hours=2)
        }
        self.access_slot = models.AccessSlot(**data)
        self.access_slot.put()

    def test_basic_checks(self):
        t1 = self.now + datetime.timedelta(hours=1)
        t2 = self.now + datetime.timedelta(hours=3)
        t3 = self.now + datetime.timedelta(days=1, hours=1)
        t4 = self.now + datetime.timedelta(days=1, hours=3)
        t5 = self.now + datetime.timedelta(days=3, hours=1)
        self.assertTrue(self.access_slot.check_and_update_slot(t1))
        self.assertFalse(self.access_slot.check_and_update_slot(t2))
        self.assertTrue(self.access_slot.check_and_update_slot(t3))
        self.assertFalse(self.access_slot.check_and_update_slot(t4))
        self.assertFalse(self.access_slot.check_and_update_slot(t5))

    #test that the slot updates its own currStart and currEnd based on
    #most recent queries
    def test_update(self):
        t1 = self.now + datetime.timedelta(days=1, hours=1)
        self.assertTrue(self.access_slot.check_and_update_slot(t1))

        slot = models.AccessSlot.get_by_id(self.slot_id)
        self.assertNotEqual(self.now, slot.currStart)
        self.assertEqual(self.now, slot.start)


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


class TestRouteCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteCreationHandler, self).setUp()
        self.endpoint = "/v1/route"
        self.now = datetime.datetime.utcnow()

    def test_basic(self):
        self.method = 'POST'
        self.params = {
            "userId": "user001",
            "emails": json.dumps(["email12@gmail.com","email5@gmail.com"]),
            "phoneNumbers": json.dumps(["3533524434"]),
            "slots": json.dumps([
                {
                    "start": APIUtils.datetime_to_epoch(self.now),
                    "end": APIUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": APIUtils.datetime_to_epoch(self.now)
                }
            ])
        }
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        route_id = self.response_data["routeId"]
        slot_id = self.response_data["slots"][0]["slotId"]

        route = models.Route.get_by_id(route_id)
        slot = models.AccessSlot.get_by_id(slot_id)
        self.assertIsNotNone(route)
        self.assertIsNotNone(slot)

    def test_invalid_no_email_or_phone_num(self):
        self.method = 'POST'
        self.params = {
            "userId": "user001",
            #"emails": json.dumps(["email12@gmail.com","email5@gmail.com"]),
            #"phoneNumbers": json.dumps(["3533524434"]),
            "slots": json.dumps([
                {
                    "start": APIUtils.datetime_to_epoch(self.now),
                    "end": APIUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": APIUtils.datetime_to_epoch(self.now)
                }
            ])
        }
        self.send()
        self.expect_resp_code(422)

    def test_malformed_user_id_and_slots(self):
        self.method = 'POST'
        self.params = {
            #"userId": "user001",
            "emails": json.dumps(["email12@gmail.com","email5@gmail.com"]),
            "phoneNumbers": json.dumps(["3533524434"]),
            "slots": json.dumps([
                {
                    "start": APIUtils.datetime_to_epoch(self.now),
                    #"end": APIUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": APIUtils.datetime_to_epoch(self.now)
                }
            ])
        }
        self.send()
        self.expect_resp_code(400)

class TestRouteHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteHandler, self).setUp()
        self.route_id = getUUID(IDTYPE.ROUTE)
        self.now = datetime.datetime.utcnow()
        self.route_name = "green_leaf"
        self.external_route_name = urllib.quote("green leaf")
        route_data = {
            "id": self.route_id,
            "name": self.route_name,
            "userId": "user001",
            "emails": ["email1@gmail.com","email2@gmail.com"],
            "phoneNumbers": ["3603335346"]
        }
        models.Route(**route_data).put()

        slot_id = getUUID(IDTYPE.ACCESS_SLOT)
        access_slot_data = {
            "id": slot_id,
            "routeId": self.route_id,
            "active": True,
            "start": self.now,
            "end": self.now + datetime.timedelta(hours=2),
            "repeatInterval": 60 * 60 * 24,
            "cutoff": self.now + datetime.timedelta(days=3),
            "currStart": self.now,
            "currEnd": self.now + datetime.timedelta(hours=2)
        }
        models.AccessSlot(**access_slot_data).put()

        slot_id = getUUID(IDTYPE.ACCESS_SLOT)
        access_slot_data = {
            "id": slot_id,
            "routeId": self.route_id,
            "active": True,
            "start": self.now + datetime.timedelta(hours=24),
            "end": self.now + datetime.timedelta(hours=26),
            "repeatInterval": 60 * 60 * 24,
            "cutoff": self.now + datetime.timedelta(days=3),
            "currStart": self.now + datetime.timedelta(hours=24),
            "currEnd": self.now + datetime.timedelta(hours=26)
        }
        models.AccessSlot(**access_slot_data).put()
        self.endpoint = "/v1/route/"

    def test_basic(self):
        self.method = 'GET'
        self.endpoint += self.external_route_name
        self.send()
        response_expectation = view_models.Route.view_contract()
        response_expectation["slots"][0]["active"] = 'True'
        self.expect_resp_conforms(response_expectation)

    def test_invalid_route_id(self):
        self.method = 'GET'
        self.endpoint += self.INVALID_ID
        self.send()
        self.expect_resp_code(422)

if __name__ == '__main__':
    unittest.main()