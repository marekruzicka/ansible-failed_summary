from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
import json
import os


env_debug = os.environ.get("ANSIBLE_CALLBACK_FAILED_SUMMARY_DEBUG")
if env_debug and env_debug.strip():
    import debugpy
    debugpy.listen(("localhost", 5678))
    print("Waiting for debugger to attach...")
    debugpy.wait_for_client()

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'failed_summary'

    # Toggle to enable/disable displaying ignored errors and rescued tasks
    display_ignored_errors = True
    display_rescued_tasks = True

    env_ignored_errors = os.environ.get("ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_IGNORED_ERRORS")
    if env_ignored_errors:
        display_ignored_errors = env_ignored_errors.lower() == "true"

    env_rescued_tasks = os.environ.get("ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_RESCUED_TASKS")
    if env_rescued_tasks:
        display_rescued_tasks = env_rescued_tasks.lower() == "true"

    def __init__(self):
        super(CallbackModule, self).__init__()
        # Store failures separately
        self.failed_tasks = {}
        self.ignored_failed_tasks = {}
        self.rescued_failed_tasks = {}
        self.potential_rescued_tasks = {}

        # Default output is formatted text
        self.json_output = False  
        # Check the environment variable for output mode and override the default
        env_output = os.environ.get("ANSIBLE_CALLBACK_FAILED_SUMMARY_OUTPUT_JSON")
        if env_output:
            self.json_output = env_output.lower() == "true"

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        task_name = result.task_name

        if ignore_errors:
            self.ignored_failed_tasks.setdefault(host, []).append(task_name)
        else:
            self.potential_rescued_tasks.setdefault(host, []).append(task_name)

    def v2_playbook_on_stats(self, stats):
        # Process potential rescued tasks
        for host, tasks in self.potential_rescued_tasks.items():
            rescued_count = stats.rescued.get(host, 0)
            rescued_tasks = tasks[:rescued_count]
            failed_tasks = tasks[rescued_count:]
            if rescued_tasks:
                self.rescued_failed_tasks[host] = rescued_tasks
            if failed_tasks:
                self.failed_tasks[host] = failed_tasks

        # If JSON output is enabled, build a summary dictionary accordingly
        if self.json_output:
            summary = {
                "failed_tasks": self.failed_tasks
            }
            # Only include ignored_failed_tasks if display is enabled
            if self.display_ignored_errors:
                summary["ignored_failed_tasks"] = self.ignored_failed_tasks
            # Only include rescued_failed_tasks if display is enabled
            if self.display_rescued_tasks:
                summary["rescued_failed_tasks"] = self.rescued_failed_tasks

            self._display.display(json.dumps(summary, indent=2))
            return

        # Check the output mode: JSON vs. formatted text
        if self.json_output:
            # Output summary as JSON
            self._display.display(json.dumps(summary, indent=2))
            return

        # ANSI color codes for formatted text output
        RESET           = "\033[0m"
        WHITE           = "\033[37m"
        BRIGHT_GRAY     = "\033[90m"
        BRIGHT_PURPLE   = "\033[95m"
        RED             = "\033[31m"
        DARK_GRAY       = "\033[90m"
        PURPLE          = "\033[35m"
        CYAN            = "\033[36m"
        GREEN           = "\033[32m"
        YELLOW          = "\033[33m"
        BLUE            = "\033[34m"

        # Helper function to calculate the alignment offset
        def get_alignment_offset(host, task_type):
            return len(host) + 3 + len(task_type) + 2

        # Helper function to format a task list with proper alignment
        def format_task_list(host, tasks, task_type):
            if not tasks:
                return ""
            offset = get_alignment_offset(host, task_type)
            result = tasks[0]
            for task in tasks[1:]:
                result += ",\n" + " " * offset + task
            return result

        # Display summary for critical (non-rescued) failures
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

        # Display summary for soft failures (ignored errors)
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

        # Display summary for rescued failures
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
