from handler_utils import APIBaseHandler
import models
from handler_utils import getUUID, IDTYPE, Namer
from utils import APIUtils
import messenger
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from messenger import Email, MessageException


def create_client_message(source, sender_user, message_body, route_name):
    if sender_user is None:
        raise MessageException("could not find a user associated with number")

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
        raise MessageException("could not find a user associated with number")
    prev_messages, next_cursor, more = models.Message.query(models.Message.senderUserId == client_id)\
                                                .filter(models.Message.receiverUserId == sender_user.get_id())\
                                                .order(-models.Message.created)\
                                                .fetch_page(1)

    if prev_messages.get(0) is None:
        raise MessageException("could not find message to respond to")

    last_message = prev_messages.get() #only fetched one, but need to get it

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
            except MessageException, e:
                self.abort(422, e)

        elif APIUtils.is_owner_message(message_raw):
            client_id, body = APIUtils.split_owner_message(message_raw)
            sender_user = models.User.query(models.User.phoneNumbers == phone_number)
            try:
                create_owner_message(phone_number, sender_user, body, client_id)
            except MessageException, e:
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
            except MessageException, e:
                self.abort(422, e)
        # owner message
        else:
            sender_user = models.User.query(models.User.emails == email_sender)
            try:
                create_owner_message(email_sender, sender_user, email_body, client_id)
            except MessageException, e:
                self.abort(422, e)


# Can only create client message from the native app
class MessageNativeCreationHandler(APIBaseHandler):
    def post(self, **kwargs):
        contract = {
            "senderUserId": ["id","+"],
            "routeName": ["varchar","+"],
            "message": ["varchar","+"]
        }
        try:
            self.check_params_conform(contract)
        except:
            return

        sender_user_id = self.get_param("senderUserId")
        message_body = self.get_param("message")
        route_name = self.get_param("routeName")
        sender_user = models.User.get_by_id(sender_user_id)
        if sender_user is None:
            self.abort(422, "could not find user by that username")

        try:
            create_client_message(messenger.SOURCE_VALUE_NATIVE, sender_user, message_body, route_name)
        except MessageException, e:
            self.abort(422, e)

