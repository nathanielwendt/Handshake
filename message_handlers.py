from handler_utils import APIBaseHandler, ValidatorException
import models
from utils import MessageUtils, NamingGenerator, UtilsException
import messenger
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from messenger import Email, MessageException
import view_models
from google.appengine.datastore.datastore_query import Cursor


def create_client_message(source, source_type, sender_user_id, message_body, route_id):
    route = models.Route.get_by_id(route_id)
    if route is None:
        raise MessageException("could not find route associated with id")

    if not route.is_now_valid():
        raise MessageException("route is closed")

    message_data = {
        "routeId": route_id,
        "source": source,
        "sourceType": source_type,
        "senderUserId": sender_user_id,
        "receiverUserId": route.userId,
        "clientUserId": sender_user_id ,
        "body": message_body
    }
    message = models.Message(**message_data)
    message.put()

    for outgoing_email in route.emails:
        messenger.send_message(outgoing_email, messenger.SOURCE_TYPE_EMAIL, message_body)

    for outgoing_phone_number in route.phoneNumbers:
        messenger.send_message(outgoing_phone_number, messenger.SOURCE_TYPE_SMS, message_body)

    return message

def create_owner_message(source, source_type, sender_user_id, message_body, client_id, route_id):
    prev_messages, next_cursor, more = models.Message.query(models.Message.routeId == route_id)\
                                                .filter(models.Message.clientUserId == client_id)\
                                                .order(-models.Message.created)\
                                                .fetch_page(1)

    if prev_messages == []:
        raise MessageException("could not find message to respond to")
    last_message = prev_messages[0]

    message_data = {
        "routeId": last_message.routeId,
        "source": source,
        "sourceType": source_type,
        "senderUserId": sender_user_id,
        "receiverUserId": last_message.senderUserId,
        "clientUserId": last_message.senderUserId,
        "body": message_body
    }
    message = models.Message(**message_data)
    message.put()
    messenger.send_message(last_message.source, last_message.sourceType, message_body)

    return message


class MessageSMSCreationHandler(APIBaseHandler):
    def post(self, **kwargs):
        """
        Creates a message from an sms message

        :param Body: message body, route name should be included in message
        :param From: number from which the message originates
        """
        contract = {
            "Body": ["varchar","+"],
            "From": ["phone","+"]
        }
        print self.request.params
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        message_raw = self.get_param("Body").strip()
        phone_number = self.get_param("From")
        source_type = messenger.SOURCE_TYPE_SMS

        if MessageUtils.is_client_message(message_raw):
            print "message senindg client"
            try:
                route_name, body = MessageUtils.split_client_message(message_raw)
            except UtilsException, e:
                self.abort(422, e)
            sender_user = models.User.query(models.User.phoneNumbers == phone_number)
            if sender_user is None:
                self.abort(422, "Could not find a user associated with that number")
            try:
                create_client_message(phone_number, source_type, sender_user.get_id(),
                                      body, route_name)
            except MessageException, e:
                self.abort(422, e)

        elif MessageUtils.is_owner_message(message_raw):
            print "message sending owner"
            try:
                client_id, route_id, body = MessageUtils.split_owner_message(message_raw)
            except UtilsException, e:
                self.abort(422, e)
            sender_user = models.User.query(models.User.phoneNumbers == phone_number)
            try:
                create_owner_message(phone_number, source_type, sender_user.get_id(),
                                     body, client_id, route_id)
            except MessageException, e:
                self.abort(422, e)
        else:
            self.abort(403, "message recipient could not be determined")

        self.set_default_success_response()
        self.send_response()


class MessageEmailCreationHandler(InboundMailHandler, APIBaseHandler):
    def receive(self, mail_message):
        print "receive email"
        try:
            email_sender = MessageUtils.get_email_from_sender_field(mail_message.sender)
        except UtilsException, e:
            self.abort(422, e)

        #TODO: route_id lowercase and strip!

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


class MessageNativeCreationHandler(APIBaseHandler):
    def post(self):
        """
        Creates a message from the native app.

        :param senderUserId: the id of the sending user
        :param receiverUserId: the id of the receiving user
        :param routeId: the id of the route along which to send the message
        :param message: message body
        """
        contract = {
            "senderUserId": ["id","+"],
            "receiverUserId": ["id", "*"],
            "routeId": ["varchar","+"],
            "message": ["varchar","+"]
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        sender_user_id = self.get_param("senderUserId")
        receiver_user_id = self.get_param("receiverUserId")
        message_body = self.get_param("message")
        route_id = self.get_param("routeId").lower().strip()

        sender_user = models.User.get_by_id(sender_user_id)
        if sender_user is None:
            self.abort(422, "could not find user by that username")

        source_type = messenger.SOURCE_TYPE_NATIVE
        source = messenger.SOURCE_VALUE_NATIVE

        message = None
        #message client -> owner
        if receiver_user_id is None:
            try:
                message = create_client_message(source, source_type, sender_user_id,
                                  message_body, route_id)
            except MessageException, e:
                self.abort(422, e)
        #message owner -> client
        else:
            try:
                message = create_owner_message(source, source_type, sender_user_id,
                                     message_body,receiver_user_id, route_id)
            except MessageException, e:
                self.abort(422, e)

        self.set_response_view_model(view_models.Message.view_contract())
        self.api_response = view_models.Message.form(message)
        self.send_response()


class MessageListHandler(APIBaseHandler):
    def get(self, **kwargs):
        """
        Retrieves a list of messages as a back and forth between a route owner and single client

        :param cursor: query cursor to resume querying position
        """
        contract = {
            "cursor": ["id", "*"]
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        route_id = kwargs["route_id"]
        client_id = kwargs["user_id"]
        num_to_fetch = kwargs["n"]

        curr_cursor = Cursor(urlsafe=self.get_param('cursor'))
        messages, cursor, more = models.Message.query(models.Message.routeId == route_id)\
                                               .filter(models.Message.clientUserId == client_id)\
                                                .fetch_page(num_to_fetch, start_cursor=curr_cursor)

        self.set_response_view_model(view_models.Message.view_list_contract())
        self.api_response = view_models.Message.form_list(messages, more, cursor)
        self.send_response()



