import json
from handler_utils import APIBaseHandler
import models
import view_models
from handler_utils import getUUID, IDTYPE, Namer

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