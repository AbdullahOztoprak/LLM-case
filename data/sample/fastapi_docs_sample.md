# Path Parameters

FastAPI lets you declare path parameters using the same syntax used by Python format
strings. The value from the URL path is passed to your path operation function as an
argument.

## Declare path parameters

If the path is `/items/{item_id}`, the function can define `item_id` as a parameter.
FastAPI reads the value from the URL, converts it according to the Python type
annotation, validates it, and provides it to the function.

## Data validation

When a request contains an invalid path parameter, FastAPI returns a validation error
instead of calling the endpoint function.
