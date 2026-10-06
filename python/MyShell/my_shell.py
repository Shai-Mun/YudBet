import os
import sys
import subprocess
import shlex
import getpass
from datetime import datetime

# Internal environment variable containing script lookup directories (MY_PATH)
MY_PATH = [
    r"C:\temp\my_scripts",
    os.path.join(os.getcwd(), "scripts")
]

# Built-in internal commands
INNER_COMMANDS = ["exit", "cd", "set", "help", "cls", "echo", "type", "dir", "mkdir"]


def print_dir(path):
    """Formats and returns directory contents with file size and modification time."""
    directory = ""

    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)

        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            last_modified_time = os.path.getmtime(filepath)
            last_modified_time = datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
            directory += f"{filename} | Size: {file_size} bytes | Last Modified: {last_modified_time}\n"
        elif os.path.isdir(filepath):
            last_modified_time = os.path.getmtime(filepath)
            last_modified_time = datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
            directory += f"[DIR] {filename} | Last Modified: {last_modified_time}\n"

    return directory


def print_prompt():
    """Generates a custom command prompt showing user and current working directory."""
    username = getpass.getuser()
    cwd = os.getcwd()
    return f"[{username}@MyShell {cwd}]> "


def handle_internal_command(cmd_name, args):
    """Handles execution of built-in internal shell commands."""
    cmd_name = cmd_name.lower()
    output = []

    if cmd_name == "exit":
        print("Exiting MyShell. Goodbye!")
        sys.exit(0)

    elif cmd_name == "cd":
        target_dir = args[0] if args else os.path.expanduser("~")
        try:
            os.chdir(target_dir)
        except Exception as e:
            print(f"cd error: {e}")

    elif cmd_name == "set":
        if not args:
            for k, v in os.environ.items():
                output.append(f"{k}={v}")
        elif "=" in args[0]:
            k, v = args[0].split("=", 1)
            os.environ[k] = v
        else:
            output.append(f"{args[0]}={os.environ.get(args[0], '')}")

    elif cmd_name == "help":
        output.append("--- MyShell Help ---")
        output.append(f"Internal commands: {', '.join(INNER_COMMANDS)}")
        output.append("Supports external python scripts in MY_PATH, system commands, pipes (|), and redirection (>, >>, <).")

    elif cmd_name == "cls":
        os.system('cls' if os.name == 'nt' else 'clear')

    elif cmd_name == "echo":
        output.append(" ".join(args))

    elif cmd_name == "dir":
        try:
            target = args[0] if args else os.getcwd()
            output.append(print_dir(target))
        except Exception as e:
            output.append(f"dir error: {e}")

    elif cmd_name == "mkdir":
        for path_arg in args:
            try:
                target_path = os.path.abspath(path_arg)
                os.makedirs(target_path, exist_ok=True)
            except Exception as e:
                output.append(f"mkdir error: {e}")

    return "\n".join(output) if output else None


def find_script_in_my_path(script_name):
    """Searches for a Python script within directories specified in MY_PATH."""
    if not script_name.endswith('.py'):
        script_name += '.py'

    for folder in MY_PATH:
        full_path = os.path.join(folder, script_name)
        if os.path.isfile(full_path):
            return full_path
    return None


def parse_redirection(tokens):
    """
    Parses command tokens to extract I/O redirection operators (<, >, >>).
    Returns clean command tokens and file paths for stdin/stdout.
    """
    clean_tokens = []
    stdin_file = None
    stdout_file = None
    append_mode = False

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "<":
            if i + 1 < len(tokens):
                stdin_file = tokens[i + 1]
                i += 2
                continue
        elif token == ">":
            if i + 1 < len(tokens):
                stdout_file = tokens[i + 1]
                append_mode = False
                i += 2
                continue
        elif token == ">>":
            if i + 1 < len(tokens):
                stdout_file = tokens[i + 1]
                append_mode = True
                i += 2
                continue
        clean_tokens.append(token)
        i += 1

    return clean_tokens, stdin_file, stdout_file, append_mode


def execute_single_command(cmd_str, stdin_pipe=None, stdout_pipe=None):
    """Executes a single command, supporting internal commands, external scripts, and system commands."""
    tokens = shlex.split(cmd_str)
    if not tokens:
        return None

    clean_tokens, stdin_file, stdout_file, append_mode = parse_redirection(tokens)
    if not clean_tokens:
        return None

    cmd_name = clean_tokens[0]
    args = clean_tokens[1:]

    # Handle internal commands
    if cmd_name.lower() in INNER_COMMANDS:
        result_text = handle_internal_command(cmd_name, args)

        if result_text is not None:
            text_bytes = (result_text + "\n").encode('utf-8')

            # Redirection to File (> or >>)
            if stdout_file:
                mode = 'a' if append_mode else 'w'
                with open(stdout_file, mode, encoding='utf-8') as f:
                    f.write(result_text + "\n")

            # Redirection to Pipe (|)
            elif stdout_pipe == subprocess.PIPE:
                proc = subprocess.Popen(
                    [sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=None
                )
                proc.stdin.write(text_bytes)
                proc.stdin.close()
                return proc

            # Standard Console Output
            else:
                print(result_text)

        return None

    # Handle external scripts and system commands
    fin = None
    fout = None

    if stdin_file:
        fin = open(stdin_file, 'r')
    elif stdin_pipe:
        fin = stdin_pipe

    if stdout_file:
        mode = 'a' if append_mode else 'w'
        fout = open(stdout_file, mode)
    elif stdout_pipe:
        fout = stdout_pipe

    proc = None
    script_path = find_script_in_my_path(cmd_name)

    if script_path:
        cmd_args = [sys.executable, script_path] + args
        proc = subprocess.Popen(cmd_args, stdin=fin, stdout=fout, stderr=None)
    else:
        proc = subprocess.Popen(clean_tokens, stdin=fin, stdout=fout, stderr=None, shell=True)

    if stdin_file and fin:
        fin.close()
    if stdout_file and fout:
        fout.close()

    return proc


def execute_pipeline(line):
    """Splits a command line by pipes (|) and executes each stage concurrently."""
    commands = line.split("|")
    processes = []
    prev_pipe = None

    for i, cmd_str in enumerate(commands):
        is_last = (i == len(commands) - 1)
        next_pipe = subprocess.PIPE if not is_last else None

        proc = execute_single_command(
            cmd_str.strip(),
            stdin_pipe=prev_pipe,
            stdout_pipe=next_pipe
        )

        if proc:
            processes.append(proc)
            prev_pipe = proc.stdout

    # Wait for all processes in the pipeline to finish
    for p in processes:
        p.wait()


def main():
    print("Welcome to MyShell! Type 'help' for available commands.")

    # Main shell loop
    while True:
        try:
            prompt = print_prompt()
            user_input = input(prompt).strip()

            if not user_input:
                continue

            execute_pipeline(user_input)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully without exiting the shell
            print("\nUse 'exit' to exit MyShell.")
        except Exception as e:
            # Global exception handling to prevent shell crashes
            print(f"Shell Error: {e}")


if __name__ == "__main__":
    main()