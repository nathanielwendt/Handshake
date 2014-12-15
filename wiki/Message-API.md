# Message API 

------------
##[GET] /v1/message/{route_id}/{user_id}/{n}##

Retrieves a list of messages as a back and forth between a route owner and single client

#####Params#####
`cursor` query cursor to resume querying position (id, optional)

#####Response#####

~~~~
{'cursor': '*',
 'messages': [{'clientUserId': '+',
               'id': '+',
               'isClient': '+',
               'message': '+',
               'routeId': '+'}],
 'more': '+'}
~~~~

------------
##[POST] /v1/message/native##

Creates a message from the native app.

#####Params#####
`message` message body (varchar, required)

`receiverUserId` the id of the receiving user (id, optional)

`senderUserId` the id of the sending user (id, required)

`routeId` the id of the route along which to send the message (varchar, required)

#####Response#####

~~~~
{'clientUserId': '+',
 'id': '+',
 'isClient': '+',
 'message': '+',
 'routeId': '+'}
~~~~

------------
##[POST] /v1/message/sms##

Creates a message from an sms message

#####Params#####
`Body` message body, route name should be included in message (varchar, required)

`From` number from which the message originates (phone, required)

#####Response#####

~~~~
{'status': 'success'}
~~~~

