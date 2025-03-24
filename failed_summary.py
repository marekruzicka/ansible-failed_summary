from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'failed_summary'

    # Toggle to enable/disable displaying ignored errors.
    display_ignored_errors = True
    # Toggle to enable/disable displaying rescued tasks.
    display_rescued_tasks = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        # Store failures separately: critical failures, ignored failures, and rescued failures.
        self.failed_tasks = {}
        self.ignored_failed_tasks = {}
        self.rescued_failed_tasks = {}
        # Keep track of potential tasks that might be rescued.
        self.potential_rescued_tasks = {}

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        task_name = result.task_name

        # Store the task in the appropriate category.
        if ignore_errors:
            self.ignored_failed_tasks.setdefault(host, []).append(task_name)
        else:
            # For non-ignored failures, add them to a temporary list.
            self.potential_rescued_tasks.setdefault(host, []).append(task_name)

    def v2_playbook_on_stats(self, stats):
        # ANSI Color codes
        RESET           = "\033[0m"     # reset color
        WHITE           = "\033[37m"    # highlight: white
        BRIGHT_GRAY     = "\033[90m"    # verbose: bright gray
        BRIGHT_PURPLE   = "\033[95m"    # warn: bright purple
        RED             = "\033[31m"    # error: red, also used for unreachable and diff_remove
        DARK_GRAY       = "\033[90m"    # debug: dark gray (using the same as bright gray here)
        PURPLE          = "\033[35m"    # deprecate: purple
        CYAN            = "\033[36m"    # skip: cyan, also used for diff_lines
        GREEN           = "\033[32m"    # ok: green, also used for diff_add
        YELLOW          = "\033[33m"    # changed: yellow
        BLUE            = "\033[34m"    # task: blue

        # Process potential rescued tasks based on stats.
        for host, tasks in self.potential_rescued_tasks.items():
            # Determine how many tasks were rescued for this host.
            rescued_count = stats.rescued.get(host, 0)
            # Partition the tasks list: first rescued_count tasks are considered rescued.
            rescued_tasks = tasks[:rescued_count]
            failed_tasks = tasks[rescued_count:]
            if rescued_tasks:
                self.rescued_failed_tasks[host] = rescued_tasks
            if failed_tasks:
                self.failed_tasks[host] = failed_tasks

        # Helper function to calculate the alignment offset.
        def get_alignment_offset(host, task_type):
            # Format: "{host} | {task_type}: "
            return len(host) + 3 + len(task_type) + 2

        # Helper function to format a task list with proper alignment.
        def format_task_list(host, tasks, task_type):
            if not tasks:
                return ""
            offset = get_alignment_offset(host, task_type)
            result = tasks[0]
            for task in tasks[1:]:
                result += ",\n" + " " * offset + task
            return result

        # Display summary for critical (non-rescued) failures.
        if self.failed_tasks:
            self._display.display("Failed hosts:")
            for host, tasks in self.failed_tasks.items():
                if tasks:
                    task_type = "Failed tasks"
                    message = "{}{}{} | {}{}:{} {}".format(
                        RED, host, RESET,
                        BRIGHT_GRAY, task_type, RESET,
                        format_task_list(host, tasks, task_type)
                    )
                    self._display.display(message)
            self._display.display("")

        # Display summary for soft failures (ignored errors).
        if self.ignored_failed_tasks and self.display_ignored_errors:
            self._display.display("Soft failed hosts (errors ignored):")
            for host, tasks in self.ignored_failed_tasks.items():
                task_type = "Ignored failed tasks"
                message = "{}{}{} | {}{}:{} {}".format(
                    YELLOW, host, RESET,
                    BRIGHT_GRAY, task_type, RESET,
                    format_task_list(host, tasks, task_type)
                )
                self._display.display(message)
            self._display.display("")

        # Display summary for rescued failures.
        if self.rescued_failed_tasks and self.display_rescued_tasks:
            self._display.display("Rescued hosts:")
            for host, tasks in self.rescued_failed_tasks.items():
                task_type = "Rescued failed tasks"
                message = "{}{}{} | {}{}:{} {}".format(
                    CYAN, host, RESET,
                    BRIGHT_GRAY, task_type, RESET,
                    format_task_list(host, tasks, task_type)
                )
                self._display.display(message)
            self._display.display("")
