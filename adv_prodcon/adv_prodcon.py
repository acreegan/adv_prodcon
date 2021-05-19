from multiprocessing import Process, Value, Pipe, Queue
from threading import Thread
import time
from abc import ABCMeta, abstractmethod
import atexit
from queue import Empty
import ctypes
import pickle


class Worker:
    """
    The main metaclass for adv_prodcon. Worker should not be used directly. Instead, the Producer and Consumer
    classes that derive from this should be used as the base for classes that users define.

    Worker defines the methods that are common to both Producer and Consumer. Most importantly it defines the start_new
    method which handles creation of a new process where the work is run.

    Worker also contains two instances of multiprocessing.Pipe. The result pipe is used by Producer and Consumer to send
    results from their work functions back to the main process. The message pipe is made available to derived classes by
    passing it as an argument to the work functions. This allows the work functions to communicate directly with the main
    process.

    Worker defines three variables that describe the state of a Producer or Consumer's work loop: stopped, started, and
    stop_at_queue_end.
    """
    __metaclass__ = ABCMeta

    stopped = 1
    started = 2
    stop_at_queue_end = 3

    def __init__(self):
        self.process = None
        self.result_thread = None
        self.message_thread = None
        self.work_queues = []
        self.state = Value('i', 1)
        self.result_pipe_parent, self.result_pipe_child = (None, None)
        self.message_pipe_parent, self.message_pipe_child = (None, None)
        atexit.register(self.set_stopped)
        self.work_timeout = 0
        self.max_buffer_size = 1
        self.work_args = ()
        self.work_kwargs = {}

    def get_state(self):
        """
        Get Worker state.

        Returns
        -------
        Worker state
        """
        return self.state.value

    def start_new(self, work_args=(), work_kwargs=None):
        """
        Start a new worker process passing the abstract method work_loop as the target.

        New instances of result_pipe and message_pipe are also created, and new threads are started to wait on them.

        Parameters
        ----------
        work_args: tuple
            args to pass to the work function
        work_kwargs: dict
            kwargs to pass to the work function
        """
        if work_kwargs is None:
            work_kwargs = {}
        if self.process is not None:
            self.set_stopped()
            while self.process.is_alive():
                time.sleep(0)

        self.result_pipe_parent, self.result_pipe_child = Pipe()
        self.message_pipe_parent, self.message_pipe_child = Pipe()
        self.state.value = Worker.started
        self.process = Process(target=self.work_loop,
                               args=(self.work, self.on_start, self.on_stop, self.state, self.work_queues,
                                     (*self.work_args, *work_args), {**self.work_kwargs, **work_kwargs},
                                     self.result_pipe_child, self.message_pipe_child, self.work_timeout, self.max_buffer_size))
        self.process.start()
        self.result_thread = Thread(target=self.wait_on_result_pipe, daemon=True)
        self.result_thread.start()
        self.message_thread = Thread(target=self.wait_on_message_pipe, daemon=True)
        self.message_thread.start()

    @staticmethod
    @abstractmethod
    def work_loop(*args, **kwargs):
        """
        Static method passed as the target for the process in start_new. Implemented by Producer and Consumer.

        Parameters
        ----------
        args
        kwargs
        """
        pass

    @staticmethod
    @abstractmethod
    def work(*args, **kwargs):
        """
        Static method representing the actual work function for a class derived from Producer or Consumer.

        Parameters
        ----------
        args
        kwargs
        """
        pass

    @staticmethod
    def on_start(state, message_pipe, *args, **kwargs):
        """
        Static method representing a function to be called once when a work loop is started.

        Parameters
        ----------
        state
        message_pipe
        args
        kwargs
        """
        pass

    @staticmethod
    def on_stop(on_start_result, state, message_pipe, *args, **kwargs):
        """
        Static method representing a function to be called once when a work loop is stopped.

        Parameters
        ----------
        on_start_result
        state
        message_pipe
        args
        kwargs
        """
        pass

    def set_stopped(self):
        """
        Stop the work loop by setting the worker state to stopped.
        """
        self.state.value = Worker.stopped

    def wait_on_result_pipe(self):
        """
        Loop waiting on data from the result pipe. Calls on_result_ready when data is received.

        Returns when an error occurs (indicating that the paired process has ended).
        """
        while 1:
            try:
                result = self.result_pipe_parent.recv()
                self.on_result_ready(result)
            except (EOFError, AssertionError, pickle.UnpicklingError, BrokenPipeError):
                return

    def wait_on_message_pipe(self):
        """
        Loop waiting on data from the result pipe. Calls on_message_ready when data is received.

        Returns when an error occurs (indicating that the paired process has ended).
        """
        while 1:
            try:
                message = self.message_pipe_parent.recv()
                self.on_message_ready(message)
            except (EOFError, AssertionError, pickle.UnpicklingError, BrokenPipeError):
                return

    def on_result_ready(self, result):
        """
        Method that can optionally be overloaded with a callback for when a result is received from the result pipe.

        Parameters
        ----------
        result
        """
        pass

    def on_message_ready(self, message):
        """
        Method that can optionally be overloaded with a callback for when a message is received from the message pipe.

        Parameters
        ----------
        message
        """
        pass


