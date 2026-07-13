RPC Functionality
=================

The ``RPCMixin`` allows your SPADE agent to perform and respond to remote procedure calls using the XEP-0009 standard.

.. note::
   The mixin automatically registers the ``xep_0009`` plugin upon initialization.

Using Remote Calls (``call``)
-----------------------------

To invoke a method on a remote agent, use the ``call`` method. This method sends an IQ stanza containing the method name and parameters, and returns the result once received.

.. code-block:: python

   # Example: Calling a remote method
   result = await agent.rpc.call(
       jid="target@example.com",
       method_name="get_status",
       params=["arg1", "arg2"],
       timeout=10
   )

* **jid**: The Jabber ID of the target agent.
* **method_name**: The name of the RPC method to invoke.
* **params**: A list of arguments to pass to the method.
* **timeout**: Time in seconds to wait for a response (default is 10).

Registering Methods (``register_method``)
-----------------------------------------

To allow other agents to call functions on your agent, you must expose them using ``register_method``. This maps a local function to a string identifier that remote agents can call.

.. code-block:: python

   # Define your handler
   def my_handler(arg1, arg2):
       return f"Processed {arg1} and {arg2}"

   # Register the handler
   agent.rpc.register_method(handler=my_handler, method_name="process_data")

The wrapper handles the underlying conversion of XML to Python types automatically, allowing your handler to receive standard Python objects.
