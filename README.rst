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


Python package implementing a full featured producer/consumer pattern for concurrent workers


* Free software: MIT license
* Documentation: https://adv-prodcon.readthedocs.io.


Features
--------

* Producer and Consumer background workers are defined as metaclasses that can be extended by the user. They implement work functions that run in separate processes.
* Consumers are buffered and can be configured to run based on a timeout, a max buffer size, or both.
* The queues that connect Producers to Consumers can be either non-lossy or lossy.
* Producers and Consumers are connected by a subscription model. Producers can have multiple consumers subscribed to them. Consumers can be subscribed to multiple Producers.
* Producers and Consumers have onStart and onStop functions that can be defined to run code for setup and teardown.
* Results from Consumers (and Producers) can be accessed in the main process through a user-defined callback.
* User defined functions can be defined to communicate between the main process and the work functions.


Credits
-------
* Development Lead: Andrew Creegan <andrew.s.creegan@gmail.com>
* This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
