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
        self.route_id = "greenleaf"
        self.now = datetime.datetime.utcnow()
        self.external_route_name = "greenleaf"
        route_data = {
            "id": self.route_id,
            "userId": "user001",
            "emails": ["email1@gmail.com","email2@gmail.com"],
            "phoneNumbers": ["3603335346"],
            "displayName": "GreenLeaf"
        }
        models.Route(**route_data).put()

        self.slot1_id = getUUID(IDTYPE.ACCESS_SLOT)
        access_slot_data = {
            "id": self.slot1_id,
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

        self.slot2_id = getUUID(IDTYPE.ACCESS_SLOT)
        access_slot_data = {
            "id": self.slot2_id,
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

    def test_get_basic(self):
        self.method = 'GET'
        self.endpoint += self.external_route_name
        self.send()
        response_expectation = view_models.Route.view_contract()
        response_expectation["slots"][0]["active"] = 'True'
        self.expect_resp_conforms(response_expectation)

    def test_get_route_case_sensitivity(self):
        self.method = 'GET'
        self.endpoint += "GREEnleaF"
        self.send()
        response_expectation = view_models.Route.view_contract()
        response_expectation["slots"][0]["active"] = 'True'
        self.expect_resp_conforms(response_expectation)

    def test_get_invalid_route_id(self):
        self.method = 'GET'
        self.endpoint += self.INVALID_ID
        self.send()
        self.expect_resp_code(422)

    def test_put_invalid_route_id(self):
        self.method = 'PUT'
        self.endpoint += self.INVALID_ID
        self.send()
        self.expect_resp_code(422)

    def test_put_emails(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_emails = ["email1@gmail.com","email2@gmail.com"]
        new_emails = ["kent@gmail.com"]

        self.params["emails"] = json.dumps(new_emails)
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        self.expect_resp_param("emails", json.dumps(new_emails))

    def test_put_emails_malformed_email(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_emails = ["email1@gmail.com","email2@gmail.com"]
        new_emails = ["k@@ent@gmail.com"]

        self.params["emails"] = json.dumps(new_emails)
        self.send()
        self.expect_resp_code(400)

    def test_put_emails_empty(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_emails = ["email1@gmail.com","email2@gmail.com"]
        new_emails = []

        self.params["emails"] = json.dumps(new_emails)
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        self.expect_resp_param("emails", json.dumps(new_emails))

    def test_put_phone_numbers(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_numbers = ["3603335346"]
        new_numbers = ["3503333352","1234253678"]

        self.params["phoneNumbers"] = json.dumps(new_numbers)
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        self.expect_resp_param("phoneNumbers", json.dumps(new_numbers))

    def test_put_phone_numbers_empty(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_numbers = ["3603335346"]
        new_numbers = []

        self.params["phoneNumbers"] = json.dumps(new_numbers)
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        self.expect_resp_param("phoneNumbers", json.dumps(new_numbers))

    def test_put_phone_numbers_malformed_number(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        prev_numbers = ["3603335346"]
        new_numbers = ["390395303","30939---"]

        self.params["phoneNumbers"] = json.dumps(new_numbers)
        self.send()
        self.expect_resp_code(400)

    def test_put_slots(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        self.now = datetime.datetime.utcnow()
        self.params["slots"] = json.dumps([{
                "start": BaseUtils.datetime_to_epoch(self.now),
                "end": BaseUtils.datetime_to_epoch(self.now),
                "repeatInterval": 999,
                "cutoff": BaseUtils.datetime_to_epoch(self.now)
            }
        ])
        #ensure that old slots exist
        slot1 = models.AccessSlot.get_by_id(self.slot1_id)
        slot2 = models.AccessSlot.get_by_id(self.slot2_id)
        self.assertIsNotNone(slot1)
        self.assertIsNotNone(slot2)

        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_contract())
        self.assertEqual(len(self.response_data["slots"]), 1) #old slots are wiped
        new_slot = self.response_data["slots"][0]
        self.assertEqual(int(new_slot["repeatInterval"]), 999) #new slots reflected slot inserted above


    def test_put_slots_empty(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        self.now = datetime.datetime.utcnow()
        self.params["slots"] = json.dumps([])

        #check that old slots exist
        slot1 = models.AccessSlot.get_by_id(self.slot1_id)
        slot2 = models.AccessSlot.get_by_id(self.slot2_id)
        self.assertIsNotNone(slot1)
        self.assertIsNotNone(slot2)

        self.send()
        self.expect_resp_code(200)
        self.assertEqual(len(self.response_data["slots"]), 0) #old slots are wiped

    def test_put_slots_malformed_slots(self):
        self.method = 'PUT'
        self.endpoint += self.external_route_name
        self.now = datetime.datetime.utcnow()
        self.params["slots"] = json.dumps([{
                "start": BaseUtils.datetime_to_epoch(self.now),
                #"end": BaseUtils.datetime_to_epoch(self.now),
                "repeatInterval": 999,
                "cutoff": BaseUtils.datetime_to_epoch(self.now)
            }
        ])
        #ensure that old slots exist
        slot1 = models.AccessSlot.get_by_id(self.slot1_id)
        slot2 = models.AccessSlot.get_by_id(self.slot2_id)
        self.assertIsNotNone(slot1)
        self.assertIsNotNone(slot2)

        self.send()
        self.expect_resp_code(400)


class TestRouteMemberHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteMemberHandler, self).setUp()
        self.endpoint = "/v1/route/"

        self.user = models.User(id="user001", name="John Doe")
        self.user.put()

        self.member_user = models.User(id="user002", name="Jeff Coolio")
        self.member_user.put()

        items = ["dog","cat","duck","platypus"]
        models.Naming(id=NamingGenerator.ANIM_KEY, items=items).put()

        self.route = models.Route(id="cavalierbro", userId="user001")
        self.route.put()

    def test_basic_valid(self):
        self.method = "POST"
        self.endpoint += self.route.get_id() + "/member"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.RouteMember.view_contract())
        member_id = self.response_data["memberId"]

        member = models.RouteMember.get_entry(self.route, member_id)
        self.assertIsNotNone(member)
        self.assertEqual("dog", member.memberId)
        self.assertEqual("user002", member.userId)

    def test_invalid_route(self):
        self.method = "POST"
        self.endpoint += self.INVALID_ID + "/member"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_owner_joins_own_route(self):
        self.method = "POST"
        self.endpoint += self.route.get_id() + "/member"
        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(422)


class TestRouteMemberListHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteMemberListHandler, self).setUp()
        self.endpoint = "/v1/route/"
        self.route = models.Route(id="cavalierbro", userId="user001")
        self.route.put()
        items = ["dog","cat","duck","platypus"]
        models.Naming(id=NamingGenerator.ANIM_KEY, items=items).put()

    def test_basic_empty(self):
        self.endpoint += self.route.get_id() + "/member/list"
        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(200)
        self.assertEqual([], self.response_data["members"])

    def test_basic(self):
        models.User(id="user002", name="Jeff Perkins").put()
        models.User(id="user003", name="Kaleb Bosh").put()
        models.User(id="user004", name="Kevin Ko").put()
        NamingGenerator.generate_route_member(self.route, "user002")
        NamingGenerator.generate_route_member(self.route, "user003")
        NamingGenerator.generate_route_member(self.route, "user004")

        self.endpoint += self.route.get_id() + "/member/list"
        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.RouteMember.view_list_contract())

        members = self.response_data["members"]
        self.assertIn({"userId": "user002", "memberId": "dog"}, members)
        self.assertIn({"userId": "user003", "memberId": "cat"}, members)
        self.assertIn({"userId": "user004", "memberId": "duck"}, members)

    def test_invalid_route_id(self):
        self.endpoint += self.INVALID_ID + "/member/list"
        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_non_owner_query(self):
        self.endpoint += self.route.get_id() + "/member/list"
        self.params["userId"] = self.INVALID_ID
        self.send()
        self.expect_resp_code(422)


class TestRouteMemberCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteMemberCreationHandler, self).setUp()
        self.endpoint = "/v1/route/"

        self.owner_user = models.User(id="user001", name="Tim Ricman")
        self.owner_user.put()
        self.client_user = models.User(id="user002", name="Rickity Cricket")
        self.client_user.put()

        self.route = models.Route(id="cavalierbro", userId="user001")
        self.route.put()
        items = ["dog","cat","duck","platypus"]
        models.Naming(id=NamingGenerator.ANIM_KEY, items=items).put()

    def test_basic(self):
        self.method = 'POST'
        self.endpoint += self.route.get_id() + "/member"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.RouteMember.view_contract())
        self.expect_resp_param("userId", "user002")
        self.expect_resp_param("memberId", "dog")

    def test_invalid_route(self):
        self.method = 'POST'
        self.endpoint += self.INVALID_ID + "/member"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_already_joined_route(self):
        self.method = 'POST'
        self.endpoint += self.route.get_id() + "/member"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(200)
        self.send()
        self.expect_resp_code(422)

    def test_invalid_join_own_route(self):
        self.method = 'POST'
        self.endpoint += self.route.get_id() + "/member"
        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(422)

class TestRouteListHandler(AppEngineTest):
    def setUp(self):
        super(TestRouteListHandler, self).setUp()
        self.endpoint = "/v1/route/list"
        self.user = models.User(id="user001", name="Tim Ricman")
        self.user.put()
        items = ["dog","cat","duck","platypus"]
        models.Naming(id=NamingGenerator.ANIM_KEY, items=items).put()

    def test_basic(self):
        self.method = "GET"
        models.Route(id="cavalierbro", userId="user001", displayName="CavalierBro").put()
        models.Route(id="chiefdog", userId="user001", displayName="ChiefDog").put()
        route1 = models.Route(id="plainjane", userId="user002", displayName="PlainJane")
        route1.put()

        NamingGenerator.generate_route_member(route1, "user001")

        self.params["userId"] = "user001"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Route.view_list_contract())
        routes = set()
        routes.add(self.response_data["routes"][0]["displayName"])
        routes.add(self.response_data["routes"][1]["displayName"])
        routes.add(self.response_data["routes"][2]["displayName"])
        self.assertEqual({"PlainJane", "CavalierBro", "ChiefDog"}, routes)

    def test_invalid_user(self):
        self.method = "GET"
        self.params["userId"] = "user002"
        self.send()
        self.expect_resp_code(422)