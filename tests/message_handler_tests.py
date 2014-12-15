import models
from test_utils import AppEngineTest
import messenger
import view_models
from utils import MessageUtils
from google.appengine.ext import testbed
from message_handlers import *
import message_handlers


class TestMessageListHandler(AppEngineTest):
    def setUp(self):
        super(TestMessageListHandler, self).setUp()
        self.endpoint = "/v1/message/"

        models.User(id="user001", name="Nate Dogg").put()
        models.User(id="user002", name="Doug Beed").put()

        models.Route(id="greenleaf").put()

        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "source",
            "sourceType": messenger.SOURCE_TYPE_EMAIL,
            "senderUserId": "user001",
            "receiverUserId": "user002",
            "clientUserId": "user001",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        message_data["id"] = "message002"
        models.Message(**message_data).put()
        message_data["id"] = "message003"
        message_data["senderUserId"] = "user002"
        message_data["receiverUserId"] = "user001"
        message_data["clientUserId"] = "user001"
        models.Message(**message_data).put()

    def test_basic(self):
        self.method = "GET"
        self.endpoint += "greenleaf/user001/3"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_list_contract())
        messages = self.response_data["messages"]
        self.assertEqual(3, len(messages))
        self.assertEqual(messages[0]["id"], "message003")
        self.assertEqual(messages[1]["id"], "message002")
        self.assertEqual(messages[2]["id"], "message001")

    def test_cursor(self):
        self.method = "GET"
        self.endpoint += "greenleaf/user001/2"
        self.send()
        self.expect_resp_code(200)
        messages1 = self.response_data["messages"]
        self.assertEqual(2, len(messages1))
        self.assertIsNotNone(self.response_data["cursor"])

        #user cursor to continue query, will be an 'n' of 2, but only 1 entry left to retrieve
        self.params["cursor"] = self.response_data["cursor"]
        self.send()
        messages2 = self.response_data["messages"]
        self.assertEqual(1, len(messages2))
        self.assertEqual(messages2[0]["id"], "message001")


class MessengerMock(object):
    sms_count = 0
    gcm_count = 0

    def __init__(self):
        self.reset_counts()
        self.sms_send_original = messenger.SMS.send
        self.gcm_send_original = messenger.GCM.send

    def create(self):
        messenger.SMS.send = self.sms_send_mock
        messenger.GCM.send = self.gcm_send_mock

    def reset_counts(self):
        MessengerMock.sms_count = 0
        MessengerMock.gcm_count = 0

    def cleanup(self):
        messenger.SMS.send = self.sms_send_original
        messenger.GCM.send = self.gcm_send_original

    def sms_send_mock(self, *args):
        MessengerMock.sms_count += 1

    def gcm_send_mock(self, *args):
        MessengerMock.gcm_count += 1

    #@staticmethod
    #def gcm_send_mock(*args):
    #    MessengerMock.GCM_COUNT += 1

class RouteMock(object):
    def __init__(self):
        self.is_now_valid_backup = models.Route.is_now_valid

    def open_routes(self):
        models.Route.is_now_valid = lambda x: True

    def close_routes(self):
        models.Route.is_now_valid = lambda x: False

    def cleanup(self):
        models.Route.is_now_valid = self.is_now_valid_backup


class CreateMessageMock(object):
    def __init__(self):
        self.create_client_message_original = message_handlers.create_client_message
        self.create_owner_message_original = message_handlers.create_owner_message

        #create owner and client message
        self.source = ""
        self.source_type = ""
        self.sender_user_id = ""
        self.message_body = ""
        self.route_id = ""

        #create owner message
        self.client_id = ""

    def create_client_message_mock(self, source, source_type, sender_user_id,
                                   message_body, route_id):
        self.source = source
        self.source_type = source_type
        self.sender_user_id = sender_user_id
        self.message_body = message_body
        self.route_id = route_id

    def create_owner_message_mock(self, source, source_type, sender_user_id,
                                  message_body, client_id, route_id):
        self.create_client_message_mock(source, source_type, sender_user_id, message_body,
                                        route_id)
        self.client_id = client_id

    def create(self):
        message_handlers.create_client_message = self.create_client_message_mock
        message_handlers.create_owner_message = self.create_owner_message_mock

    def cleanup(self):
        message_handlers.create_client_message = self.create_client_message_original
        message_handlers.create_owner_message = self.create_owner_message_original

class InboundMessageMock(object):
    def __init__(self, sender, body, subject):
        self.sender = sender
        self.body = body
        self.subject = subject
        self.original = self

