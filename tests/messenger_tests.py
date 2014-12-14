from test_utils import AppEngineTest
from messenger import SMS

class TestSMS(AppEngineTest):
    def test_basic(self):
        SMS.send("3603036634", "cat@FreshDope [Nathaniel Wendt]" +
                                "\nhey dude can I have help with studying for the final?")

    def test_2(self):
        self.endpoint = "/v1/message/sms"
        self.method = 'POST'
        self.params["Body"] = "dog@RouteName lkeflkef"
        self.params["From"] = "3603036634"
        self.send()
        self.expect_resp_code(200)