def put_in_queue(queue, data):
    """
    An interface to put an item into a Consumer's work queue from the main process. This is defined instead of simply
    using queue.put in case queue items in adv_prodcon ever need to be wrapped in a dict with the data plus a command.

    Parameters
    ----------
    queue
    data
    """
    queue.put(data)


class Producer(Worker):
    """
    The metaclass defining adv_prodcon's Producer. A Producer is a worker that runs its work function in a loop, and
    puts the results into each of a list of subscriber Queues.

    """
    __metaclass__ = ABCMeta

    def __init__(self, subscriber_queues=None, work_timeout=0):
        """
        Initialize the Producer. subscriber_queues is a list of queues into which the results of the work function
        should be put. work_timeout specifies the time in seconds between work function calls. If set to 0, the work
        function will be called as frequently as possible.

        Parameters
        ----------
        subscriber_queues
        work_timeout
        """
        super().__init__()
        self.work_queues = subscriber_queues
        self.work_timeout = work_timeout

    # set_subscribers must be called before start_new
    def set_subscribers(self, subscriber_queues):
        """
        Set the queues into which the results of the work function should be put. This must be called before start_new.

        Parameters
        ----------
        subscriber_queues
        """
        self.work_queues = subscriber_queues

    @staticmethod
    def work_loop(work, on_start, on_stop, state, work_queues,
                  work_args, work_kwargs, result_pipe, message_pipe, work_timeout, buffer_size):
        """
        Runs an infinite loop calling self.work until state is set to stopped. on_start is called at the start and
        on_stop is called at the end. self.work is called when time since last worked exceeds the work timeout.
        Results are put into each of the subscriber queues and the result pipe.

        Parameters
        ----------
        work
        on_start
        on_stop
        state
        work_queues
        work_args
        work_kwargs
        result_pipe
        message_pipe
        work_timeout
        buffer_size
        """
        # Producer does not make use of the buffer size argument
        assert buffer_size == 1
        on_start_result = on_start(state, message_pipe, *work_args, **work_kwargs)

        last_worked = time.time()
        while state.value != Worker.stopped:
            if time.time() - last_worked >= work_timeout:
                last_worked = time.time()
                result = work(on_start_result, state, message_pipe, *work_args, **work_kwargs)
                for queue in work_queues:
                    if queue.is_ready() and not (queue.full()):
                        queue.put(result)
                result_pipe.send(result)

                # sleep until it's time to work again (if there is time)
                sleep_time = max(0, work_timeout - (time.time() - last_worked) - 0.000001)
                time.sleep(sleep_time)

        result_pipe.close()

        on_stop(on_start_result, state, message_pipe, *work_args, **work_kwargs)
        if not message_pipe.closed:
            message_pipe.close()

    @staticmethod
    @abstractmethod
    def work(on_start_result, state, message_pipe, *args):
        """
        Static method representing the actual work function for a class derived from Producer.

        Parameters
        ----------
        on_start_result
        state
        message_pipe
        args
        """
        # Gets called in loop. Use self.set_stopped() to stop
        pass


