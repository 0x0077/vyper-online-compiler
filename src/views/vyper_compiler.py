from vyper import compile_code
import json
import argparse


class VyperCompile:
    def __init__(self, code, evm_version):
        self.code = code
        self.evm_version = evm_version

    def vyper_compile(self):
        
        compiled_code = compile_code(self.code, ["bytecode", "abi"], evm_version=self.evm_version)
        bytecode = compiled_code["bytecode"]
        abi = compiled_code["abi"]
        
        return bytecode, abi


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile Vyper Contract")
    parser.add_argument("file_path", help="Path to the file containing Vyper code")
    parser.add_argument("evm_version", help="EVM version")
    args = parser.parse_args()

    with open(args.file_path, "r") as f:
        code = f.read()

    compiler = VyperCompile(code, args.evm_version)
    bytecode, abi = compiler.vyper_compile()

    print(json.dumps({"bytecode": bytecode, "abi": abi}))