class MockedMessageTest(AppEngineTest):
    def setUp(self, messenger_mock=False, email_mock=False, create_message_mock=False):
        super(MockedMessageTest, self).setUp()
        self.route_mock = RouteMock()
        self.messenger_mock = MessengerMock()
        self.create_message_mock = CreateMessageMock()
        if messenger_mock:
            self.messenger_mock.create()
        if email_mock:
            self.testbed.init_mail_stub()
            self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        if create_message_mock:
            self.create_message_mock.create()

    def tearDown(self):
        self.route_mock.cleanup()
        self.messenger_mock.cleanup()
        self.create_message_mock.cleanup()
        super(MockedMessageTest, self).tearDown()


class TestMessageNativeCreationHandler(MockedMessageTest):
    def setUp(self):
        super(TestMessageNativeCreationHandler, self).setUp(messenger_mock=True, email_mock=True)

        self.messenger_mock = MessengerMock()
        self.route_mock.open_routes()
        self.endpoint = "/v1/message/native"

        self.owner = models.User(id="user001", name="Nate Dogg", pushRegKey="pushuser001")
        self.owner.put()

        self.client = models.User(id="user002", name="Chief Brent", pushRegKey="pushuser002")
        self.client.put()

        self.route = models.Route(id="greencow")
        self.route.userId = "user001"
        self.route.displayName = "GreenCow"
        self.route.emails = ["myemail@nate.com","otheremail@gmail.com"]
        self.route.phoneNumbers = ["+1334253245"]
        self.route.put()

        self.route_member = models.RouteMember.create_entry(self.route, "meerkat",
                                                            "user002", "Jeff Brown")
        self.route_member.put()

    def test_client_send(self):
        self.method = 'POST'
        self.params["senderUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "Yo dude you have to check this out!"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())

        #self.assertEqual(2, self.messenger_mock.)
        self.assertEqual(1, MessengerMock.sms_count)
        self.assertEqual(1, MessengerMock.gcm_count)

        message = models.Message.query().get()
        self.assertIsNotNone(message)
        self.assertEqual("greencow", message.routeId)
        self.assertEqual(messenger.SOURCE_TYPE_NATIVE, message.sourceType)
        self.assertEqual("pushuser002", message.source)
        self.assertEqual("user002", message.senderUserId)
        self.assertEqual("user001", message.receiverUserId)
        self.assertEqual("user002", message.clientUserId)
        self.assertEqual(self.params["message"], message.body)

    def test_client_send_invalid_sender(self):
        self.method = 'POST'
        self.params["senderUserId"] = self.INVALID_ID
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "Yo dude you have to check this out!"
        self.send()
        self.expect_resp_code(422)

    def test_client_send_invalid_closed_route(self):
        self.route_mock.close_routes()
        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "Yo dude you have to check this out!"
        self.send()
        self.expect_resp_code(422)

    def test_owner_send_to_native(self):
        message = models.Message(id="message002920")
        message.routeId = "greencow"
        message.source = messenger.SOURCE_VALUE_NATIVE
        message.sourceType = messenger.SOURCE_TYPE_NATIVE
        message.senderUserId = "user002"
        message.receiverUserId = "user001"
        message.clientUserId = "user002"
        message.body = "Yo dude you have to check this out!"
        message.put()

        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())

        self.assertEqual(1, MessengerMock.gcm_count)

        #delete first message so we only have to check for one
        message.key.delete()

        message = models.Message.query().get()
        self.assertIsNotNone(message)
        self.assertEqual("greencow", message.routeId)
        self.assertEqual(messenger.SOURCE_TYPE_NATIVE, message.sourceType)
        self.assertEqual("pushuser001", message.source)
        self.assertEqual("user001", message.senderUserId)
        self.assertEqual("user002", message.receiverUserId)
        self.assertEqual("user002", message.clientUserId)
        self.assertEqual(self.params["message"], message.body)

    def test_owner_send_to_sms(self):
        message = models.Message(id="message002920")
        message.routeId = "greencow"
        message.source = "+13935534532"
        message.sourceType = messenger.SOURCE_TYPE_SMS
        message.senderUserId = "user002"
        message.receiverUserId = "user001"
        message.clientUserId = "user002"
        message.body = "Yo dude you have to check this out!"
        message.put()

        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())

        self.assertEqual(1, MessengerMock.sms_count)
        #owner_to_native tested the state of message already

    def test_owner_send_to_email(self):
        message = models.Message(id="message002920")
        message.routeId = "greencow"
        message.source = "blob@gmail.com"
        message.sourceType = messenger.SOURCE_TYPE_EMAIL
        message.senderUserId = "user002"
        message.receiverUserId = "user001"
        message.clientUserId = "user002"
        message.body = "Yo dude you have to check this out!"
        message.put()

        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())
        #owner_to_native tested the state of message already

    def test_owner_send_invalid_no_prev_message(self):
        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(422)

    #owner should still be able to send messages when route is closed
    def test_owner_send_valid_closed(self):
        self.route_mock.close_routes()
        message = models.Message(id="message002920")
        message.routeId = "greencow"
        message.source = messenger.SOURCE_VALUE_NATIVE
        message.sourceType = messenger.SOURCE_TYPE_NATIVE
        message.senderUserId = "user002"
        message.receiverUserId = "user001"
        message.clientUserId = "user002"
        message.body = "Yo dude you have to check this out!"
        message.put()

        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())

