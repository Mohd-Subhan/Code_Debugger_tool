import subprocess
import tempfile

def debug_code(code):
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name

        exec_process = subprocess.run(f"python {temp_file_path}", shell=True, capture_output=True, text=True)
        return exec_process.stdout or exec_process.stderr
    except Exception as e:
        return str(e)