import adv_prodcon
import time
from itertools import count
import sys


class ExampleProducer(adv_prodcon.Producer):
    exit = False

    @staticmethod
    def on_start(state, message_pipe, *args, **kwargs):
        return {"count": count()}

    @staticmethod
    def work(on_start_result, state, message_pipe, *args):

        # Receive a message from main process
        if message_pipe.poll():
            if message_pipe.recv() == "reset":
                on_start_result["count"] = count()

        number = next(on_start_result["count"])

        # Send a message to main process
        if number > 5:
            message_pipe.send("reached 5")

        return number

    def on_message_ready(self, message):
        if message == "reached 5":
            self.exit = True


class ExampleConsumer(adv_prodcon.Consumer):

    @staticmethod
    def work(items, on_start_result, state, message_pipe, *args):
        for item in items:
            print(item)


if __name__ == "__main__":
    example_producer = ExampleProducer(work_timeout=1)
    example_consumer = ExampleConsumer(work_timeout=2,
                                       max_buffer_size=1000)

    example_producer.set_subscribers([example_consumer.get_work_queue()])
    example_producer.start_new()
    example_consumer.start_new()

    time.sleep(5)

    print("Resetting...")
    example_producer.message_pipe_parent.send("reset")

    while True:
        if example_producer.exit:
            print("Exiting.")
            sys.exit(0)
