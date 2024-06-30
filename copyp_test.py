#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from netmiko import ConnectHandler
import time
import json

def run_module():
    module_args = dict(
        commands=dict(type='list', required=True),
        output_file=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
        original_message='',
        message=[],
        time_json={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    start_time = time.time()  # Start timing module execution

    if module.check_mode:
        module.exit_json(**result)

    commands = module.params['commands']
    output_file = module.params.get('output_file')

    device = {
        'device_type': 'cisco_asa',
        'host': module.params['ansible_host'],
        'username': module.params['ansible_user'],
        'password': module.params['ansible_password'],
        'global_delay_factor': 2,  # Adjust delay factor if needed
    }

    try:
        connection = ConnectHandler(**device)

        # Disable paging on the device
        connection.send_command('terminal pager 0')

        for command in commands:
            command_result = {}
            output = []
            try:
                # Capture the prompt before sending the command
                prompt = connection.find_prompt()

                # Measure start time for command execution
                command_start_time = time.time()

                # Special handling for 'copy' command
                if command.startswith('copy'):
                    output.append(f"Executing command: {command}")
                    output.append(connection.send_command_timing(command, strip_prompt=False, strip_command=False))

                    # Handle standard prompts for 'copy' command
                    max_wait_time = 7200  # Maximum wait time of 2 hours in seconds
                    start_copy_time = time.time()

                    while True:
                        partial_output = connection.send_command_timing('\n', strip_prompt=False, strip_command=False)
                        output.append(partial_output)
                        if 'Source filename' in partial_output:
                            output.append(connection.send_command_timing('\n', strip_prompt=False, strip_command=False))
                        elif 'Destination filename' in partial_output:
                            output.append(connection.send_command_timing('\n', strip_prompt=False, strip_command=False))
                        elif 'Confirm' in partial_output:
                            output.append(connection.send_command_timing('\n', strip_prompt=False, strip_command=False))
                            break
                        elif 'bytes copied' in partial_output:
                            break
                        elif 'Error' in partial_output:
                            raise ValueError(f"Error occurred during file copy: {partial_output}")

                        # Check if maximum wait time has been exceeded
                        elapsed_time = time.time() - start_copy_time
                        if elapsed_time > max_wait_time:
                            raise TimeoutError("File copy did not complete within the maximum wait time of 2 hours.")

                        time.sleep(5)  # Check every 5 seconds
                else:
                    # Regular command handling
                    command_output = connection.send_command(command, expect_string=prompt)
                    output.extend(command_output.splitlines())

                # Measure end time for command execution
                command_end_time = time.time()
                command_execution_time = round(command_end_time - command_start_time, 2)

                # Store command result
                command_result['command'] = command
                command_result['output'] = output
                command_result['execution_time'] = command_execution_time

                # Append command result to message list
                result['message'].append(command_result)

            except Exception as e:
                output.append(str(e))

            # Convert all items in output to strings to ensure compatibility
            output = [str(item) for item in output]

        result['changed'] = True

    except Exception as e:
        module.fail_json(msg=str(e))

    finally:
        connection.disconnect()
        end_time = time.time()  # End timing module execution
        total_time_taken = round(end_time - start_time, 2)  # Calculate total time taken
        result['time_json'] = {'total_time_taken': total_time_taken}  # Add time taken to result

        # Write the collected output to the specified file if defined
        if output_file:
            file_extension = os.path.splitext(output_file)[1].lower()
            with open(output_file, 'w') as f:
                if file_extension == '.json':
                    json.dump(result['message'], f, indent=4)  # Write command results in JSON format
                else:
                    for cmd_result in result['message']:
                        f.write(f"Command: {cmd_result['command']}\n")
                        f.write("\n".join(cmd_result['output']))
                        f.write(f"\nExecution Time: {cmd_result['execution_time']} seconds\n\n")

        module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
