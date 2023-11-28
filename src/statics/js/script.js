
let compiledAbi = null;
let compiledBytecode = null;

async function connectWallet() {
    const button = document.getElementById('connectWallet');
    if (window.ethereum) {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            button.textContent = accounts[0].substring(0, 6) + '...' + accounts[0].substring(accounts[0].length - 4);
            button.onclick = disconnectWallet;
        } catch (error) {
            console.error("User denied account access");
        }
    } else {
        alert("Please install MetaMask!");
    }
}

function disconnectWallet() {
    const button = document.getElementById('connectWallet');
    button.textContent = 'Connect Wallet';
    button.onclick = connectWallet;
}


async function deployContract(abi, bytecode, constructorArgs) {
    document.getElementById('loadingIndicator').style.display = 'inline-block';

    const provider = new ethers.providers.Web3Provider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    const signer = provider.getSigner();

    const contractFactory = new ethers.ContractFactory(abi, bytecode, signer);
    const contract = await contractFactory.deploy(...constructorArgs);

    await contract.deployed();

    document.getElementById('contractAddress').value = contract.address;
    document.getElementById('contractAddressContainer').style.display = 'block';
    document.getElementById('loadingIndicator').style.display = 'none';

    const inputs = document.querySelectorAll('#constructorParams input');
    inputs.forEach(input => input.value = '');

    // 隐藏构造函数参数的显示区域
    document.getElementById('constructorParamsContainer').style.display = 'none';

    // 清空bytecode和abi数据
    document.getElementById('bytecodeOutput').value = '';
    document.getElementById('abiOutput').value = '';

    const successModal = document.createElement('div');
    successModal.id = 'successModal';
    successModal.innerHTML = `
      <p>Contract deployed at: ${contract.address}</p>
      <button onclick="this.parentElement.style.display='none'">Close</button>
    `;
    document.body.appendChild(successModal);
    setTimeout(() => successModal.style.display = 'block', 100); 
    setTimeout(() => successModal.style.display = 'none', 60000);
}



function compileContract(code, vyperVersion, evmVersion) {
    const data = {
        code: code,
        vyper_version: vyperVersion,
        evm_version: evmVersion
    };

    fetch('http://127.0.0.1:8000/vyper/compile', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Compiled:', data);
        if (data.Code === 200 && data.Msg === 'succes') {
            compiledBytecode = data.Data.bytecode;
            compiledAbi = data.Data.abi;
            compiledAbi = compiledAbi.replace(/'/g, '"');
            compiledAbi = JSON.parse(compiledAbi);

            displayConstructorParams(compiledAbi);

            document.getElementById('bytecodeOutput').value = data.Data.bytecode;
            document.getElementById('abiOutput').value = data.Data.abi;

        } else {
            openModal(data.Msg)
        }
    });

}


function openModal(message) {
    document.getElementById('errorText').innerText = message;
    document.getElementById('errorModal').style.display = 'block';
    document.getElementById('errorModal').style.transform = 'translateX(0)';

    setTimeout(closeModal, 60000);
}


function closeModal() {
    var errorModal = document.getElementById('errorModal');
    if (errorModal.style.display === 'block') {
        errorModal.style.transform = 'translateX(100%)';
        setTimeout(() => {
            errorModal.style.display = 'none';
        }, 300); 
    }
}


function displayConstructorParams(abi) {
    const constructorAbi = abi.find(element => element.type === 'constructor');
    const container = document.getElementById('constructorParams');
    container.innerHTML = ''; 

    if (constructorAbi && constructorAbi.inputs.length > 0) {
        const title = document.createElement('h4');
        title.textContent = 'constructor:';
        container.appendChild(title);

        constructorAbi.inputs.forEach(input => {
            const label = document.createElement('label');
            label.textContent = input.name + ': ';
            const inputField = document.createElement('input');
            inputField.type = 'text';
            inputField.placeholder = input.type;
            container.appendChild(label);
            container.appendChild(inputField);
        });

        document.getElementById('constructorParamsContainer').style.display = 'block';
    }

}


document.getElementById('connectWallet').addEventListener('click', connectWallet);

document.getElementById('compileButton').addEventListener('click', function() {
    closeModal();

    document.getElementById('bytecodeOutput').value = '';
    document.getElementById('abiOutput').value = '';

    var code = document.getElementById('codeInput').value;
    var vyperVersion = document.getElementById('vyperVersion').value;
    var evmVersion = document.getElementById('evmVersion').value;

    compileContract(code, vyperVersion, evmVersion);

});

document.getElementById('deployButton').addEventListener('click', async () => {
    if (!compiledAbi || !compiledBytecode) {
        openModal('Please compile the contract first.');
        return;
    }

    const inputs = document.querySelectorAll('#constructorParams input');
    const constructorArgs = Array.from(inputs).map(input => input.value);

    await deployContract(compiledAbi, compiledBytecode, constructorArgs);
});

document.getElementById('codeInput').addEventListener('input', function() {
    this.style.height = 'auto'; 
    this.style.height = (this.scrollHeight) + 'px'; 
});

