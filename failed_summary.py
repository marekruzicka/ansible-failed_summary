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
        # Keep track of potential tasks that might be rescued
        self.potential_rescued_tasks = {}

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        task_name = result.task_name
        
        # Store the task in the appropriate category
        if ignore_errors:
            self.ignored_failed_tasks.setdefault(host, []).append(task_name)
        else:
            # Store in potential_rescued_tasks first
            # We'll move to failed_tasks or rescued_failed_tasks in v2_playbook_on_stats
            self.potential_rescued_tasks.setdefault(host, []).append(task_name)

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
        
        # Process potential rescued tasks based on stats
        for host, tasks in self.potential_rescued_tasks.items():
            # Check if any tasks were rescued for this host
            if host in stats.rescued and stats.rescued[host] > 0:
                # All the potential rescued tasks for this host were actually rescued
                self.rescued_failed_tasks[host] = tasks
            else:
                # The tasks weren't rescued, so they're actual failures
                self.failed_tasks[host] = tasks

        # Helper function to calculate the alignment offset
        def get_alignment_offset(host, task_type):
            # Calculate the position where the first task should start
            # Format: "{host} | {task_type}: "
            return len(host) + 3 + len(task_type) + 2
        
        # Helper function to format task list with newlines and proper alignment
        def format_task_list(host, tasks, task_type):
            if not tasks:
                return ""
            
            # Calculate the offset for alignment
            offset = get_alignment_offset(host, task_type)
            
            # First task on the same line
            result = tasks[0]
            
            # Remaining tasks aligned to the same position as the first task
            for task in tasks[1:]:
                result += ",\n" + " " * offset + task
                
            return result

        # Display summary for critical failures.
        if self.failed_tasks:
            self._display.display("Failed hosts:")
            for host, tasks in self.failed_tasks.items():
                if tasks:  # Only display if there are actually tasks
                    task_type = "Failed tasks"
                    message = "{}{}{} | {}{}:{} {}".format(
                        RED, host, RESET, 
                        BRIGHT_GRAY, task_type, RESET, 
                        format_task_list(host, tasks, task_type)
                    )
                    self._display.display(message)
            self._display.display("")

        # Display summary for soft failures that were ignored.
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