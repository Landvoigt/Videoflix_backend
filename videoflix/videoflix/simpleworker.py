from rq import Worker


# To start rqworker:
# python manage.py rqworker --worker-class videoflix.simpleworker.SimpleWorker default


class BaseDeathPenalty(object):
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, *args, **kwargs):
        pass




class SimpleWorker(Worker):
    death_penalty_class = BaseDeathPenalty

    def main_work_horse(self, *args, **kwargs):
        raise NotImplementedError("Test worker does not implement this method")

    def execute_job(self, *args, **kwargs):
        """Execute job in same thread/process, do not fork()"""
        return self.perform_job(*args, **kwargs)
