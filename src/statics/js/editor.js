
document.addEventListener('DOMContentLoaded', function () {
	var codeInput = document.getElementById("codeInput");
	var defaultCode = `
# @version 0.3.9
"""
@title Default code
@author 0x77
@license Copyright (c) VyperOnline, 2023-2025 - all rights reserved
"""

owner: public(address)
name: public(String[12])


@payable
@external
def __init__():
	self.owner = msg.sender
	self.name = "Hello Vyper!"
	`;

	codeInput.value = defaultCode.trim();

	var editor = CodeMirror.fromTextArea(codeInput, {
		lineNumbers: true,
		mode: "python",
		theme: "default",
		indentUnit: 4,
		tabSize: 4,
		indentWithTabs: true,
		autoCloseBrackets: true,
		extraKeys: { "Ctrl-Space": "autocomplete" },
		matchBrackets: true,
		hintOptions: {
			tables: {
				table1: ['name', 'score', 'birthDate'],
				table2: ['name', 'population', 'size']
			}
		}
	});

	const ignore = ['', '#', '!', '-', '=', '@', '$', '%', '&', '+', ';', '(', ')', '*'];
	const ignoreToken = (text) => {
		if (text && text[0]) {
			for (const pre in ignore) {
				if (ignore[pre] === text[0]) {
					return true;
				}
			}
		} else {
			return true;
		}
		return false;
	};

	editor.on("change", function (editor, change) {
		if (change.origin == "+input") {
			var text = change.text;
			if (!ignoreToken(text))
				setTimeout(function () { editor.execCommand("autocomplete"); }, 20);
		}
	});

});




