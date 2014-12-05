import json
from utils import APIUtils

class Default(object):
    view_contract = {
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
            "mesageId": "+",
            "senderId": "+",
            "routeName": "+",
            "message": "+"
        }

    @staticmethod
    def form(message):
        return {
            "messageId": message.get_id(),
            "userId": message.userId,
            "routeName": message.routeName,
            "message": message.body
        }


class Route(object):
    @staticmethod
    def view_contract():
        return {
            "name": "+",
            "userId": "+",
            "emails": ["+"],
            "phoneNumbers": ["+"],
            "slots": [AccessSlot.view_contract()]
        }

    @staticmethod
    def form(route, access_slot_list):
        slots = []
        for slot in access_slot_list:
            slots.append({
                "slotId": slot.get_id(),
                "start": APIUtils.datetime_to_epoch(slot.start),
                "end": APIUtils.datetime_to_epoch(slot.end),
                "repeatInterval": slot.repeatInterval,
                "cutoff": APIUtils.datetime_to_epoch(slot.cutoff),
                "active": slot.active
            })

        return {
            "name": route.name,
            "userId": route.userId,
            "emails": json.dumps(route.emails),
            "phoneNumbers": json.dumps(route.phoneNumbers),
            "slots": slots
        }