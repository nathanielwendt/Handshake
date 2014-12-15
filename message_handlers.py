from handler_utils import APIBaseHandler, ValidatorException
import models
from utils import MessageUtils, NamingGenerator, UtilsException
import messenger
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from messenger import Email, MessageException
import view_models
from google.appengine.datastore.datastore_query import Cursor
import json

#TODO: check that user is a member before sending a message along a route

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

    route_member = models.RouteMember.get_user_entry(route, sender_user_id)
    for outgoing_email in route.emails:
        header = sender_user_id
        subject = "HandshakeMessage: " + route_member.memberId + "@" + \
                  route_member.routeDisplayId + " " + \
                  "[" + route_member.userDisplayName + "]" "\n"
        messenger.Email.send(outgoing_email, message_body, subject, header)

    for outgoing_phone_number in route.phoneNumbers:
        message_sms = route_member.memberId + "@" + route_member.routeDisplayId + " " +\
              route_member.userDisplayName + "\n" + message_body
        messenger.SMS.send(outgoing_phone_number, message_sms)

    receiver_user = models.User.get_by_id(route.userId)
    message_json = json.dumps(view_models.Message.form(message))
    messenger.GCM.send(receiver_user.pushRegKey, message_json)

    return message

def create_owner_message(source, source_type, sender_user_id, message_body, client_id, route_id):
    prev_messages, next_cursor, more = models.Message.query(models.Message.routeId == route_id)\
                                                .filter(models.Message.senderUserId == client_id)\
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

    route = models.Route.get_by_id(route_id)
    if route is None:
        raise MessageException("could not find route for message")

    if last_message.sourceType == messenger.SOURCE_TYPE_EMAIL:
        header = sender_user_id
        subject = "HandshakeMessage: " + route.displayName
        messenger.Email.send(last_message.source, message_body, subject, header)
    elif last_message.sourceType == messenger.SOURCE_TYPE_SMS:
        message_sms = "#" + route.displayName + "\n" + message_body
        messenger.SMS.send(last_message.source, message_sms)
    elif last_message.sourceType == messenger.SOURCE_TYPE_NATIVE:
        message_json = json.dumps(view_models.Message.form(message))
        messenger.GCM.send(last_message.source, message_json)
    else:
        raise MessageException("previous message has an invalid source type")

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
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        message_raw = self.get_param("Body").strip()
        phone_number = self.get_param("From")
        source_type = messenger.SOURCE_TYPE_SMS

        if len(phone_number) == 12:
            phone_number = phone_number[2:]

        sender_user = models.User.query(models.User.phoneNumbers == phone_number).get()
        if sender_user is None:
            print "no user with id"
            self.abort(422, "Could not find a user associated with that number")

        if MessageUtils.is_client_message(message_raw):
            print "client msg"
            try:
                route_id, body = MessageUtils.split_client_message(message_raw)
            except UtilsException, e:
                print e
                self.abort(422, e)
            try:
                create_client_message(phone_number, messenger.SOURCE_TYPE_SMS,
                                      sender_user.get_id(), body, route_id)
            except MessageException, e:
                print e
                self.abort(422, e)

        elif MessageUtils.is_owner_message(message_raw):
            print "owner msg"
            try:
                member_id, route_id, body = MessageUtils.split_owner_message(message_raw)
                #Todo fix this redundancy as create_owner_message also queries for the route
                route = models.Route.get_by_id(route_id)
                client_id = models.RouteMember.get_user_id(route, member_id)
            except UtilsException, e:
                self.abort(422, e)
            try:
                create_owner_message(phone_number, messenger.SOURCE_TYPE_SMS,
                                     sender_user.get_id(), body, client_id, route_id)
            except MessageException, e:
                self.abort(422, e)
        else:
            self.abort(422, "message recipient could not be determined")

        self.set_default_success_response()
        self.send_response()


class MessageEmailCreationHandler(InboundMailHandler, APIBaseHandler):
    def receive(self, mail_message):
        pass
        try:
             email_sender = MessageUtils.get_email_from_sender_field(mail_message.sender)
        except UtilsException, e:
             self.abort(200, e)
        #email_sender = mail_message.sender
        print email_sender

        #client_id = MessageUtils.get_header_from_message(mail_message.original)
        html_bodies = mail_message.bodies('text/html')
        for content_type, body in html_bodies:
            email_body = MessageUtils.strip_html(body.decode())

        print email_body

        sender_user = models.User.query(models.User.emails == email_sender).get()
        if sender_user is None:
            print "sender user is none"
            self.abort(200, "Could not find user from sender")

        # client message
        if MessageUtils.is_client_message(mail_message.subject):
            #add space to format as client message
            print mail_message.subject
            route_id = MessageUtils.split_client_message(mail_message.subject + " ")[0]
            print route_id
            try:
                create_client_message(email_sender, messenger.SOURCE_TYPE_EMAIL,
                                      sender_user.get_id(),email_body,route_id)
            except MessageException, e:
                self.abort(200, e)
        # owner message
        elif MessageUtils.is_owner_message(mail_message.subject):
            #terribly inefficient to do all of this lookup. Need better way
            print "owner message"
            member_id, route_id = MessageUtils.split_owner_subject(mail_message.subject)
            route = models.Route.get_by_id(route_id)
            client_id = models.RouteMember.get_user_entry(route, member_id)
            try:
                create_owner_message(email_sender, messenger.SOURCE_TYPE_EMAIL,
                                     sender_user.get_id(), email_body, client_id, route_id)
            except MessageException, e:
                self.abort(200, e)
        else:
            self.abort(200, "Could not find message type in subject")

        self.set_default_success_response()
        self.send_response()


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

        print sender_user_id
        print receiver_user_id
        print message_body
        print route_id

        sender_user = models.User.get_by_id(sender_user_id)
        if sender_user is None:
            self.abort(422, "could not find user by that username")

        source_type = messenger.SOURCE_TYPE_NATIVE
        source = sender_user.pushRegKey

        message = None
        #message client -> owner
        if receiver_user_id is None:
            print "client message"
            try:
                message = create_client_message(source, source_type, sender_user_id,
                                                message_body, route_id)
            except MessageException, e:
                self.abort(422, e)
        #message owner -> client
        else:
            print "owner message"
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

        route_id = kwargs["route_id"].lower()
        client_id = kwargs["user_id"]
        num_to_fetch = int(kwargs["n"])

        curr_cursor = Cursor(urlsafe=self.get_param('cursor'))
        messages, cursor, more = models.Message.query(models.Message.routeId == route_id)\
                                               .filter(models.Message.clientUserId == client_id)\
                                                .order(-models.Message.created)\
                                                .fetch_page(num_to_fetch, start_cursor=curr_cursor)

        self.set_response_view_model(view_models.Message.view_list_contract())
        self.api_response = view_models.Message.form_list(messages, more, cursor)
        self.send_response()



