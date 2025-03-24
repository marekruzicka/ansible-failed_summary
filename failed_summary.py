from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'failed_summary'

    def __init__(self):
        super(CallbackModule, self).__init__()
        # Store failures separately: critical failures and ignored failures.
        self.failed_tasks = {}
        self.ignored_failed_tasks = {}

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        task_name = result.task_name
        if ignore_errors:
            self.ignored_failed_tasks.setdefault(host, []).append(task_name)
        else:
            self.failed_tasks.setdefault(host, []).append(task_name)

    def v2_playbook_on_stats(self, stats):
        # ANSI Color codes
        RED = '\033[31m'
        YELLOW = '\033[33m'
        RESET = '\033[0m'

        # Display summary for critical failures.
        if self.failed_tasks:
            self._display.display("Failed hosts:")
            for host, tasks in self.failed_tasks.items():
                message = "{}{}{} | Failed tasks: {}".format(RED, host, RESET, ', '.join(tasks))
                self._display.display(message)
            self._display.display("")

        # Display summary for failures that were ignored.
        if self.ignored_failed_tasks:
            self._display.display("Soft failed hosts (errors ignored):")
            for host, tasks in self.ignored_failed_tasks.items():
                message = "{}{}{} | Ignored failed tasks: {}".format(YELLOW, host, RESET, ', '.join(tasks))
                self._display.display(message)
            self._display.display("")
