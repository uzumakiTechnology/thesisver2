main.py
- Fast API :
- HTTPException: a way too generate HTTP error response in FastApi app
- BaseModel: A class provided by Pydantic that is used to define data models with type hinting, validation, and conversion.


when new data is received via socket, it is added to the orderData state
every orderData state is updated, updatedChart should be called to redraw the chart, this should happen in the useEffect

What we need to do right now :
Due to choosing the domain from 3 hours
Setting :

Fetch the timestamp of order
When we choosing to send new price, at that trigger moment, increase the timestamp of current order for 30 minutes 