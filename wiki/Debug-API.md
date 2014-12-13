# Debug API 

------------
##[POST] /v1/debug##

Sends a push notification along the pushRegKey path with the desired message

#####Params#####
`message` Message to send (varchar, required)

`pushRegKey` GCM push reg key to send message to (id, required)

#####Response#####

~~~~
{'status': 'success'}
~~~~

