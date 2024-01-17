from pyscript import window, document, when
from pyscript.js_modules import ethers
from pyweb import pydom
from pyodide.http import open_url, pyfetch
from js import navigator, alert, setTimeout, JSON
from collections import defaultdict
import json
import asyncio


file_code_dict = defaultdict(lambda: "default")
function_list = []
account_list = []
example_files_data = [
    "ERC20.vy",
    "ERC721.vy",
]

chain_name = {
    "1": "Ethereum Mainnet",
    "11155111": "Sepolia Network",
    "324": "zkSync Era Mainnet",
    "280": "zksync Era Testnet",
    "10": "OP Mainnet"
}

ether_unit = {
    "wei": 0,
    "ether": 18,
    "gwei": 9,
    "finney": 15
}

last_click_file_name = "contract.vy"
last_function_name = None
bytecode = None
abi = None
ganache_connect = None
ethers_connect = None
is_constructor = None
deploy_network = None


async def ganache_provider(evm):
    global ganache_connect
    global account_list
    global deploy_network

    provider = await window.initGanache(evm)
    ganache_connect = ethers.BrowserProvider.new(provider)
    acc_list = await ganache_connect.listAccounts()

    account_list = [acc.address for acc in acc_list]
    x = 0

    for acc in acc_list:
        account = acc.address
        format_account = str(account)[:7] + "..." + str(account)[35:]

        account_select_element = pydom.create("option", classes=[f"account-{str(x)}"], html=format_account)
        pydom["#customAccountSelect"][0].append(account_select_element)
        account_select_element.value = str(account)
        x += 1

    display_account = acc_list[0].address
    account_select_element = document.querySelector(".account-0")
    account_select_element.setAttribute("selected", "true")

    balance = await ganache_connect.getBalance(display_account)
    format_balance = round(balance / 10**18, 4)

    ban_element = document.querySelector(".custom-balance")
    ban_element.innerText = "Balance: " + str(format_balance) + " ETH"

    net_element = document.querySelector(".custom-network")
    net_element.innerText = "Ganache Provider"
    deploy_network = "Ganache Provider"


@when("change", "#deployEvmVersionSelector")
async def connect_wallet(event):
    global ethers_connect
    global deploy_network


    evm = event.target.value
    select_element = document.querySelector("#customAccountSelect")

    if evm in ["metamask", "paris"]:
        if not window.ethereum is None:
            select_element.options.length = 0
            provider = ethers.BrowserProvider.new(window.ethereum)
            ethers_connect = provider

            try:
                await window.ethereum.request(method="eth_requestAccounts")
                signer = await provider.getSigner()
                account = await signer.getAddress()
                balance = await provider.getBalance(account)
                format_account = str(account)[:7] + "..." + str(account)[35:]
                format_balance = round(balance / 10**18, 4)

                account_select_element = pydom.create("option", classes=[str(account)], html=format_account)
                pydom["#customAccountSelect"][0].append(account_select_element)
                account_select_element.value = str(account)

                ban_element = document.querySelector(".custom-balance")
                ban_element.innerText = "Balance: " + str(format_balance) + " ETH"

                network = await provider.getNetwork()
                net_element = document.querySelector(".custom-network")
                if chain_name[str(network.chainId)]:
                    net_element.innerText = chain_name[str(network.chainId)]
                    deploy_network = chain_name[str(network.chainId)]
                else:
                    net_element.innerText = "EVM Network"
                    deploy_network = "EVM Network"

            except Exception as e:
                window.console.log("User denied account access", e)

        else:
            window.console.log("MetaMask not installed")

    elif evm in ["shanghai", "istanbul", "berlin"]:
        select_element.options.length = 0
        await ganache_provider(evm)


caddr = None

