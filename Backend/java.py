import subprocess
import tempfile
import os

def debug_code(code):
    try:
        # Clean up any old temp files or compiled class files before starting
        cleanup_temp_files()

        # Create a temporary Java file and write code to it
        with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name

        # Extract the class name from the Java code
        class_name = extract_java_class_name(code)
        if not class_name:
            return "Class name not found in the Java code."

        # Define the renamed file path
        renamed_file_path = os.path.join(os.path.dirname(temp_file_path), f"{class_name}.java")
        
        # Rename the temporary file to match the class name (without .java)
        os.rename(temp_file_path, renamed_file_path)

        # Ensure the file exists before attempting to compile
        if not os.path.exists(renamed_file_path):
            return f"Error: The file {renamed_file_path} does not exist."

        # Compile the Java code
        compile_command = f"javac {renamed_file_path}"
        compile_process = subprocess.run(compile_command, shell=True, capture_output=True, text=True)
        if compile_process.returncode != 0:
            return compile_process.stderr

        # Run the Java code (without .java extension)
        exec_command = f"java -cp {os.path.dirname(renamed_file_path)} {class_name}"
        exec_process = subprocess.run(exec_command, shell=True, capture_output=True, text=True)

        # Clean up the temporary files after execution
        cleanup_temp_files()  # Clean-up all temp and compiled files

        # Return the output or error from the execution
        return exec_process.stdout or exec_process.stderr
    except Exception as e:
        return str(e)

def extract_java_class_name(code):
    for line in code.split("\n"):
        if "public class" in line:
            return line.split()[2].strip()
    return None

def cleanup_temp_files():
    """
    Clean up old temporary files and compiled Java class files.
    """
    # Check if there are old files in the system's temp directory and remove them
    temp_dir = os.path.join(os.getenv("TEMP"), "tmp")  # Temporary directory
    if os.path.exists(temp_dir):
        # List all files in temp directory and remove the Java and class files
        for filename in os.listdir(temp_dir):
            if filename.endswith(".java") or filename.endswith(".class"):
                try:
                    os.remove(os.path.join(temp_dir, filename))
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
    else:
        print("No temporary directory found to clean.")