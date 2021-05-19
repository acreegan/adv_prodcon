==========
User Guide
==========

To use Advanced Producer Consumer in a project::

    import adv_prodcon


Implementing a Producer
-----------------------
A Producer is a type of Worker that generates data periodically, normally by reading from a communication channel external to the application, e.g. a serial connection. This data is put into each of a list of queues that are subscribed to the Producer.

The minimum code necessary to implement a Producer is to define a class that derives from adv_prodcon.Producer, and implement its abstract method: work. An example of a Producer class that simply returns the time is shown below:

.. code-block:: python

    class ExampleProducer(adv_prodcon.Producer):

        @staticmethod
        def work(on_start_result, state, message_pipe, *args):
            return time.time()

.. _Producer On_Start and On_Stop:

On_Start and On_Stop
^^^^^^^^^^^^^^^^^^^^
When there is a need for code to be run once before the main work loop is started, or after it finishes, the on_start and on_stop methods are available. These are useful for example to set up and close a serial connection. The result from the on_start function is available in the work function and on_stop function through the argument on_start_result. An example is shown below:

.. code-block:: python

    class ExampleProducer(adv_prodcon.Producer):

        @staticmethod
        def on_start(state, message_pipe, *args, **kwargs):
            device = serial.Serial(port=kwargs["port"], baudrate=kwargs["baud"])
            return {"device": device}

        @staticmethod
        def work(on_start_result, state, message_pipe, *args):
            return on_start_result["device"].readLine()

        @staticmethod
        def on_stop(on_start_result, state, message_pipe, *args, **kwargs):
            on_start_result["device"].close()

.. _Producer Work Args and Work Kwargs:

Work Args and Work Kwargs
^^^^^^^^^^^^^^^^^^^^^^^^^
The work, on_start, and on_stop methods are all static, since they need to be passed to a separate process. This means that they will not have access to any attributes in the parent class.

If you want to make any extra data available to the work, on_start, and on_stop methods, the work_args and work_kwargs attributes can be used. The work_args and work_kwargs attributes are initialized as an empty tuple and empty dict respectively, and they are passed as arguments to the work, on_start, and on_stop methods. An example is shown below:

.. code-block:: python

    class MyProducer(Producer):
        def __init__(self, *args, **kwargs):
            tag = kwargs.pop("tag")
            Producer.__init__(self, *args, **kwargs)
            self.work_kwargs = {"tag": tag}

        @staticmethod
        def work(on_start_result, state, message_pipe, *args, **kwargs):
            return f'Message from {kwargs["tag"]}'


Implementing a Consumer
-----------------------
A Consumer is a type of worker which possesses a queue. The worker continuously monitors this queue for new items put there by a Producer to which it is subscribed. When certain criteria are met, the Consumer sends the whole buffer of items to is work function.

Implementing a Consumer is much the same as implementing a Producer, with the only requirement being to extend the Consumer class and implement the abstract work function. An example is shown below:

.. code-block:: python

    class MyConsumer(Consumer):
        @staticmethod
        def work(items, on_start_result, state, message_pipe, *args):
            for item in items:
                print(item)

On_Start and On_Stop
^^^^^^^^^^^^^^^^^^^^
The on_start and on_stop methods for a Consumer are the same as those for a Producer. See: :ref:`Producer On_Start and On_Stop`

Work Args and Work Kwargs
^^^^^^^^^^^^^^^^^^^^^^^^^
The work_args and work_kwargs attributes for a Consumer are the same as those for a Producer. See: :ref:`Producer Work Args and Work Kwargs`

Result Pipe
^^^^^^^^^^^
The result pipe is used to transfer data from a consumer back to the main process. In the Worker class, one end of the result pipe is sent to the work_loop when start_new is called. The other end is continuously monitored in a thread in the main process. When data is sent through the result pipe from the work process to the main process, the Worker's on_result_ready method is called with the result as an argument. An example is shown below:

.. code-block:: python

    class ExampleConsumer(adv_prodcon.Consumer):

        @staticmethod
        def work(items, on_start_result, state, message_pipe, *args):
            return f"Got :{items} from producer"

        def on_result_ready(self, result):
            print(result)

In this example, when the Consumer's work method is called, it will return a string listing the items it has received from the Producer. This string will be passed through the result pipe, and once it is received by the polling thread, the on_result_ready will be called with this string as the result parameter.

Since on_result_ready is called in the main process, it can interact with other main process objects, store data in the ExampleConsumer's attributes to be read later, or integrate with Qt as will be shown later in this guide.

Note that the Producer also has a result pipe, but it is recommended to always pass a Producer's data through a consumer so that you are able to control the rate at which data is sent to the main process.

Instantiating and Linking Producers and Consumers
-------------------------------------------------
Lossy Queues
^^^^^^^^^^^^
When implementing a Producer-Consumer pattern, sometimes it is important to make sure that the Consumer processes every single item sent by the Producer (e.g. when saving to file), and sometimes it is more important that the Consumer processes the latest data (e.g. when performing an expensive processing algorithm then plotting the result). Lossy queues are available for the latter situation.

Multiple Subscribers and Multiple Subscriptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Starting and Stopping
---------------------

Message Pipe
------------

Usage with PyQt5
----------------

Sending Data from the Main Process
----------------------------------