@when("click", ".deploy-contract-btn")
async def deploy_contract(event):
    global caddr

    evm_select = document.querySelector(".custom-network")
    account_select = document.querySelector("#customAccountSelect")
    all_params = document.querySelectorAll(".display-f-input")
    input_value_element = document.querySelector(".value-text input")
    unit_type_element = document.querySelector("#etherUnit")

    value = input_value_element.value if input_value_element.value != "" else 0
    gas_limit = 3000000
    unit_type = unit_type_element.value

    value = int(value) * 10 ** ether_unit[unit_type]

    pml = []
    if is_constructor:
        pml = [pm.value for pm in all_params]

    if evm_select.innerText == "Ganache Provider":
        acc_index = account_list.index(account_select.value)
        singer = await ganache_connect.getSigner(acc_index)

        factory = ethers.ContractFactory.new(abi, bytecode, singer)
        contract = await factory.deploy(*pml, gasLimit=gas_limit, value=value)
        window.console.log(f"Contract Address: {contract.target}")
        caddr = contract.target

        await contract.waitForDeployment()
        window.console.log("Deployed!!!")
        
        # contract_file_name = document.
        dnet = document.querySelector("#deployNetwork")
        dnet.innerText = deploy_network
        cname = document.querySelector("#deployedContractName")
        cname.innerText = last_click_file_name

        display_function_params(abi)



@when("click", ".compile-btn")
async def compile_code(event):
    global bytecode
    global abi
    
    vyper_version_element = document.querySelector("#versionSelector")
    evm_version_element = document.querySelector("#evmVersionSelector")
    
    vyper_version = vyper_version_element.value
    evm_version = evm_version_element.value

    params = {
        'code': str(window.editor.getValue()),
        'vyper_version': vyper_version,
        'evm_version': evm_version
    }
   
    body = json.dumps(params)
    headers = {"Content-Type": "application/json",}
    url = "http://127.0.0.1:8000/vyper/compile"

    rsp = await pyfetch(url, method="POST", headers=headers, body=body)
    if rsp.ok:
        data = await rsp.json()
        if int(data["Code"]) == 200:
            bytecode = data["Data"]["bytecode"]
            abi = data["Data"]["abi"].replace("'", "\"")

            if not pydom["#bytecodeOutputField"][0].html:
                
                # create output sidebar element
                bytecode_output_text = pydom.create("div", classes=["output-text"])
                bytecode_label = pydom.create("label", classes=["bytecode-label"], html="Bytecode")
                bytecode_output = pydom.create("textarea")
                abi_output_text = pydom.create("div", classes=["output-text"])
                abi_label = pydom.create("label", classes=["abi-label"], html="ABI")
                abi_output = pydom.create("textarea")

                # bytecode element
                pydom["#bytecodeOutputField"][0].append(bytecode_label)
                pydom["#bytecodeOutputField"][0].append(bytecode_output_text)
                bytecode_output_text.id = "bytecodeOutputText"

                pydom["#bytecodeOutputText"][0].append(bytecode_output)
                bytecode_output.type = "text"
                bytecode_output.id = "bytecodeOutput"
                bytecode_output.value = bytecode
                
                bytecode_element = document.querySelector("#bytecodeOutput")
                bytecode_element.setAttribute("readonly", "true")

                bytecode_label.style["display"] = "block"
                bytecode_output.style["display"] = "block"

                # abi element
                pydom["#abiOutputField"][0].append(abi_label)
                pydom["#abiOutputField"][0].append(abi_output_text)
                abi_output_text.id = "abiOutputText"

                pydom["#abiOutputText"][0].append(abi_output)
                abi_output.type = "text"
                abi_output.id = "abiOutput"
                abi_output.value = abi

                abi_element = document.querySelector("#abiOutput")
                abi_element.setAttribute("readonly", "true")

                construtor_param_element = document.querySelector("#defaultConstructorText")
                construtor_param_element.innerText = last_click_file_name

                display_constructor_params(abi)

                abi_label.style["display"] = "block"
                abi_output.style["display"] = "block"

                

            else:
                bytecode_element = document.querySelector("#bytecodeOutput")
                abi_element = document.querySelector("#abiOutput")
                bytecode_element.value = bytecode
                abi_element.value = abi

                construtor_param_element = document.querySelector("#defaultConstructorText")
                construtor_param_element.innerText = last_click_file_name

                display_constructor_params(abi)

        else:
            post_error(data["Msg"])
    else:
        window.console.log("error")