class TestMessageSMSCreationHandler(MockedMessageTest):
    def setUp(self):
        super(TestMessageSMSCreationHandler, self).setUp(create_message_mock=True)
        self.endpoint += "/v1/message/sms"
        self.method = "POST"

        models.User(id="user001", name="John Owner", phoneNumbers=["+11111111111"]).put()
        models.User(id="user002", name="Steve Client", phoneNumbers=["+12222222222"]).put()

        self.route = models.Route(id="greenleaf", userId="user001", displayName="GreenLeaf")
        self.route.put()
        self.route_member = models.RouteMember.create_entry(self.route, "meerkat",
                                                            "user002", "Steve Client")
        self.route_member.put()

    def test_receive_from_client(self):
        self.params["Body"] = "#GreenLeaf Yo dawg hey"
        self.params["From"] = "+12222222222"
        self.send()
        self.expect_resp_code(200)
        self.assertEqual("user002", self.create_message_mock.sender_user_id)
        self.assertEqual("+12222222222", self.create_message_mock.source)
        self.assertEqual(messenger.SOURCE_TYPE_SMS, self.create_message_mock.source_type)
        self.assertEqual("greenleaf", self.create_message_mock.route_id)
        self.assertEqual("Yo dawg hey", self.create_message_mock.message_body)

    def test_receive_from_owner(self):
        self.params["Body"] = "meerkat@GreenLeaf Oh Heyyyyy dude"
        self.params["From"] = "+11111111111"
        self.send()
        self.expect_resp_code(200)
        self.assertEqual("user001", self.create_message_mock.sender_user_id)
        self.assertEqual("+11111111111", self.create_message_mock.source)
        self.assertEqual(messenger.SOURCE_TYPE_SMS, self.create_message_mock.source_type)
        self.assertEqual("greenleaf", self.create_message_mock.route_id)
        self.assertEqual("Oh Heyyyyy dude", self.create_message_mock.message_body)
        self.assertEqual("user002", self.create_message_mock.client_id)

    def test_invalid_sender_user(self):
        self.params["Body"] = "meerkat@GreenLeaf Oh Heyyyyy dude"
        self.params["From"] = "+19999999999"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_body(self):
        self.params["Body"] = "Oh Heyyyyy dude"
        self.params["From"] = "+11111111111"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_but_still_client_message(self):
        self.params["Body"] = "# Oh Heyyyyy dude"
        self.params["From"] = "+11111111111"
        self.send()
        self.expect_resp_code(422)

    def test_invalid_bust_still_owner_message(self):
        self.params["Body"] = "@ Oh Heyyyyy dude"
        self.params["From"] = "+11111111111"
        self.send()
        self.expect_resp_code(422)


