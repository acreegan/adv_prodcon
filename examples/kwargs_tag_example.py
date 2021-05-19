from adv_prodcon import Producer, Consumer
import time


class MyProducer(Producer):
    def __init__(self, *args, **kwargs):
        tag = kwargs.pop("tag")
        Producer.__init__(self, *args, **kwargs)
        self.work_kwargs = {"tag": tag}

    @staticmethod
    def work(on_start_result, state, message_pipe, *args, **kwargs):
        return f'Message from {kwargs["tag"]}'


class MyConsumer(Consumer):
    @staticmethod
    def work(items, on_start_result, state, message_pipe, *args):
        for item in items:
            print(item)


if __name__ == "__main__":
    producer1 = MyProducer(tag="Mary", work_timeout=1)
    producer2 = MyProducer(tag="James", work_timeout=1)

    consumer = MyConsumer()
    producer1.set_subscribers([consumer.get_work_queue()])
    producer2.set_subscribers([consumer.get_work_queue()])

    producer1.start_new()
    producer2.start_new()
    consumer.start_new()

    time.sleep(5)