def display_constructor_params(abi):
    global is_constructor

    abi = json.loads(abi)
    types = [t["type"] for t in abi]

    # list constructor params
    if "constructor" in types:
        ctc_index = types.index("constructor")
        cpl = document.querySelector("#constructorParamsList")
        cpl.innerHTML = ""

        for func in abi[ctc_index]["inputs"]:
            fn = func["name"]
            ft = func["type"]

            fparams = pydom.create("div", classes=["constructor-params"])
            pydom["#constructorParamsList"][0].append(fparams)
            fparams.id = fn
            
            fname = pydom.create("span", classes=["display-fname"], html=f"{fn}:")
            function_input = pydom.create("input", classes=["display-f-input"])
            pydom[f"#{fn}"][0].append(fname)
            pydom[f"#{fn}"][0].append(function_input)

            fnid = str(fn) + "DisplayFname"
            fname.id = fnid

            fid = str(fn) + "DisplayFInput"
            function_input.type = "text" 
            function_input.id = fid

            fi_element = document.querySelector(f"#{fid}")
            fi_element.placeholder = ft

        is_constructor = True
    else:
        is_constructor = False



def display_function_params(abi):
    global function_list

    abi = json.loads(abi)
    types = [t["type"] for t in abi]

    pydom["#layerFive"][0].style["visibility"] = "visible"
    pydom["#collapseContent"][0].style["visibility"] = "visible"

    x = 0
    func_write_list = []
    func_read_list = []

    for tp in types:
        if tp == "function":
            func_state = abi[x]["stateMutability"]
            func_name = abi[x]["name"]

            if func_state in ["payable", "nonpayable"]:
                func_write_dict = {}
                func_write_dict[func_name] = {
                    "type": func_state,
                    "params": abi[x]["inputs"]
                }
                func_write_list.append(func_write_dict)

            elif func_state == "view":
                func_read_dict = {}
                func_read_dict[func_name] = {
                    "type": func_state,
                    "params": abi[x]["inputs"]
                }
                func_read_list.append(func_read_dict)
        
        x += 1

    func_write_list = sorted(func_write_list, key=lambda x: list(x.keys())[0])
    func_read_list = sorted(func_read_list, key=lambda x: list(x.keys())[0])
    func_list = func_write_list + func_read_list
    function_list = func_list

    y = 0

    for func in func_list:
        fn = list(func.keys())[0]
        fn_state = list(func.values())[0]["type"]
        fn_params = list(func.values())[0]["params"]

        if y == 0:
            func_name_list_element = pydom.create("li", classes=["fname-list", "selected"])
        else:
            func_name_list_element = pydom.create("li", classes=["fname-list"])

        pydom["#functionNamesSidebar"][0].append(func_name_list_element)
        func_name_list_element.id = "fnameList" + str(fn)

        func_name_element = pydom.create("span", classes=["fname"], html=fn)
        icon_type, func_type = ("fa-eye", "read") if fn_state == "view" else ("fa-pencil-alt", "write")
        func_name_list_element.style["cursor"] = "pointer"

        icon_element = pydom.create("i", classes=["fas", icon_type])
        pydom[f"#fnameList{str(fn)}"][0].append(func_name_element)
        pydom[f"#fnameList{str(fn)}"][0].append(icon_element)
        icon_element.id = "fnameIcon" + str(fn)

        if y == 0:
            fns = document.querySelector("#functionNamesSidebar")
            fns.value = fn

            icon_element = document.querySelector("#fnTypeIcon")
            icon_element.classList.add("fa", icon_type)
            
            ftype_content = document.querySelector(".function-type-content")
            ftype_content.innerText = func_type

            ftype = document.querySelector(".function-type")
            ftype.innerText = fn_state
            
            k = 0

            for param_input in fn_params:
                pydom["#defaultInputText"][0].style["display"] = "none"
                fn_input_element = pydom.create("div", classes=["fn-input"])
                pydom["#functionInputs"][0].append(fn_input_element)
                fn_input_element.id = "fnInput" + str(k)

                param_name = param_input["name"]
                param_type = param_input["type"]

                fn_input_label = pydom.create("label", classes=["fn-input-label"], html=f"{param_name}:")
                fn_input_text = pydom.create("input", classes=["fn-input-text"])
                
                pydom[f"#fnInput{k}"][0].append(fn_input_label)
                pydom[f"#fnInput{k}"][0].append(fn_input_text)

                fntid = str(param_name) + "DisplayParamInputText"
                fn_input_text.id = fntid
                fn_input_text_element = document.querySelector(f"#{fntid}")
                fn_input_text_element.placeholder = param_type
                k += 1

        y += 1


