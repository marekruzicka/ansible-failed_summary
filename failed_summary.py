from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'failed_summary'


    # Toggle to enable/disable displaying ignored errors.
    display_ignored_errors = True


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
        RESET = '\033[0m'

        WHITE          = "\033[37m"  # highlight: white
        BRIGHT_GRAY    = "\033[90m"  # verbose: bright gray
        BRIGHT_PURPLE  = "\033[95m"  # warn: bright purple
        RED            = "\033[31m"  # error: red, also used for unreachable and diff_remove
        DARK_GRAY      = "\033[90m"  # debug: dark gray (using the same as bright gray here)
        PURPLE         = "\033[35m"  # deprecate: purple
        CYAN           = "\033[36m"  # skip: cyan, also used for diff_lines
        GREEN          = "\033[32m"  # ok: green, also used for diff_add
        YELLOW         = "\033[33m"  # changed: yellow
        BLUE           = "\033[34m"  # task: blue

        # Display summary for critical failures.
        if self.failed_tasks:
            self._display.display("Failed hosts:")
            for host, tasks in self.failed_tasks.items():
                message = "{}{}{} | {}Failed tasks: {}{}".format(RED, host, RESET, BRIGHT_GRAY, RESET, ', '.join(tasks))
                self._display.display(message)
            self._display.display("")

        # Display summary for soft failures that were ignored.
        if self.ignored_failed_tasks and self.display_ignored_errors:
            self._display.display("Soft failed hosts (errors ignored):")
            for host, tasks in self.ignored_failed_tasks.items():
                message = "{}{}{} | {}Ignored failed tasks: {}{}".format(YELLOW, host, RESET, BRIGHT_GRAY, RESET, ', '.join(tasks))
                self._display.display(message)
            self._display.display("")
