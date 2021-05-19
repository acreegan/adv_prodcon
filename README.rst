==========================
Advanced Producer-Consumer
==========================

.. image:: https://www.travis-ci.com/acreegan/adv_prodcon.svg?branch=main
        :target: https://travis-ci.com/acreegan/adv_prodcon

.. image:: https://readthedocs.org/projects/adv-prodcon/badge/?version=latest
        :target: https://adv-prodcon.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/acreegan/adv_prodcon/shield.svg
     :target: https://pyup.io/repos/github/acreegan/adv_prodcon/shield.svg
     :alt: Updates


Advanced Producer-Consumer is a python package implementing a full featured producer-consumer pattern for concurrent workers. This is useful for developing data acquisition programs or programs that involve real-time data processing while maintatining a responsive UI. It is compatible with PyQt5, which allows it to be used to develop graphical data acquisition and visualisation applications.


* Free software: MIT license
* Documentation: https://adv-prodcon.readthedocs.io.


Features
--------

* Producer and Consumer background workers are defined as metaclasses that can be extended by the user. They implement work functions that run in separate processes.
* Consumers are buffered and can be configured to run based on a timeout, a max buffer size, or both.
* The queues that connect Producers to Consumers can be either non-lossy or lossy.
* Producers and Consumers are connected by a subscription model. Producers can have multiple consumers subscribed to them. Consumers can be subscribed to multiple Producers.
* Producers and Consumers have on_start and on_stop functions that can be defined to run code for setup and teardown.
* Results from Consumers (and Producers) can be accessed in the main process through a user-defined callback.
* User defined functions can be defined to communicate between the main process and the work functions.
* Compatible with PyQt5, which allows development of graphical data acquisition and visualisation applications.

Installation
------------
To install Advanced Producer Consumer, run this command in your terminal:

.. code-block:: console

    $ pip install adv_prodcon

Quick Start
-----------
The following is a quick example of how to use the adv_prodcon package

.. code-block:: python

 import adv_prodcon
 import time
 from itertools import count

Imports.

.. code-block:: python

 class ExampleProducer(adv_prodcon.Producer):

     @staticmethod
     def on_start(state, message_pipe, *args, **kwargs):
         return {"count": count()}

     @staticmethod
     def work(on_start_result, state, message_pipe, *args):
         return next(on_start_result["count"])

Define a Producer class. Here we are using the on_start method to establish a itertools.count iterator. This is made available in the work function through the on_start_result argument. The work function will return the next count each time it is run.

.. code-block:: python

 class ExampleConsumer(adv_prodcon.Consumer):

     @staticmethod
     def work(items, on_start_result, state, message_pipe, *args):
         return f"Got :{items} from producer"

     def on_result_ready(self, result):
         print(result)

Define a Consumer Class. This Consumer will just be used as a buffer, returning a string with the items received from the Producer.
The on_result_ready function is called when the main process receives the result of the work function. Here we are just printing out the result.

.. code-block:: python

 if __name__ == "__main__":
     example_producer = ExampleProducer(work_timeout=1)
     example_consumer = ExampleConsumer(work_timeout=2,
                                        max_buffer_size=1000)

     example_producer.set_subscribers([example_consumer.get_work_queue()])
     example_producer.start_new()
     example_consumer.start_new()

     time.sleep(10)

In the main code block, we create an instance of both our ExampleProducer and our ExampleConsumer. We set the work_timeout of the ExampleProducer to 1 so that it runs once per second. We set the work_timeout of the ExampleConsumer to 2 so that every 2 seconds it performs work on all items in its queue. The max_buffer_size is set high so that the ExampleConsumer is controlled by its work_timeout.

The output of this code is shown below:

.. code-block:: console

 Got :[0, 1] from producer
 Got :[2, 3] from producer
 Got :[4, 5] from producer
 Got :[6, 7] from producer

 Process finished with exit code 0

Note that the output may be slightly different depending on the time taken to start the worker processes.

Credits
-------
* Development Lead: Andrew Creegan <andrew.s.creegan@gmail.com>
* This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