@when("click", "#functionNamesSidebar")
def change_function(event):
    
    fname = event.target.innerText
    fn_params = next(item[fname] for item in function_list if fname in item)

    fns = document.querySelector("#functionNamesSidebar")
    fns.value = fname

    new_fname_list_element = document.querySelector(f"#fnameList{fname}")
    fname_list_element = document.querySelectorAll(".fname-list")

    for fle in fname_list_element:
        fle.classList.remove("selected")

    if new_fname_list_element:
        new_fname_list_element.classList.add("selected")


    fn_state = fn_params["type"]
    icon_type, func_type = ("fa-eye", "read") if fn_state == "view" else ("fa-pencil-alt", "write")
    
    icon_element = document.querySelector("#fnTypeIcon")
    icon_element.className = ""
    icon_element.classList.add("fa", icon_type)

    ftype_content = document.querySelector(".function-type-content")
    ftype_content.innerText = func_type

    k = 0

    fn_input_element = document.querySelector("#functionInputs")
    fn_input_element.innerHTML = '<div class="default-input-text" id="defaultInputText">No inputs</div>'

    for param_input in fn_params["params"]:
        pydom["#defaultInputText"][0].style["display"] = "none"
        fn_input_element = pydom.create("div", classes=["fn-input"])
        pydom["#functionInputs"][0].append(fn_input_element)
        fn_input_element.id = "fnInput" + str(k)

        param_name = param_input["name"]
        param_type = param_input["type"]

        fn_input_label = pydom.create("label", classes=["fn-input-label"], html=f"{param_name}:")
        fn_input_text = pydom.create("input", classes=["fn-input-text"])
        
        pydom[f"#fnInput{k}"][0].append(fn_input_label)
        pydom[f"#fnInput{k}"][0].append(fn_input_text)

        fntid = str(param_name) + "DisplayParamInputText"
        fn_input_text.id = fntid
        fn_input_text_element = document.querySelector(f"#{fntid}")
        fn_input_text_element.placeholder = param_type
        k += 1


@when("click", ".run-function-btn")
async def call_contract(event):

    account_select = document.querySelector("#customAccountSelect")
    acc_index = account_list.index(account_select.value)
    singer = await ganache_connect.getSigner(acc_index)

    fns_element = document.querySelector("#functionNamesSidebar")
    func_name = fns_element.value

    fn_params = next(item[func_name] for item in function_list if func_name in item)
    func_type = fn_params["type"]
    method_types = ",".join([param["type"] for param in fn_params["params"]])
    method_id = f"{func_name}({method_types})"
    window.console.log(str(method_id))
    params = []

    for param_input in fn_params["params"]:
        param_name = param_input["name"]
        fntid = str(param_name) + "DisplayParamInputText"
        fn_input_text_element = document.querySelector(f"#{fntid}")
        params.append(fn_input_text_element.value)
        
    contract = ethers.Contract.new(caddr, abi, singer)
    
    if func_type == "view":
        res = await getattr(contract, method_id)(*params)
        output_element = document.querySelector("#functionsResponse")
        output_element.innerText = res
    
    else:
        tx = await getattr(contract, method_id)(*params)
        await tx.wait()








@when("click", ".files-header")
def open_files(event):
    toggle_icon = document.querySelector("#toggleIcon")
    files_list = document.querySelector(".file-tree")

    files_list.style.display = "block" if files_list.style.display == "none" else "none"

    if files_list.style.display == "none":
        toggle_icon.classList.replace('fa-chevron-down', 'fa-chevron-right')
    else:
        toggle_icon.classList.replace('fa-chevron-right', 'fa-chevron-down')


