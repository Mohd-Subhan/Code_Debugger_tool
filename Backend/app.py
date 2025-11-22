import os
import subprocess
import tempfile
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import ast

app = Flask(__name__)
CORS(app)

@app.route('/debug', methods=['POST'])
def debug_code():
    data = request.get_json()
    code = data.get('code')
    language = data.get('language')
    user_input = data.get('user_input', "")

    if not code or not language:
        return jsonify({"error": "Code or language missing"}), 400

    output_response = execute_code(code, language, user_input)
    questions = generate_questions(code)

    try:
        tree = ast.parse(code)
        execution_steps = generate_execution_steps(tree, code)
    except SyntaxError as e:
        return jsonify({
            "output": output_response.get("output", ""),
            "error": output_response.get("error", str(e)),
            "questions": questions
        })

    return jsonify({
        "output": output_response.get("output", ""),
        "error": output_response.get("error", ""),
        "questions": questions,
        "execution_steps": execution_steps,
    })

@app.route('/autocorrect', methods=['POST'])
def auto_correct_code():
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"error": "Code missing"}), 400

    corrected_code = correct_code_using_mistral(code)

    return jsonify({
        "corrected_code": corrected_code
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

def execute_code(code, language, user_input=""):
    try:
        with tempfile.NamedTemporaryFile(suffix=f'.{language}', delete=False) as temp_file:
            temp_file.write(code.encode())
            temp_file.close()

            if language == "python":
                python_executable = sys.executable
                result = subprocess.run([python_executable, temp_file.name], input=user_input.encode(), capture_output=True, text=True)
            elif language == "cpp":
                exe_file = temp_file.name.replace('.cpp', '.exe')
                compile_result = subprocess.run(['g++', temp_file.name, '-o', exe_file], capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return {"error": compile_result.stderr}
                result = subprocess.run([exe_file], input=user_input.encode(), capture_output=True, text=True)
            elif language == "java":
                class_name = extract_java_class_name(code)
                if not class_name:
                    return {"error": "No public class found in Java code."}

                temp_dir = os.path.dirname(temp_file.name)
                java_file_name = f"{temp_dir}/{class_name}.java"

                if os.path.exists(java_file_name):
                    os.remove(java_file_name)

                os.rename(temp_file.name, java_file_name)

                if not os.path.exists(java_file_name):
                    return {"error": "Renaming failed"}

                compile_result = subprocess.run(['javac', java_file_name], capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return {"error": compile_result.stderr}

                result = subprocess.run(['java', '-cp', temp_dir, class_name], input=user_input.encode(), capture_output=True, text=True)

                if os.path.exists(java_file_name):
                    os.remove(java_file_name)
            elif language == "c":
                exe_file = temp_file.name.replace('.c', '.exe')
                compile_result = subprocess.run(['gcc', temp_file.name, '-o', exe_file], capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return {"error": compile_result.stderr}
                result = subprocess.run([exe_file], input=user_input.encode(), capture_output=True, text=True)
            else:
                return {"error": "Unsupported language"}

            os.remove(temp_file.name)
            return {"output": result.stdout if result.returncode == 0 else "", "error": result.stderr if result.returncode != 0 else ""}
    except Exception as e:
        return {"error": str(e)}

def generate_questions(code):
    try:
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "your api")
        if not MISTRAL_API_KEY or MISTRAL_API_KEY.lower() in ("your api", "your api key", "your_api_key"):
            # No valid API key configured — return an empty questions list so frontend doesn't fail
            return ["Question generation disabled: no Mistral API key configured"]
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-medium",
            "messages": [{"role": "user", "content": f"Analyze the following code and generate 5 conceptual or practical questions:\n\n{code}"}]
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            questions = result["choices"][0]["message"]["content"].strip()
            return questions.split("\n")
        elif response.status_code == 401:
            return ["Question generation unavailable: unauthorized (invalid API key)"]
        else:
            return [f"Error: {response.status_code} - {response.text}"]
    except Exception as e:
        return [f"Error generating questions: {str(e)}"]

def extract_java_class_name(code):
    import re
    match = re.search(r'public\s+class\s+(\w+)', code)
    return match.group(1) if match else None

def correct_code_using_mistral(code):
    try:
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "Your api")
        if not MISTRAL_API_KEY or MISTRAL_API_KEY.lower() in ("your api", "your api key", "your_api_key"):
            return "Auto-correct disabled: no Mistral API key configured"

        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-medium",
            "messages": [{"role": "user", "content": f"Correct the following code and improve it:\n\n{code}"}]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            corrected_code = response_data["choices"][0]["message"]["content"]
            return corrected_code.strip()
        elif response.status_code == 401:
            return "Auto-correct unavailable: unauthorized (invalid API key)"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def generate_execution_steps(tree, code):
    steps = []
    lines = code.split('\n')
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            line_no = node.lineno -1
            target = ast.unparse(node.targets[0])
            value = ast.unparse(node.value)
            steps.append({
                "lineNumber": line_no,
                "stepDescription": f"{target} = {value}"
            })
        elif isinstance(node, ast.Expr):
            line_no = node.lineno -1
            value = ast.unparse(node.value)
            steps.append({
                "lineNumber": line_no,
                "stepDescription": f"{value}"
            })
        elif isinstance(node, ast.If):
            line_no = node.lineno - 1;
            test = ast.unparse(node.test)
            steps.append({
                "lineNumber": line_no,
                "stepDescription": f"If {test}"
            })

    return steps

if __name__ == '__main__':
    app.run(debug=True)
