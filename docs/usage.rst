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
Instantiating Producers and Consumers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Producers and Consumers are instantiated in the normal way by calling their classes:

.. code-block:: python

    example_producer = ExampleProducer()
    example_consumer = ExampleConsumer()

When a Producer is instantiated, it is possible to set it's work_timeout as shown:

.. code-block:: python

    example_producer = ExampleProducer(work_timeout=1)

This sets the time in seconds between calls to the Producer's work function. In most cases however, it is best to leave this at its default value of 0 so that the Producer runs as fast as possible. This is especially advisable if the work function contains a blocking call such as serial.readline.

When a Consumer is instantiated it is possible to set its work_timeout and its max_buffer_size as shown:

.. code-block:: python

    example_consumer = ExampleConsumer(work_timeout=2, max_buffer_size=1000)

The Consumer's work function runs if the work_timeout is exceeded OR the max_buffer_size is exceeded. Therefore if you want the Consumer to mainly be driven by time, set the max_buffer_size high. If you want the Consumer to mainly be driven by buffer size, set the work_timeout high. Otherwise the Consumer can be triggered by either, which can be useful especially if it is subscribed to multiple producers.

Linking Producers with Consumers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
adv_prodcon handles connections between Producers and Consumers using a subscription model. Producers can have multiple subscribers, and will put the results of their work functions into each of their subscribers' queues. (This is useful for example if you want to read from a serial port, and both plot the results and print the raw results to the screen) Consumers can have multiple subscriptions, and will receive messages in their single queue from each of the Producers they are subscribed to. (This is useful for example if you want to implement a Consumer that saves the data from multiple Producers to file)

Subscriptions are set by using the Producer's set_subscribers method. The input to this method is a list of queues retrieved from Consumers by means of the get_work_queue method.

Subscribing a Single Consumer to Multiple Producers
"""""""""""""""""""""""""""""""""""""""""""""""""""
The code below shows an example of subscribing a single Consumer to multiple Producers:

.. code-block:: python

    producer1.set_subscribers([consumer.get_work_queue()])
    producer2.set_subscribers([consumer.get_work_queue()])

Subscribing Multiple Consumers to a Single Producer
"""""""""""""""""""""""""""""""""""""""""""""""""""
The example below shows how to subscribe multiple Consumers to a single Producer

.. code-block:: python

    producer.set_subscribers([consumer1.get_work_queue(), consumer2.get_work_queue()])

Note that producer.set_subscribers must be called with a list as its argument even if it only contains one item.
Also note that producer.set_subscribers must be called before calling producer.start_new, since the queues must be passed to the worker process during creation.

Lossy Queues
^^^^^^^^^^^^
When implementing a Producer-Consumer pattern, sometimes it is important to make sure that the Consumer processes every single item sent by the Producer (e.g. when saving to file), and sometimes it is more important that the Consumer processes the latest data (e.g. when performing an expensive processing algorithm then plotting the result). Lossy queues are available for the latter situation. An example of instantiating a Consumer with a lossy queue is shown below:

.. code-block:: python

    self.consumer = DataConsumer(work_timeout=0.01, max_buffer_size=1000, lossy_queue=True)


Starting and Stopping
---------------------
Starting
^^^^^^^^
In order to start a Producer or Consumer, a call to their start_new method must be made. Note that all Producers and Consumers need to be started individually for them to function. Below is an example of this:

.. code-block:: python

    example_producer.start_new()
    example_consumer.start_new()

Work Args and Work Kwargs
^^^^^^^^^^^^^^^^^^^^^^^^^
When calling the start_new method, there is an opportunity to add additional args and kwargs for the work, on_start, and on_stop methods. Any args and kwargs added here will be concatenated with any args and kwargs added in the Producer or Consumer implementation. The code below shows an example of setting args and kwargs while calling start_new:

.. code-block:: python

    example_producer.start_new(work_args=(arg1,arg2), work_kwargs={"first_kwarg":1, "second_kwarg": 2})

Stopping
^^^^^^^^
In order to stop a Producer or Consumer, call the set_stopped method. For example:

.. code-block:: python

    producer.set_stopped()
    consumer.set_stopped()

Stop at Queue End
^^^^^^^^^^^^^^^^^
Often instead of stopping a Consumer immediately it is important to ensure that it has processed all the data in its queue. In these situations, stop the consumer by calling set_stop_at_queue_end. For example:

.. code-block:: python

    consumer.set_stop_at_queue_end()

This ensures that the Consumer's work function is called one final time with the remaining items in its queue even if the work_timeout or max_buffer_size are not exceeded.

Message Pipe
------------
In some cases it is necessary for the main process to communicate with a Producer or Consumer's work function, or vice versa. For this, the message pipe is available. The each Worker has a message pipe which is sent to its work function as an argument. In the main process, the Worker monitors the message pipe for any messages from the work function, and calls on_message_ready when a message is received.

Sending a Message from the Main Process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following is an example of a work function that checks the message pipe for a signal:

.. code-block:: python

    @staticmethod
    def work(on_start_result, state, message_pipe, *args):

        # Receive a message from main process
        if message_pipe.poll():
            if message_pipe.recv() == "reset":
                on_start_result["count"] = count()

        return next(on_start_result["count"])

In order to send a message to the work function, use message_pipe_parent.send, as shown:

.. code-block:: python

    example_producer.message_pipe_parent.send("reset")

Receiving a Message in the Main Process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following is an example of a work function that sends a message to the main process:

.. code-block:: python

    @staticmethod
    def work(on_start_result, state, message_pipe, *args):

        number = next(on_start_result["count"])

        # Send a message to main process
        if number > 5:
            message_pipe.send("reached 5")

        return number

When the message is received in the main process, on_message_ready is called. For example:

.. code-block:: python

    def on_message_ready(self, message):
        if message == "reached 5":
            print("Reached 5")

Integration with PyQt5
----------------------
In order to integrate adv_prodcon with PyQt5, simply extend PyQt5.QtCore.QObject in addition to adv_prodcon.Consumer. Declare a PyQt5.QtCore.pyqtSignal, and in the on_result_ready method, call emit.

.. code-block:: python

    class DataConsumer(adv_prodcon.Consumer, PyQt5.QtCore.QObject):
        new_data = PyQt5.QtCore.pyqtSignal(list)

        def __init__(self, *args, **kwargs):
            PyQt5.QtCore.QObject.__init__(self)
            adv_prodcon.Consumer.__init__(self, *args, **kwargs)

        @staticmethod
        def work(items, on_start_result, state, message_pipe, *args):
            return items

        def on_result_ready(self, result):
            self.new_data.emit(result)

Sending Data from the Main Process
----------------------------------
In some cases it is necessary to send data to a consumer directly from the main process. In order to do this, use the put_in_queue method.

.. code-block:: python

    put_in_queue(consumer.get_work_queue(), item)