@when("click", ".file")
def load_file(event):
    global last_click_file_name
    global file_code_dict
    global example_files_data


    if last_click_file_name is None:
        last_click_file_name = "contract.vy"

    file_code_dict[last_click_file_name.lower()] = window.editor.getValue()

    file_id = event.target.id
    file_id = file_id.replace(".", "\\.")
    file_name = event.target.innerText

    files_element = document.querySelectorAll(".file")
    
    for files in files_element:
        files.classList.remove("selected")

    selected_file = document.querySelector(f"#{file_id}")
    selected_file.classList.add("selected")
    
    with open_url(f"../assets/files/{file_name}") as fl:
        file_code = fl.read()

        if file_code_dict[file_name.lower()] == "default":
            window.editor.setValue(file_code)
        else:
            window.editor.setValue(file_code_dict[file_name.lower()])

    last_click_file_name = file_name

    if file_name in example_files_data:
        folder_element = document.querySelector(".folder-name")
        nested_list = folder_element.nextElementSibling
        nested_list.classList.toggle("open")


@when("click", ".folder")
def open_folder(event):
    folder_element = document.querySelector(".folder-name")
    nested_list = folder_element.nextElementSibling
    nested_list.classList.toggle("open")




@when("click", "#bytecodeOutputField")
def copy_bytecode_output(event):
    copied_text = document.querySelector("#bytecodeOutput").value
    navigator.clipboard.writeText(copied_text).then(
        lambda _: alert("Copied!!!"),
        lambda error: window.console.log("error!!!")
    )


@when("click", "#abiOutputField")
def copy_abi_output(event):
    copied_text = document.querySelector("#abiOutput").value
    navigator.clipboard.writeText(copied_text).then(
        lambda _: alert("Copied!!!"),
        lambda error: window.console.log("error!!!")
    )


@when("click", "#deployTitle")
def open_deploy_title(event):
    compile_element = document.querySelector(".compile-sidebar")
    compile_element.style.display = "none"

    deploy_element = document.querySelector(".deploy")
    deploy_element.style.display = "block"

    compile_title_element = document.querySelector("#compileTitle")
    deploy_title_element = document.querySelector("#deployTitle")
    compile_title_element.style.color = "white"
    deploy_title_element.style.color = "#7969e6"


@when("click", "#compileTitle")
def open_compile_title(event):
    compile_element = document.querySelector(".compile-sidebar")
    compile_element.style.display = "block"

    deploy_element = document.querySelector(".deploy")
    deploy_element.style.display = "none"

    compile_title_element = document.querySelector("#compileTitle")
    deploy_title_element = document.querySelector("#deployTitle")
    compile_title_element.style.color = "#7969e6"
    deploy_title_element.style.color = "white"


@when("click", ".contract-card")
def open_card(event):
    contract_content = document.querySelector("#collapseContent")
    card_icon_element = document.querySelector("#openCardIcon")

    # if contract_content.style.display == "none":

    #     view_func = pydom.create("div", classes="view-func")
    #     pydom["#collapseContent"][0].append(view_func)
    #     view_func.id = "vf"
    #     view_func.style["display"] = "block"
    #     card_icon_element.classList.replace('fa-chevron-right', 'fa-chevron-down')
    #     contract_content.style.display = "block"

    # else:
    #     card_icon_element.classList.replace('fa-chevron-down', 'fa-chevron-right')
    #     contract_content.style.display = "none"
    





def post_error(error):
    error_element = pydom.create("div", classes=["error-post"])
    pydom["#compileSidebar"][0].append(error_element)
    error_element.id = "errorPost"

    err_text_element = pydom.create("textarea")
    pydom["#errorPost"][0].append(err_text_element)
    err_text_element.type = "text"
    err_text_element.id = "compileErrorText"
    err_text_element.value = error

    textarea = document.querySelector("#compileErrorText")
    textarea.setAttribute("readonly", "true")
    err_text_element.style["height"] = str(textarea.scrollHeight) + "px"
    err_text_element.style["resize"] = "none"
    err_text_element.style["display"] = "block"


loop = asyncio.get_event_loop()
loop.run_until_complete(ganache_provider("shanghai"))
