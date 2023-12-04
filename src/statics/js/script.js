
let compiledAbi = null;
let compiledBytecode = null;
let ganacheAccounts = null;
let w3 = null;

async function ganacheProvider(envVersion) {
    const options = {
        hardfork: envVersion
    };
    
    const provider = Ganache.provider(options);
    w3 = new ethers.providers.Web3Provider(provider);
    ganacheAccounts = await w3.listAccounts();
}


async function connectWallet() {
    const environmentSelect = document.getElementById('environment');
    if (environmentSelect.value === 'metamask' || environmentSelect.value === 'paris') {
        if (window.ethereum) {
            try {
                await window.ethereum.request({ method: 'eth_requestAccounts' });
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                const signer = provider.getSigner();
                const account = await signer.getAddress();
                const balance = await provider.getBalance(account);               
                const formattedBalance = parseFloat(ethers.utils.formatEther(balance)).toFixed(4);
                const formatAccount = account.slice(0, 6) + "..." + account.slice(38, 42) + " (" + formattedBalance + " ether" + ")";

                const accountSelect = document.getElementById('account'); 
                accountSelect.innerHTML = '';

                const option = document.createElement('option');
                option.textContent = formatAccount;
                accountSelect.appendChild(option);

                console.log('Connected to MetaMask.');
                console.log("balance: ", formattedBalance);
                console.log(formatAccount)

            } catch (error) {
                console.error('User denied account access', error);
            }

        } else {
            alert('MetaMask is not installed. Please consider installing it: https://metamask.io/');
        };

    } else if (environmentSelect.value === 'shanghai' || environmentSelect.value === 'istanbul' || environmentSelect.value == 'berlin') {

        await ganacheProvider(environmentSelect.value);
        updateAccountDisplay(ganacheAccounts, w3);

    };
}


function updateAccountDisplay(accounts, w3) {
    const accountSelect = document.getElementById('account'); 
    accountSelect.innerHTML = ''; 

    accounts.forEach(async account => {
        const accountBalance = await w3.getBalance(account);
        const formattedBalance = parseFloat(ethers.utils.formatEther(accountBalance)).toFixed(4);
        const option = document.createElement('option');
        option.value = account;
        option.textContent = account.slice(0, 6) + "..." + account.slice(38, 42) + " (" + formattedBalance + " ether" + ")";
        accountSelect.appendChild(option);
    });
}



function displayConstructorParams(abi) {
    const constructorAbi = abi.find(element => element.type === 'constructor');
    const container = document.getElementById('constructorParams');
    container.innerHTML = ''; 

    if (constructorAbi && constructorAbi.inputs.length > 0) {
        constructorAbi.inputs.forEach(input => {
            const paramDiv = document.createElement('div'); 
            paramDiv.classList.add('param'); 

            const label = document.createElement('label');
            label.textContent = input.name + ': ';
            label.htmlFor = input.name; 

            const inputField = document.createElement('input');
            inputField.type = 'text';
            inputField.id = input.name; 
            inputField.placeholder = " " + input.type;

            paramDiv.appendChild(label); 
            paramDiv.appendChild(inputField);
            container.appendChild(paramDiv); 
        });

        document.getElementById('constructorParamsContainer').style.display = 'block';
    } else {
        document.getElementById('constructorParamsContainer').style.display = 'none';
    }
}


function compileContract(code, version, environment) {
    const data = {
        code: code,
        vyper_version: version,
        evm_version: environment
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

            document.getElementById('bytecodeOutput').value = data.Data.bytecode;
            document.getElementById('abiOutput').value = data.Data.abi;

            displayConstructorParams(compiledAbi);

        } else {
            openModal(data.Msg)
        }
    });

}


async function deployContract(envVersion, abi, bytecode, constructorArgs, gasLimit, value) {

    let provider = null;
    let signer = null;

    if (envVersion === "metamask" || envVersion === "paris") {
        provider = new ethers.providers.Web3Provider(window.ethereum);
        await provider.send("eth_requestAccounts", []);
        signer = provider.getSigner();
    } else if (envVersion === 'shanghai' || envVersion === 'istanbul' || envVersion === 'berlin') {
        provider = w3;
        const account = document.getElementById("account").value;
        const accountIndex = ganacheAccounts.findIndex(addr => addr.toLowerCase() === account.toLowerCase());
        signer = provider.getSigner(accountIndex);
    }

    const contractFactory = new ethers.ContractFactory(abi, bytecode, signer);
    const contract = await contractFactory.deploy(...constructorArgs, {gasLimit: gasLimit, value: value});

    await contract.deployed();

    document.getElementById('address').value = contract.address;

    const inputs = document.querySelectorAll('#constructorParams input');
    inputs.forEach(input => input.value = '');

    document.getElementById('constructorParamsContainer').style.display = 'none';

    document.getElementById('bytecodeOutput').value = '...';
    document.getElementById('abiOutput').value = '...';

    const successModal = document.createElement('div');
    successModal.id = 'successModal';
    successModal.innerHTML = `
      <p>Contract deployed at: ${contract.address}</p>
      <button onclick="this.parentElement.style.display='none'">Close</button>
    `;
    document.body.appendChild(successModal);
    setTimeout(() => successModal.style.display = 'block', 100); 
    setTimeout(() => successModal.style.display = 'none', 5000);
}


function copyToClipboard(id) {
	var copyText = document.getElementById(id);
	navigator.clipboard.writeText(copyText.value)
		.then(() => {
			alert("Copied the text: " + copyText.value);
		})
		.catch(err => {
			console.error('Error in copying text: ', err);
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


document.addEventListener('DOMContentLoaded', async function () {
	const environmentSelect = document.getElementById('environment');
    environmentSelect.addEventListener('change', connectWallet);
    connectWallet();
    
});


document.getElementById('compileButton').addEventListener('click', function() {
    closeModal();

    document.getElementById('bytecodeOutput').value = '...';
    document.getElementById('abiOutput').value = '...';
    document.getElementById('address').value = '...';
    document.getElementById('value').value = '';

    var code = document.getElementById('codeInput').value;
    var version = document.getElementById('version').value;
    var environment = document.getElementById('environment').value;

    compileContract(code, version, environment);

});


document.getElementById('deployButton').addEventListener('click', async (event) => {
    if (!compiledAbi || !compiledBytecode) {
        openModal('Please compile the contract first.');
        return;
    }

    const deployButton = event.currentTarget;
    deployButton.style.backgroundColor = '#f8f8f8';
    deployButton.innerHTML = '<img src="/statics/images/loading.svg" alt="Loading..." class="loading-indicator">';
    deployButton.disabled = true;

    const inputs = document.querySelectorAll('#constructorParams input');
    const constructorArgs = Array.from(inputs).map(input => input.value);

    const gasLimit = ethers.BigNumber.from(document.getElementById("gasLimit").value);
    let valueInput = document.getElementById("value").value;
    let value =  valueInput === "" ? "0" : valueInput
    const unit = document.getElementById("unit").value;

    value = ethers.utils.parseUnits(value, unit);

    const environmentSelect = document.getElementById('environment');
    console.log(environmentSelect.value);

    await deployContract(environmentSelect.value, compiledAbi, compiledBytecode, constructorArgs, gasLimit, value)
        .then(() => {
            deployButton.style.backgroundColor = 'yellow';
        })
        .catch(() => {
            deployButton.style.backgroundColor = 'yellow';
        });

    deployButton.innerHTML = "Deploy";
    deployButton.disabled = false;
    document.getElementById('value').value = '';
});





