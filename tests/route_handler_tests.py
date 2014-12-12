import json
import urllib

import models
from test_utils import AppEngineTest, ConsistencyTest
import view_models
import datetime
from models import getUUID, IDTYPE
from utils import BaseUtils, NamingGenerator


class TestRouteCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteCreationHandler, self).setUp()
        self.endpoint = "/v1/route"
        self.now = datetime.datetime.utcnow()
        AppEngineTest.set_up_naming()

    def test_basic(self):
        self.method = 'POST'
        self.params = {
            "userId": "user001",
            "emails": json.dumps(["email12@gmail.com","email5@gmail.com"]),
            "phoneNumbers": json.dumps(["3533524434"]),
            "slots": json.dumps([
                {
                    "start": BaseUtils.datetime_to_epoch(self.now),
                    "end": BaseUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": BaseUtils.datetime_to_epoch(self.now)
                }
            ])
        }
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        route_id = self.response_data["id"]
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
                    "start": BaseUtils.datetime_to_epoch(self.now),
                    "end": BaseUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": BaseUtils.datetime_to_epoch(self.now)
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
                    "start": BaseUtils.datetime_to_epoch(self.now),
                    #"end": BaseUtils.datetime_to_epoch(self.now),
                    "repeatInterval": 1000,
                    "cutoff": BaseUtils.datetime_to_epoch(self.now)
                }
            ])
        }
        self.send()
        self.expect_resp_code(400)

class TestRouteHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteHandler, self).setUp()
        self.route_id = "green leaf"
        self.now = datetime.datetime.utcnow()
        self.external_route_name = urllib.quote("green leaf")
        route_data = {
            "id": self.route_id,
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