class TestMessageEmailCreationHandler(MockedMessageTest):
    def setUp(self):
        super(TestMessageEmailCreationHandler, self).setUp(email_mock=True,
                                                           create_message_mock=True)
        def header_extract_mock(message):
            return self.header

        def abort(code, message):
            raise MessageException()

        self.get_header_from_message_original = MessageUtils.get_header_from_message
        MessageUtils.get_header_from_message = staticmethod(header_extract_mock)

        self.handler = MessageEmailCreationHandler(request=None, response=None)
        self.header = ""
        self.handler.abort = abort

        models.User(id="user001", name="John Owner", emails=["john@gmail.com"]).put()
        models.User(id="user002", name="Steve Client", emails=["steve@gmail.com"]).put()

        self.route = models.Route(id="greenleaf", userId="user001", displayName="GreenLeaf")
        self.route.put()
        self.route_member = models.RouteMember.create_entry(self.route, "meerkat",
                                                            "user002", "Steve Client")
        self.route_member.put()

    def tearDown(self):
        MessageUtils.get_header_from_message = self.get_header_from_message_original
        super(TestMessageEmailCreationHandler, self).tearDown()

    def test_receive_from_client(self):
        message_mock = InboundMessageMock("steve@gmail.com","body","#GreenLeaf")
        self.handler.receive(message_mock)
        self.assertEqual("user002", self.create_message_mock.sender_user_id)
        self.assertEqual("steve@gmail.com", self.create_message_mock.source)
        self.assertEqual(messenger.SOURCE_TYPE_EMAIL, self.create_message_mock.source_type)
        self.assertEqual("greenleaf", self.create_message_mock.route_id)
        self.assertEqual("body", self.create_message_mock.message_body)

    def test_receive_from_owner(self):
        self.header = "user002"
        message_mock = InboundMessageMock("john@gmail.com","body","mouse@GreenLeaf")
        self.handler.receive(message_mock)
        self.assertEqual("user001", self.create_message_mock.sender_user_id)
        self.assertEqual("john@gmail.com", self.create_message_mock.source)
        self.assertEqual(messenger.SOURCE_TYPE_EMAIL, self.create_message_mock.source_type)
        self.assertEqual("greenleaf", self.create_message_mock.route_id)
        self.assertEqual("body", self.create_message_mock.message_body)
        self.assertEqual("user002", self.create_message_mock.client_id)

    def test_receive_invalid_sender_user(self):
        message_mock = InboundMessageMock("INVALID@gmail.com","body","mouse@GreenLeaf")
        self.assertRaises(MessageException, self.handler.receive, message_mock)

class TestCreateOwnerMessage(MockedMessageTest):
    def setUp(self):
        super(TestCreateOwnerMessage, self).setUp(messenger_mock=True, email_mock=True)
        models.User(id="user001", name="John Owner", emails=["john@gmail.com"]).put()
        models.User(id="user002", name="Steve Client", emails=["steve@gmail.com"]).put()

        self.route = models.Route(id="greenleaf", userId="user001", displayName="GreenLeaf")
        self.route.put()
        self.route_member = models.RouteMember.create_entry(self.route, "meerkat",
                                                            "user002", "Steve Client")
        self.route_member.put()
        self.route_mock.open_routes()

    def test_basic_message_storage(self):
        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "steve@gmail.com",
            "sourceType": messenger.SOURCE_TYPE_EMAIL,
            "senderUserId": "user002",
            "receiverUserId": "user001",
            "clientUserId": "user002",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()

        message = create_owner_message("+13053353342", messenger.SOURCE_TYPE_SMS,
                                       "user001", "Hey man", "user002", "greenleaf")
        self.assertEqual("greenleaf", message.routeId)
        self.assertEqual(messenger.SOURCE_TYPE_SMS, message.sourceType)
        self.assertEqual("+13053353342", message.source)
        self.assertEqual(False, message.is_client_message())
        self.assertEqual("user002", message.receiverUserId)
        self.assertEqual("user001", message.senderUserId)
        self.assertEqual("user002", message.clientUserId)

    def test_outgoing_email(self):
        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "steve@gmail.com",
            "sourceType": messenger.SOURCE_TYPE_EMAIL,
            "senderUserId": "user002",
            "receiverUserId": "user001",
            "clientUserId": "user002",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        message = create_owner_message("+13053353342", messenger.SOURCE_TYPE_SMS,
                                       "user001", "Hey man", "user002", "greenleaf")
        message = self.mail_stub.get_sent_messages(to='steve@gmail.com')[0]
        self.assertIsNotNone(message)

    def test_outgoing_sms(self):
        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "+1233424444",
            "sourceType": messenger.SOURCE_TYPE_SMS,
            "senderUserId": "user002",
            "receiverUserId": "user001",
            "clientUserId": "user002",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        message = create_owner_message("+13053353342", messenger.SOURCE_TYPE_SMS,
                                       "user001", "Hey man", "user002", "greenleaf")
        self.assertEqual(1, MessengerMock.sms_count)
        self.assertEqual(0, MessengerMock.gcm_count)

    def test_outgoing_gcm(self):
        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "pushRegKey",
            "sourceType": messenger.SOURCE_TYPE_NATIVE,
            "senderUserId": "user002",
            "receiverUserId": "user001",
            "clientUserId": "user002",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        message = create_owner_message("+13053353342", messenger.SOURCE_TYPE_SMS,
                                       "user001", "Hey man", "user002", "greenleaf")
        self.assertEqual(1, MessengerMock.gcm_count)
        self.assertEqual(0, MessengerMock.sms_count)

    def test_invalid_no_last_message(self):
        params = ("+13053353342", messenger.SOURCE_TYPE_SMS,
                 "user001", "Hey man", "user002", "greenleaf")
        self.assertRaises(MessageException, create_owner_message, *params)

    def test_invalid_route(self):
        params = ("+13053353342", messenger.SOURCE_TYPE_SMS,
                 "user001", "Hey man", "user002", "INVALID_ROUTE")
        self.assertRaises(MessageException, create_owner_message, *params)

    def test_invalid_prev_message_source_type(self):
        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "pushRegKey",
            "sourceType": 9999, #invalid source type
            "senderUserId": "user002",
            "receiverUserId": "user001",
            "clientUserId": "user002",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        params = ("+13053353342", messenger.SOURCE_TYPE_SMS,
                 "user001", "Hey man", "user002", "greenleaf")
        self.assertRaises(MessageException, create_owner_message, *params)

