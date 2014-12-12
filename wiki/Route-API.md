# Route API 

------------
##[POST] /v1/route##

Creates a route with 1 or more communication channels attached
:return:

#####Params#####
`slots` Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" } (slot_list, required)

`userId` Id for user that is creating the route (id, required)

`phoneNumbers` Numbers attached to the route (num_list, optional)

`emails` Emails attached to the route (email_list, optional)

#####Response#####

~~~~
{'emails': ['+'],
 'id': '+',
 'phoneNumbers': ['+'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'}],
 'userId': '+'}
~~~~

------------
##[PUT] /v1/route/{id}##

Updates route parameters.
Note: updating slots will wipe old slots and replace with new set.

#####Params#####
`slots` Access Slot items formatted as { "start": "+", "end": "+", "repeatInterval": "+", "cutoff": "+" } (slot_list, optional)

`phoneNumbers` Numbers attached to the route (num_list, optional)

`emails` Emails attached to the route (email_list, optional)

#####Response#####

~~~~
{'emails': ['+'],
 'id': '+',
 'phoneNumbers': ['+'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'}],
 'userId': '+'}
~~~~

------------
##[GET] /v1/route/{id}##

Retrieves a route by route name

#####Params#####

None

#####Response#####

~~~~
{'emails': ['+'],
 'id': '+',
 'phoneNumbers': ['+'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'}],
 'userId': '+'}
~~~~

------------
##[POST] /v1/route/{id}/join##

Joins a user to a specific route

#####Params#####
`userId` id of user to join route (id, required)

#####Response#####

~~~~
{'status': 'success'}
~~~~

