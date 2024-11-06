import subprocess
import os

def input_default(prompt, default_value):
    result = input(prompt)
    return result if result.strip() else default_value

def run_command(command, input_text=None, suppress_output=False):
    try:
        stdout = subprocess.PIPE if not suppress_output else open(os.devnull, 'w')
        stderr = subprocess.PIPE if not suppress_output else open(os.devnull, 'w')

        # Execute the command
        result = subprocess.run(command, input=input_text, check=True, stdout=stdout, stderr=stderr, text=True)

        if not suppress_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

        return result
    except subprocess.CalledProcessError as e:
        # Returns error information when an error occurs during command execution
        error_message = f"Command '{' '.join(command)}' returned non-zero exit status {e.returncode}."
        if e.stdout:
            error_message += f"\nOutput: {e.stdout}"
        if e.stderr:
            error_message += f"\nError: {e.stderr}"
        print(f"********************\nError executing command: {error_message}\n********************")
        return None
    except Exception as e:
        # Catch other errors and return None
        print(f"********************\nError executing command: {str(e)}\n********************")
        return None