class TestCreateClientMessage(MockedMessageTest):
    def setUp(self):
        super(TestCreateClientMessage, self).setUp(messenger_mock=True, email_mock=True)
        models.User(id="user001", name="John Owner", emails=["john@gmail.com"]).put()
        models.User(id="user002", name="Steve Client", emails=["steve@gmail.com"]).put()

        self.route = models.Route(id="greenleaf", userId="user001", displayName="GreenLeaf")
        self.route.put()
        self.route_member = models.RouteMember.create_entry(self.route, "meerkat",
                                                            "user002", "Steve Client")
        self.route_member.put()

        message_data = {
            "id": "message001",
            "routeId": "greenleaf",
            "source": "source",
            "sourceType": messenger.SOURCE_TYPE_EMAIL,
            "senderUserId": "user001",
            "receiverUserId": "user002",
            "clientUserId": "user001",
            "body": "message 1 body"
        }
        models.Message(**message_data).put()
        self.route_mock.open_routes()

    def test_basic_message_storage(self):
        message = create_client_message("+13603036622",messenger.SOURCE_TYPE_SMS,
                                        "user002", "Yo dawg", "greenleaf")
        self.assertEqual("greenleaf", message.routeId)
        self.assertEqual(messenger.SOURCE_TYPE_SMS, message.sourceType)
        self.assertEqual("+13603036622", message.source)
        self.assertEqual(True, message.is_client_message())
        self.assertEqual("user001", message.receiverUserId)
        self.assertEqual("user002", message.senderUserId)
        self.assertEqual("user002", message.clientUserId)

    def test_basic_outgoing_email(self):
        self.route.emails = ["john@gmail.com"]
        self.route.put()
        message = create_client_message("+13603036622",messenger.SOURCE_TYPE_SMS,
                                        "user002", "Yo dawg", "greenleaf")
        message = self.mail_stub.get_sent_messages(to='john@gmail.com')[0]
        self.assertEqual("HandshakeMessage: meerkat@GreenLeaf [Steve Client]\n", message.subject)
        self.assertEqual("john@gmail.com", message.to)
        self.assertEqual(messenger.Email.APP_SENDER, message.sender)
        self.assertEqual(1, MessengerMock.gcm_count)

    def test_basic_outgoing_phones(self):
        self.route.phoneNumbers = ["+13603036622","+1234453532"]
        self.route.put()
        message = create_client_message("+13603036622",messenger.SOURCE_TYPE_SMS,
                                        "user002", "Yo dawg", "greenleaf")
        self.assertEqual(1, MessengerMock.gcm_count)
        self.assertEqual(2, MessengerMock.sms_count)
        message = self.mail_stub.get_sent_messages(to='john@gmail.com')
        self.assertIsNotNone(message)

    def test_invalid_route_closed(self):
        self.route_mock.close_routes()
        args = ("+13603036622",messenger.SOURCE_TYPE_SMS,
                "user002", "Yo dawg", "greenleaf")
        self.assertRaises(MessageException, create_client_message, *args)

    def test_invalid_nonexistent_route(self):
        args = ("+13603036622",messenger.SOURCE_TYPE_SMS,
                "user002", "Yo dawg", "INVALIDROUTE")
        self.assertRaises(MessageException, create_client_message, *args)

