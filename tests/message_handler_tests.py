import models
from test_utils import AppEngineTest
import messenger
import view_models

class TestMessageCreationHandler(AppEngineTest):
    pass


class MessengerMock(object):
    SMS_COUNT = 0
    EMAIL_COUNT = 0
    GCM_COUNT = 0

    @staticmethod
    def reset_counts():
        MessengerMock.SMS_COUNT = 0
        MessengerMock.EMAIL_COUNT = 0
        MessengerMock.GCM_COUNT = 0

    @staticmethod
    def sms_send_mock(*args):
        MessengerMock.SMS_COUNT += 1

    @staticmethod
    def email_send_mock(*args):
        MessengerMock.EMAIL_COUNT += 1

    @staticmethod
    def gcm_send_mock(*args):
        MessengerMock.GCM_COUNT += 1

    @staticmethod
    def create_messenger_mocks():
        messenger.SMS.send = staticmethod(MessengerMock.sms_send_mock)
        messenger.Email.send = staticmethod(MessengerMock.email_send_mock)
        messenger.GCM.send = staticmethod(MessengerMock.gcm_send_mock)

    @staticmethod
    def make_route_open():
        models.Route.is_now_valid = lambda x: True

    @staticmethod
    def make_route_closed():
        models.Route.is_now_valid = lambda x: False

class TestMessageNativeCreationHandler(AppEngineTest):
    def setUp(self):
        super(TestMessageNativeCreationHandler, self).setUp()
        MessengerMock.create_messenger_mocks()
        MessengerMock.reset_counts()
        MessengerMock.make_route_open()
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

        self.assertEqual(2, MessengerMock.EMAIL_COUNT)
        self.assertEqual(1, MessengerMock.SMS_COUNT)
        self.assertEqual(1, MessengerMock.GCM_COUNT)

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
        MessengerMock.make_route_closed()
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

        self.assertEqual(1, MessengerMock.GCM_COUNT)

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

        self.assertEqual(1, MessengerMock.SMS_COUNT)
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
        message = models.Message(id="message002920")
        message.routeId = "greencow"
        message.source = messenger.SOURCE_VALUE_NATIVE
        message.sourceType = messenger.SOURCE_TYPE_NATIVE
        message.senderUserId = "user002"
        message.receiverUserId = "user001"
        message.clientUserId = "user002"
        message.body = "Yo dude you have to check this out!"
        message.put()

        MessengerMock.make_route_closed()
        self.method = 'POST'
        self.params["senderUserId"] = "user001"
        self.params["receiverUserId"] = "user002"
        self.params["memberName"] = "meerkat"
        self.params["routeId"] = "GreenCow"
        self.params["message"] = "I will check it out as soon as I can. :)"
        self.send()
        self.expect_resp_code(200)
        self.expect_resp_conforms(view_models.Message.view_contract())


class TestMessageListHandler(AppEngineTest):
    def setUp(self):
        super(TestMessageListHandler, self).setUp()
        self.endpoint = "v1/message/"


