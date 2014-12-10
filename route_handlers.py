import json
from handler_utils import APIBaseHandler
import models
import view_models
from models import getUUID, IDTYPE
from utils import BaseUtils
import urllib
from utils import NamingGenerator

class RouteCreationHandler(APIBaseHandler):
    def post(self):
        """
        Creates a route with 1 or more communication channels attached
        :param userId: Id for user that is creating the route
        :param emails: Emails attached to the route
        :param phoneNumbers: Numbers attached to the route
        :param slots: Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" }
        :return:
        """
        contract = {
            "userId": ["id", "+"],
            "emails": ["email_list", "*"],
            "phoneNumbers": ["num_list", "*"],
            "slots": ["slot_list","+"],
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        user_id = self.get_param("userId")
        emails = self.get_param("emails")
        phone_numbers = self.get_param("phoneNumbers")

        if emails is None and phone_numbers is None:
            self.abort(422, "need at least one phone number or email communication channel")


        route_id = NamingGenerator.get_route_id()
        route_data = {
            "id": route_id,
            "userId": user_id,
            "emails": json.loads(emails),
            "phoneNumbers": json.loads(phone_numbers)
        }
        route = models.Route(**route_data)
        route.put()


        slots = json.loads(self.get_param("slots"))

        access_slot_list = []
        for slot in slots:
            data = {
                "id": getUUID(IDTYPE.ACCESS_SLOT),
                "routeId": route_id,
                "start": BaseUtils.epoch_to_datetime(slot["start"]),
                "end": BaseUtils.epoch_to_datetime(slot["end"]),
                "repeatInterval": slot["repeatInterval"],
                "cutoff": BaseUtils.epoch_to_datetime(slot["cutoff"]),
                "currStart": BaseUtils.epoch_to_datetime(slot["start"]),
                "currEnd": BaseUtils.epoch_to_datetime(slot["end"])
            }
            next_slot = models.AccessSlot(**data)
            next_slot.put()
            access_slot_list.append(next_slot)

        self.set_response_view_model(view_models.Route.view_contract())
        self.api_response = view_models.Route.form(route, access_slot_list)
        self.send_response()


class RouteHandler(APIBaseHandler):
    def get(self, **kwargs):
        """
        Retrieves a route by route name
        """
        name = urllib.unquote(kwargs["name"])
        route = models.Route.get_by_name(name)
        if route is None:
            self.abort(422, "could not find route by that id")

        access_slots = models.AccessSlot.query(models.AccessSlot.routeId == route.get_id())
        self.set_response_view_model(view_models.Route.view_contract())
        self.api_response = view_models.Route.form(route, access_slots)
        self.send_response()

from google.appengine.ext import ndb

class TestHandler(APIBaseHandler):
    def get(self):
        entry = models.Test.get_by_id("123")
        if not entry:
            entry = models.Test(id="123")
            entry.num = 0
        else:
            entry.num += 1

        entry.put()
        self.response.out.write(entry.num)