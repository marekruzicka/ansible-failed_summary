# Ansible Callback Plugin: Failed Summary

This Ansible callback plugin provides a concise summary of task failures at the end of a playbook run. It categorizes tasks into three groups (for each host):

- **Failed tasks:** Tasks that failed and were not rescued
- **Soft failed tasks:** Tasks that failed with ignore_errors enabled
- **Rescued tasks:** Failures that were rescued by a rescue block

![callback_failed_summary](https://github.com/user-attachments/assets/4ecb2ce7-f14d-407d-86aa-3baab7f0d7dd)

## Features
- **Customizable Output:**
    Supports optional display of *soft failures (ignore_errors)* and *rescued tasks* via internal toggles:
  - `display_ignored_errors`
    Set to `True` (default) to display soft failures (ignored errors).

  - `display_rescued_tasks`
    Set to `True` (default) to display rescued tasks.
- **ANSI Color Coding:**
    Uses ANSI escape sequences to format the summary with colors (again "configurable" within the code):

    ```python
    ...
    # ANSI Color codes
    RESET           = "\033[0m"     # reset color
    BRIGHT_GRAY     = "\033[90m"    # verbose: bright gray
    RED             = "\033[31m"    # error: red, also used for unreachable and diff_remove
    YELLOW          = "\033[33m"    # changed: yellow
    ...
    message = "{}{}{} | {}{}:{} {}".format(
        RED, host, RESET,
        BRIGHT_GRAY, task_type, RESET,
        format_task_list(host, tasks, task_type)
    )
    ...
    ```

## Installation
1. **Copy the Plugin File**
Save the provided `failed_summary.py` file into a directory of your choice. For example, create a directory named `callback_plugins` in your project.

2. **Configure Ansible to Use the Plugin**
    In your ansible.cfg file, add or modify the following lines:

    ```ini
    [defaults]
    # Set the stdout callback to default so you keep the standard output
    stdout_callback = default
    # Enable your custom plugin
    callbacks_enabled = failed_summary
    # Specify the callback plugins directory
    callback_plugins = ./callback_plugins
    ```

## Usage
Run your playbook as usual. For example:

```bash
ansible-playbook -i inventory main.yml
```
At the end of the playbook run, you will see a summary similar to (with nicer colors :)): 
```yaml
Failed hosts:
localhost | Failed tasks: Task A
                          Task B

Soft failed hosts (errors ignored):
localhost | Ignored failed tasks: Task C

Rescued failed hosts:
localhost | Rescued tasks: Rescue Task
```


### Example Playbook
```yaml
---
- name: Playbook with a task that fails and a rescue task
  hosts: localhost
  gather_facts: false

  tasks:
    - block:

        - name: This task will fail, but is ignored
          ansible.builtin.command: /bin/false
          ignore_errors: true

        - name: This task will fail but is rescued
          ansible.builtin.command: /bin/false

      rescue:
        - name: Rescue task
          ansible.builtin.debug:
            msg: "The previous task failed, executing rescue task."

    - name: Another ignored error task
      ansible.builtin.command: /bin/false
      ignore_errors: true

    - name: This will fail for good
      ansible.builtin.command: /bin/false

```


