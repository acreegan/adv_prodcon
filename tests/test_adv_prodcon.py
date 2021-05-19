#!/usr/bin/env python

"""Tests for `adv_prodcon` package."""

import unittest
from adv_prodcon import Producer, ReadyQueue
from multiprocessing import freeze_support
import time


class Testadv_prodcon(unittest.TestCase):
    def test_set_stopped(self):
        t = MyTestProducer()
        t.set_subscribers([ReadyQueue()])
        t.start_new()
        t.set_stopped()
        time.sleep(1)
        t.process.join()
        self.assertEqual(t.message, "stopped")

    def test_simple_test(self):
        t = MyTestProducer()
        self.assertEqual(t.get_state(), t.stopped)


class MyTestProducer(Producer):
    def __init__(self):
        super().__init__()
        self.message = None

    @staticmethod
    def work(on_start_result, state, message_pipe, *args):
        pass

    @staticmethod
    def on_stop(on_start_result, state, message_pipe, *args, **kwargs):
        message_pipe.send("stopped")

    def on_message_ready(self, message):
        self.message = message


if __name__ == '__main__':
    freeze_support()
