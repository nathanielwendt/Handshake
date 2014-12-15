#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from route_handlers import *
from message_handlers import *
from user_handlers import *
from web_handlers import *
from debug_handlers import *

v1_routes = [
    webapp2.Route(r'/v1/user', handler=UserCreationHandler, name="User-Creation"),
    webapp2.Route(r'/v1/user/<id:[\w-]+>/notifications',
                  handler=UserNotificationsHandler, name="User-Notifications"),
    webapp2.Route(r'/v1/user/<id:[\w-]+>', handler=UserHandler, name="User"),

    #[App Names]
    #Fleet
    #Groovy
    #Nimbus

    #[Channel Names]
    #Route
    #Groove
    #Trail
    #Track
    #Line
    #Knit
    #Notch
    webapp2.Route(r'/v1/route', handler=RouteCreationHandler, name="Route-Creation"),
    webapp2.Route(r'/v1/route/<id:([\w|\W])+>/member/list',
                  handler=RouteMemberListHandler, name="Route-MemberList"),
    webapp2.Route(r'/v1/route/<id:([\w|\W])+>/member',
                  handler=RouteMemberCreationHandler, name="Route-MemberCreation"),
    webapp2.Route(r'/v1/route/list', handler=RouteListHandler, name="Route-List"),
    webapp2.Route(r'/v1/route/<id:([\w|\W])+>', handler=RouteHandler, name="Route"),

    webapp2.Route(r'/v1/message/<route_id:([\w|\W])+>/<user_id:[\w-]+>/<n:[0-9]+>',
                  handler=MessageListHandler, name="Message-List"),
    webapp2.Route(r'/v1/message/native', handler=MessageNativeCreationHandler, name="Message-NativeCreation"),
    webapp2.Route(r'/v1/message/sms', handler=MessageSMSCreationHandler, name="Message-SMSCreation"),
    # MessageEmailCreationHandler is called internally

    MessageEmailCreationHandler.mapping(),

    webapp2.Route(r'/v1/debug', handler=DebugPushNotificationHandler, name="Debug-PushNotification")
]

web_routes = [
    webapp2.Route(r'/', handler=WebHomeHandler, name="Web-HomeHandler")
]



routes = v1_routes + web_routes
app = webapp2.WSGIApplication(routes = routes, debug=True)