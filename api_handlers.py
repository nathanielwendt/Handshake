import webapp2
import json
from handler_utils import APIBaseHandler
import models
import view_models
from handler_utils import getUUID, IDTYPE, Namer
from utils import APIUtils
import messenger
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from messenger import Email

class UserCreationHandler(APIBaseHandler):
    def post(self):
        """
        Creates a new user.

        :param name: name of the user
        :param email: email for user account purposes
        :param emails: emails made available for route creation
        :param phoneNumbers: phone numbers made available for route creation
        """
        contract = {
            "name": ["varchar", "+"],
            "email": ["email","+"],
            "emails": ["email_list","+"],
            "phoneNumbers": ["num_list","+"],
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        data = {
            "id": getUUID(IDTYPE.USER),
            "name": self.get_param("name"),
            "email": self.get_param("email"),
            "emails": json.loads(self.get_param("emails")),
            "phoneNumbers": json.loads(self.get_param("phoneNumbers"))
        }
        user = models.User(**data)
        user.put()

        self.set_response_view_model(view_models.User.view_contract())
        self.api_response = view_models.User.form(user)
        self.send_response()

class UserHandler(APIBaseHandler):
    def get(self, **kwargs):
        """
        Retrieves a user entry by id
        """
        user_id = kwargs["id"]
        user = models.User.get_by_id(user_id)
        if user is None:
            self.abort(422, "could not find user")

        self.set_response_view_model(view_models.User.view_contract())
        self.api_response = view_models.User.form(user)
        self.send_response()


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

        route_id = getUUID(IDTYPE.ROUTE)
        route_data = {
            "id": route_id,
            "name": Namer.get_next(),
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
                "start": APIUtils.epoch_to_datetime(slot["start"]),
                "end": APIUtils.epoch_to_datetime(slot["end"]),
                "repeatInterval": slot["repeatInterval"],
                "cutoff": APIUtils.epoch_to_datetime(slot["cutoff"]),
                "currStart": APIUtils.epoch_to_datetime(slot["start"]),
                "currEnd": APIUtils.epoch_to_datetime(slot["end"])
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
        Retrieves a route by id
        """
        name_raw = kwargs["name"]
        name = APIUtils.name_to_backend_format(name_raw)
        route = models.Route.query(models.Route.name == name).get()

        if route is None:
            self.abort(422, "could not find route by that id")

        access_slots = models.AccessSlot.query(models.AccessSlot.routeId == route.get_id())
        self.set_response_view_model(view_models.Route.view_contract())
        self.api_response = view_models.Route.form(route, access_slots)
        self.send_response()


class MessageNativeCreationHandler(APIBaseHandler):
    def post(self):
        contract = {
            "userId": ["id","+"],
            "routeName": ["varchar","+"],
            "body": ["varchar","+"]
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        message_data = {
            "id": getUUID(IDTYPE.MESSAGE),
            "senderId": self.get_param("userId"),
            "routeName": self.get_param("routeName"),
            "body": self.get_param("body")
        }
        message = models.Message(**message_data)
        message.put()


def create_client_message(source, sender_user, message_body, route_name):
    if sender_user is None:
        raise CreateMessageException("could not find a user associated with number")

    route = models.Route.query(models.Route.name == route_name)

    message_data = {
        "routeName": route_name,
        "source": source,
        "sourceType": messenger.SOURCE_TYPE_SMS,
        "senderUserId": sender_user.get_id(),
        "receiverUserId": route.userId,
        "clientUserId": sender_user.get_id(),
        "body": message_body
    }
    models.Message(**message_data).put()

    for outgoing_email in route.emails:
        messenger.send_message(outgoing_email, messenger.SOURCE_TYPE_EMAIL, message_body)

    for outgoing_phone_number in route.phoneNumbers:
        messenger.send_message(outgoing_phone_number, messenger.SOURCE_TYPE_SMS, message_body)

def create_owner_message(source, sender_user, message_body, client_id):
    if sender_user is None:
        raise CreateMessageException("could not find a user associated with number")
    prev_messages, next_cursor, more = models.Message.query(models.Message.senderUserId == client_id)\
                                                .filter(models.Message.receiverUserId == sender_user.get_id())\
                                                .order(-models.Message.created)\
                                                .fetch_page(1)

    if prev_messages.get(0) is None:
        raise CreateMessageException("could not find message to respond to")

    last_message = prev_messages.get(0) #only fetched one, but need to get it

    message_data = {
        "routeName": last_message.routeName,
        "source": source,
        "sourceType": messenger.SOURCE_TYPE_SMS,
        "senderUserId": sender_user.get_id(),
        "receiverUserId": last_message.senderUserId,
        "clientUserId": last_message.senderUserId,
        "body": message_body
    }
    models.Message(**message_data).put()

    messenger.send_message(last_message.source, last_message.sourceType, message_body)


class MessageSMSCreationHandler(APIBaseHandler):
    def post(self):
        contract = {
            "message": "+",
            "phoneNumber": "+"
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        message_raw = self.get_param("message").strip()
        phone_number = self.get_param("phoneNumber")
        if APIUtils.is_client_message(message_raw):
            route_name, body = APIUtils.split_client_message(message_raw)
            sender_user = models.User.query(models.User.phoneNumbers == phone_number)
            try:
                create_client_message(phone_number, sender_user, body, route_name)
            except CreateMessageException, e:
                self.abort(422, e)

        elif APIUtils.is_owner_message(message_raw):
            client_id, body = APIUtils.split_owner_message(message_raw)
            sender_user = models.User.query(models.User.phoneNumbers == phone_number)
            try:
                create_owner_message(phone_number, sender_user, body, client_id)
            except CreateMessageException, e:
                self.abort(422, e)
        else:
            self.abort(403, "message recipient could not be determined")


class MessageEmailCreationHandler(InboundMailHandler, APIBaseHandler):
    def receive(self, mail_message):
        email_sender = APIUtils.get_email_from_sender_field(mail_message.sender)
        email_body = mail_message.body

        client_id = mail_message.headers.get(Email.HEADER_EMBED_FIELD)
        # client message
        if client_id is None or client_id == "":
            route_name = mail_message.subject.strip().lower()
            sender_user = models.User.query(models.User.emails == email_sender)
            try:
                create_client_message(email_sender, sender_user, email_body, route_name)
            except CreateMessageException, e:
                self.abort(422, e)
        # owner message
        else:
            sender_user = models.User.query(models.User.emails == email_sender)
            try:
                create_owner_message(email_sender, sender_user, email_body, client_id)
            except CreateMessageException, e:
                self.abort(422, e)


class MessageNativeCreationHandler(APIBaseHandler):
    def post(self, **kwargs):
        contract = {
            "senderUserId": ["id","+"],
            "routeName": ["varchar","+"]
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        try:
            create_client_message(email_sender, sender_user, email_body, route_name)
        except CreateMessageException, e:
            self.abort(422, e)


class CreateMessageException(BaseException):
    pass