class Consumer(Worker):
    """
    The metaclass defining adv_prodcon's Consumer. A Consumer is a worker which runs a loop checking for new items in
    its queue. When the correct criteria are met, Consumer runs its work function with the items from its queue as input.

    The criteria for Consumer to run its work function can be: number of items in the queue, time passed since last work,
    or state stop_at_queue_end set.

    """
    def __init__(self, work_timeout=5, max_buffer_size=1, lossy_queue=False, *args, **kwargs):
        """
        Initialize the Consumer. work_timeout specifies the time in seconds between work function calls. max_buffer_size
        specifies the max number of items in the buffer before the work function is called. lossy_queue specifies
        whether the Consumer's work_queue should be lossy.

        Parameters
        ----------
        work_timeout
        max_buffer_size
        lossy_queue
        args
        kwargs
        """
        super().__init__()
        maxsize = kwargs.pop("maxsize", 0)
        self.work_queues = [ReadyQueue(lossy=lossy_queue, maxsize=maxsize)]

        # work_timeout is the time to wait between work and the timeout for queue.get
        self.work_timeout = work_timeout
        self.max_buffer_size = max_buffer_size

    def start_new(self, work_args=(), work_kwargs=None):
        """
        Extends Worker.start_new by setting the Consumer's work_queue to ready, allowing producers to put items into
        it.

        Parameters
        ----------
        work_args
        work_kwargs
        """
        if work_kwargs is None:
            work_kwargs = {}
        self.work_queues[0].set_ready()
        super().start_new(work_args=work_args, work_kwargs=work_kwargs)

    @staticmethod
    def work_loop(work, on_start, on_stop, state, work_queues,
                  work_args, work_kwargs, result_pipe, message_pipe, work_timeout, max_buffer_size):
        """
        Runs an infinite loop calling self.work until state is set to stopped. on_start is called at the start and
        on_stop is called at the end. self.work is called when time since last worked exceeds the work timeout, or
        len(buffer) exceeds max_buffer_size, or state is set to stop_at_queue_end. Results are put into the result pipe.

        Parameters
        ----------
        work
        on_start
        on_stop
        state
        work_queues
        work_args
        work_kwargs
        result_pipe
        message_pipe
        work_timeout
        max_buffer_size
        """
        # Consumer only uses one work queue: its own
        assert len(work_queues) == 1
        work_queue = work_queues[0]

        on_start_result = on_start(state, message_pipe, *work_args, **work_kwargs)

        buffer = []

        last_worked = time.time()
        while state.value != Worker.stopped:
            try:
                # calling get and rebuffering so that we can wait and give someone else a chance to go
                # print(work_queue.qsize())
                buffer.append(work_queue.get(timeout=work_timeout))
            except Empty:
                # if we didn't get anything, check if we should be stopped
                continue

            if len(buffer) >= max_buffer_size or \
               (time.time() - last_worked) >= work_timeout or \
               state.value == Worker.stop_at_queue_end:

                last_worked = time.time()
                results = work(buffer, on_start_result, state, message_pipe, *work_args, **work_kwargs)
                buffer = []
                try:
                    result_pipe.send(results)
                except BrokenPipeError as e:
                    if state.value != Worker.stopped:
                        print(e)
                if state.value == Worker.stop_at_queue_end:
                    state.value = Worker.stopped
                    break

        work_queue.set_not_ready()
        on_stop(on_start_result, state, message_pipe, *work_args, **work_kwargs)

    @staticmethod
    @abstractmethod
    def work(items, on_start_result, state, message_pipe, *args):
        """
        Static method representing the actual work function for a class derived from Consumer.

        Parameters
        ----------
        items
        on_start_result
        state
        message_pipe
        args
        """
        # Gets called in loop. Use self.set_stopped() to stop
        pass

    def get_work_queue(self):
        """
        Gets the Consumer's work_queue.

        Returns
        -------

        """
        return self.work_queues[0]

    def set_stop_at_queue_end(self):
        """
        Sets the Consumer's state to stop_at_queue_end.

        """
        self.state.value = Worker.stop_at_queue_end


# https://stackoverflow.com/questions/66591320/python-multiprocessing-queue-child-class-losing-attributes-in-process/66607658#66607658
# There is an issue with making child classes from multiprocessing.queues.queue. This is a workaround
class ReadyQueue:
    """
    A class defining an extended multiprocessing.queues.queue. ReadyQueue implements an internal state "Ready" which
    users can check before adding items to it. The queue is cleared when ready is set to false.

    ReadyQueue also implements a "lossy" parameter. When set, if the queue is full, one item will be removed before a
    new one is placed.

    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the ReadyQueue. self._ready is initialized to false. kwarg "lossy" is used to specify whether the
        queue should be lossy. args and other kwargs are passed on to the queue.

        Parameters
        ----------
        args
        kwargs
        """
        self.lossy = kwargs.pop("lossy", False)
        self.queue = Queue(*args, **kwargs)
        self._ready = Value(ctypes.c_bool, False)

    def set_ready(self):
        """
        Sets the state to ready.

        """
        self._ready.value = True

    def set_not_ready(self):
        """
        Sets the state to not ready and clears the queue.

        """
        self._ready.value = False
        self.clear()

    def is_ready(self):
        """
        Returns self._ready.value.

        Returns
        -------

        """
        return self._ready.value

    def clear(self):
        """
        Clears the queue by calling queue.get until the Empty exception is reached.
        """
        try:
            while True:
                self.queue.get(block=False)
        except Empty:
            pass

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    def put(self, obj, block=True, timeout=None):
        """
        Puts obj in the queue. If self.lossy is true, calls self.get() first.

        Parameters
        ----------
        obj
        block
        timeout

        Returns
        -------

        """
        if self.lossy and self.full():
            self.get()
        return self.queue.put(obj, block, timeout)

    def full(self):
        return self.queue.full()

    def empty(self):
        return self.queue.empty()

    def qsize(self):
        return self.queue.qsize()
