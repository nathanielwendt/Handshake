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
 'name': '+',
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
##[GET] /v1/route/{name}##

Retrieves a route by id

#####Params#####

None

#####Response#####

~~~~
{'emails': ['+'],
 'name': '+',
 'phoneNumbers': ['+'],
 'slots': [{'active': '+',
            'cutoff': '+',
            'end': '+',
            'repeatInterval': '+',
            'slotId': '+',
            'start': '+'}],
 'userId': '+'}
~~~~

