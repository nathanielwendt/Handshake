import json
from handler_utils import APIBaseHandler, ValidatorException
import models
import view_models
from models import getUUID, IDTYPE
from handler_utils import ValidatorException
import messenger

class DebugPushNotificationHandler(APIBaseHandler):
    def post(self):
        """
        Sends a push notification along the pushRegKey path with the desired message

        :param pushRegKey: GCM push reg key to send message to
        :param message: Message to send
        """
        contract = {
            "pushRegKey": ["id", "+"],
            "message": ["varchar","+"],
        }
        try:
            self.check_params_conform(contract)
        except ValidatorException:
            return

        messenger.GCM.send(self.get_param("pushRegKey"), self.get_param("message"))

        self.set_default_success_response()
        self.send_response()