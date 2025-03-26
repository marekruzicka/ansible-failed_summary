# Ansible Callback Plugin: Failed Summary

This Ansible callback plugin provides a concise summary of task failures at the end of a playbook run. It categorizes tasks into three groups (for each host):

- **Failed tasks:** Tasks that failed and were not rescued
- **Soft failed tasks:** Tasks that failed with ignore_errors enabled
- **Rescued tasks:** Failures that were rescued by a rescue block

![callback_failed_summary](https://github.com/user-attachments/assets/4ecb2ce7-f14d-407d-86aa-3baab7f0d7dd)

## Features
### 1. Customizable Output

Supports optional display of soft failures *(ignore_errors)* and rescued tasks, and customizable output mode (JSON vs. formatted text) via:

**environment variables** (or internal toggles)
  - `ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_IGNORED_ERRORS` (maps to *display_ignored_errors*)
    - **Purpose**: Controls the display of soft failures (ignored errors)
    - **Usage**: Set to `True` or `False` (default `True`)

  - `ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_RESCUED_TASKS` (maps to *display_rescued_tasks*)
    - **Purpose**: Controls the display of rescued tasks (error rescued within a block of tasks)
    - **Usage**: Set to `True` or `False` (default `True`) 

  - `ANSIBLE_CALLBACK_FAILED_SUMMARY_OUTPUT_JSON` (maps to *json_output*)
    - **Purpose**: Controls the output mode (JSON vs. formatted text)
    - **Usage**: Set to `True` or `False` (default `False`)

### 2. ANSI Color Coding

The summary uses ANSI escape sequences for colored text. This color coding is configurable directly in the code.

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
Run your playbook as usual with plugin default settings:

```bash
ansible-playbook -i inventory main.yml

PLAY RECAP ***********************************************************************************************************************************************
localhost                  : ok=4    changed=3    unreachable=0    failed=0    skipped=1    rescued=1    ignored=2   
vm                         : ok=3    changed=2    unreachable=0    failed=1    skipped=0    rescued=1    ignored=2   

Failed hosts:
vm | Failed tasks: This will fail for good

Soft failed hosts (errors ignored):
vm | Ignored failed tasks: This task will fail, but is ignored,
                           Another ignored error task
localhost | Ignored failed tasks: This task will fail, but is ignored,
                                  Another ignored error task

Rescued hosts:
localhost | Rescued failed tasks: This task will fail but is rescued
vm | Rescued failed tasks: This task will fail but is rescued

```

Or configure the plugin output as desired:
``` bash
ANSIBLE_CALLBACK_FAILED_SUMMARY_OUTPUT_JSON=true \
ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_IGNORED_ERRORS=false \
ANSIBLE_CALLBACK_FAILED_SUMMARY_DISPLAY_RESCUED_TASKS=false  \
ansible-playbook -i inventory main.yml

PLAY RECAP ***********************************************************************************************************************************************
localhost                  : ok=4    changed=3    unreachable=0    failed=0    skipped=1    rescued=1    ignored=2   
vm                         : ok=3    changed=2    unreachable=0    failed=1    skipped=0    rescued=1    ignored=2   

{
  "failed_tasks": {
    "vm": [
      "This will fail for good"
    ]
  }
}
```

### Example Playbook
```ini
# inventory
localhost
vm ansible_ssh_host=localhost
```
```yaml
# main.yml
---
- name: Playbook with a task that fails and a rescue task
  hosts: all
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
      when: inventory_hostname == "vm"
    
    - name: Success task
      ansible.builtin.command: /bin/true

```


