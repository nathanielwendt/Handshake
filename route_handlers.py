import json
from handler_utils import APIBaseHandler, ValidatorException
import models
import view_models
from models import getUUID, IDTYPE
from utils import BaseUtils
import urllib
from utils import NamingGenerator
from google.appengine.ext import ndb

class RouteCreationHandler(APIBaseHandler):
    def post(self):
        """
        Creates a route with 1 or more communication channels attached

        :param userId: Id for user that is creating the route
        :param emails: Emails attached to the route
        :param phoneNumbers: Phone numbers attached to the route (10 digit, not characters other than numbers)
        :param slots: Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" }
        :return:
        """
        contract = {
            "userId": ["id", "+"],
            "emails": ["email_list", "*"],
            "phoneNumbers": ["phone_list", "*"],
            "slots": ["slot_list","+"],
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        user_id = self.get_param("userId")
        emails = self.get_param("emails")
        phone_numbers = self.get_param("phoneNumbers")

        if emails is None and phone_numbers is None:
            self.abort(422, "need at least one phone number or email communication channel")

        route_id = NamingGenerator.get_route_id()
        route = models.Route.get_by_id(route_id)
        route.userId = user_id
        route.emails = json.loads(emails)
        route.phoneNumbers = json.loads(phone_numbers)
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
        route_id = kwargs["id"]
        route = models.Route.get_by_id(route_id)
        if route is None:
            self.abort(422, "could not find route by that id")

        access_slots = models.AccessSlot.query(models.AccessSlot.routeId == route.get_id())
        self.set_response_view_model(view_models.Route.view_contract())
        self.api_response = view_models.Route.form(route, access_slots)
        self.send_response()

    def put(self, **kwargs):
        """
        Updates route parameters.
        Note: updating slots will wipe old slots and replace with new set.

        :param emails: Emails attached to the route
        :param phoneNumbers: Numbers attached to the route
        :param slots: Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" }
        """
        contract = {
            "emails": ["email_list", "*"],
            "phoneNumbers": ["phone_list", "*"],
            "slots": ["slot_list", "*"],
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        route_id = urllib.unquote(kwargs["id"])
        route = models.Route.get_by_id(route_id)
        if route is None:
            self.abort(422, "could not find route by that id")

        emails = self.get_param("emails")
        phone_numbers = self.get_param("phoneNumbers")
        slots = self.get_param("slots")

        if emails is not None:
            route.emails = json.loads(emails)

        if phone_numbers is not None:
            route.phoneNumbers = json.loads(phone_numbers)

        #populate slot list for response, will delete and replace list if
        #request has slot params
        access_slot_list = []
        old_slots = models.AccessSlot.query(models.AccessSlot.routeId == route_id)
        for old_slot in old_slots:
            access_slot_list.append(old_slot)

        if slots is not None:
            #delete old slots
            list_of_keys = ndb.put_multi(access_slot_list)
            ndb.delete_multi(list_of_keys)

            #create new slots
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

class RouteMemberListHandler(APIBaseHandler):
    def get(self, **kwargs):
        """
        Retrieves a list of members belonging to a specific route

        :param userId: id of user that is requesting the list, only the route owner is allowed here
        """
        contract = {
            "userId": ["id", "+"]
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        user_id = self.get_param("userId")
        route_id = kwargs["id"]
        route = models.Route.get_by_id(route_id)
        if route is None:
            self.abort(422, "could not find route")

        if user_id != route.userId:
            self.abort(422, "non owner of route is not allowed to request members")

        members = route.get_members()
        self.set_response_view_model(view_models.RouteMember.view_list_contract())
        self.api_response = view_models.RouteMember.form_list(members)
        self.send_response()

class RouteMemberCreationHandler(APIBaseHandler):
    def post(self, **kwargs):
        """
        Joins a user to a specific route

        :param userId: id of user to join route
        """
        contract = {
            "userId": ["id", "+"]
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        user_id = self.get_param("userId")
        route_id = kwargs["id"]
        route = models.Route.get_by_id(route_id)
        if route is None:
            self.abort(422, "could not find route to join")

        existing_member = models.RouteMember.get_user_entry(route, user_id)
        if existing_member is not None:
            self.abort(422, "user has already joined route")

        if route.userId == user_id:
            self.abort(422, "route owner cannot join own route")

        member = NamingGenerator.generate_route_member(route, user_id)

        self.set_response_view_model(view_models.RouteMember.view_contract())
        self.api_response = view_models.RouteMember.form(member)
        self.send_response()

class RouteListHandler(APIBaseHandler):
    def get(self):
        """
        Retrieves all routes for a given user (both created and joined routes)

        :param userId: Id for user for which to return routes
        """
        contract = {
            "userId": ["id", "+"]
        }

        user_id = self.get_param("userId")
        user = models.User.get_by_id(user_id)
        if user is None:
            self.abort(422, "User does not exist")

        joined_route_ids = models.RouteMember.get_user_membership(user_id)
        created_routes = models.Route.query(models.Route.userId == user_id)

        all_routes = []
        for joined_route_id in joined_route_ids:
            route = models.Route.get_by_id(joined_route_id)
            all_routes.append(route)

        for created_route in created_routes:
            all_routes.append(created_route)

        self.set_response_view_model(view_models.Route.view_list_contract())
        self.api_response = view_models.Route.form_list(all_routes)
        self.send_response()
