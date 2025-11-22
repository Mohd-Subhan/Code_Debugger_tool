import subprocess
import tempfile

def debug_code(code):
    try:
        with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False) as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name

        compile_command = f"g++ {temp_file_path} -o temp_output.exe"
        exec_command = "temp_output.exe"

        compile_process = subprocess.run(compile_command, shell=True, capture_output=True, text=True)
        if compile_process.returncode != 0:
            return compile_process.stderr

        exec_process = subprocess.run(exec_command, shell=True, capture_output=True, text=True)
        return exec_process.stdout or exec_process.stderr
    except Exception as e:
        return str(e)