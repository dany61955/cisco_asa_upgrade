import paramiko
import time
import json
import os

def execute_command(shell, command, wait_time=1):
    shell.send(command + '\n')
    time.sleep(wait_time)
    output = shell.recv(65535).decode('utf-8')
    return output

def main():
    result = {
        "success": True,
        "output": ""
    }
    
    # Device credentials
    asa_ip = "x.x.x.x"
    asa_username = "asa_user"
    asa_password = "asa_password"
    
    fxos_username = "fxos_user"
    fxos_password = "fxos_password"

    # Commands to execute
    commands = [
        "connect fxos",
        fxos_username,
        fxos_password,
        "scope security",
        "show"
    ]
    
    # Create an SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the ASA device
        ssh_client.connect(asa_ip, username=asa_username, password=asa_password)
        
        # Invoke an interactive shell session on the remote device
        shell = ssh_client.invoke_shell()
        time.sleep(1)  # Wait for the shell to be ready
        
        # Execute each command in the list
        for command in commands:
            output = execute_command(shell, command, wait_time=2)
            result["output"] += output
        
    except paramiko.AuthenticationException:
        result["success"] = False
        result["output"] = "Authentication failed, please verify your credentials"
    except paramiko.SSHException as sshException:
        result["success"] = False
        result["output"] = f"Unable to establish SSH connection: {sshException}"
    except Exception as e:
        result["success"] = False
        result["output"] = f"Operation error: {e}"
    finally:
        # Close the connection
        ssh_client.close()
        
        # Write output to a file
        with open('/path/to/output.txt', 'w') as file:
            file.write(result["output"])
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
