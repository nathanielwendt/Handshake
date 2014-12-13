import json
from utils import BaseUtils

class Default(object):
    @staticmethod
    def view_contract():
        return {
            "status": "success"
        }

class User(object):
    @staticmethod
    def view_contract():
        return {
            "userId": "+",
            "name": "+",
            "email": "+",
            "emails": "+",
            "phoneNumbers": "+"
        }

    @staticmethod
    def form(user):
        return {
            "userId": user.get_id(),
            "name": user.name,
            "email": user.email,
            "emails": json.dumps(user.emails),
            "phoneNumbers": json.dumps(user.phoneNumbers)
        }

class AccessSlot(object):
    @staticmethod
    def create_contract():
        return {
            "start": "+",
            "end": "+",
            "repeatInterval": "+",
            "cutoff": "+",
        }

    @staticmethod
    def view_contract():
        view = AccessSlot.create_contract()
        view["slotId"] = "+"
        view["active"] = "+"
        return view

class Message(object):
    @staticmethod
    def view_contract():
        return {
            "id": "+",
            "clientUserId": "+",
            "isClient": "+",
            "routeId": "+",
            "message": "+",
        }

    @staticmethod
    def form(msg):
        return {
            "id": msg.get_id(),
            "clientUserId": msg.clientUserId,
            "isClient": msg.is_client_message(),
            "routeId": msg.routeId,
            "message": msg.body
        }

    @staticmethod
    def view_list_contract():
        return {
            "messages": [Message.view_contract()],
            "more": "+",
            "cursor": "*"
        }

    @staticmethod
    def form_list(messages, more, cursor):
        message_list = []
        for message in messages:
            message_list.append(Message.form(message))
        return {
            "messages": message_list,
            "more": more,
            "cursor": cursor.urlsafe()
        }


class Route(object):
    @staticmethod
    def view_contract():
        return {
            "id": "+",
            "userId": "+",
            "emails": ["+", "*"],
            "phoneNumbers": ["+", "*"],
            "slots": [AccessSlot.view_contract(), "*"]
        }

    @staticmethod
    def form(route, access_slot_list):
        slots = []
        for slot in access_slot_list:
            slots.append({
                "slotId": slot.get_id(),
                "start": BaseUtils.datetime_to_epoch(slot.start),
                "end": BaseUtils.datetime_to_epoch(slot.end),
                "repeatInterval": slot.repeatInterval,
                "cutoff": BaseUtils.datetime_to_epoch(slot.cutoff),
                "active": slot.active
            })

        return {
            "id": route.get_id(),
            "userId": route.userId,
            "emails": json.dumps(route.emails),
            "phoneNumbers": json.dumps(route.phoneNumbers),
            "slots": slots
        }

class RouteMember(object):
    @staticmethod
    def view_contract():
        return {
            "userId": "+",
            "memberId": "+"
        }

    @staticmethod
    def form(member):
        return {
            "userId": member.userId,
            "memberId": member.memberId
        }

    @staticmethod
    def view_list_contract():
        return {
            "members": [RouteMember.view_contract(), "*"]
        }

    @staticmethod
    def form_list(members):
        member_list = []
        for member in members:
            member_list.append(RouteMember.form(member))
        return {
            "members": member_list
        }