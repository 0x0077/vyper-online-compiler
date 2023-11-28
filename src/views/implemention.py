import vyper.exceptions
from sanic.response import json, html
from sanic import Blueprint
import re
import json as file_json
import time
import os
import subprocess
import tempfile


imp = Blueprint("vyper", url_prefix="vyper")

def switch_env_compiler(version, script_path, code, evm_version):

    try:
        env_name = f"vyper{version.replace('.', '')}"

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
            tmpfile.write(code)
            tmpfile.flush()
            tmpfile_path = tmpfile.name

        # /home/djuser/anaconda3/condabin/conda
        command = ["conda", "run", "-n", env_name, "python", script_path, tmpfile_path, evm_version]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            # print(result.stdout)
            return file_json.loads(result.stdout)
        else:
            raise Exception(f"Error compiling Vyper code: {result.stderr}")
    
    
    finally:
        os.remove(tmpfile_path)


@imp.route("/compile", methods=["POST"])
async def compile_vyper_code(request):

    code = request.json.get("code")
    evm_version = request.json.get("evm_version")
    vyper_version = request.json.get("vyper_version")
    
    with open("./views/evmVersion.json", "r") as f:
        evm_versions = file_json.loads(f.read())
    
    # # default evm version
    # evm_version = "shanghai"

    evm_version = evm_version if evm_version in evm_versions["evm_version"] else "shanghai"
  
    if not code:
        return json({"error": "No code provided"})

    try:
        script_path = "./views/vyper_compiler.py"

        compiled_code = switch_env_compiler(vyper_version, script_path, code, evm_version)

        data = {
            "Code": 200,
            "Time": time.strftime("%Y.%m.%d %H:%M:%S", time.localtime()),
            "Msg": "succes",
            "Data": {
                "bytecode": str(compiled_code["bytecode"]),
                "abi": str(compiled_code["abi"])
            }
        }


    except Exception as e:
        err_name = str(e.__class__.__name__)
        match = re.search(r"vyper.exceptions.\w+: (.*?)(?=\n\n|\Z)", str(e), re.DOTALL)
        if match:
            specific_error_message = match.group(1).strip()
            error_output = f"[Compiler Error] vyper.exceptions.{err_name} {specific_error_message}"
        else:
            error_output = "An unknown error occurred during compilation"

        data = {
            "Code": 400,
            "Time": time.strftime("%Y.%m.%d %H:%M:%S", time.localtime()),
            "Msg": error_output,
            "Data": {}
        }

    return json(data)
