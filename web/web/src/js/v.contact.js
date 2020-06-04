const validateSubmission = (name, email, comment) => {
    if (name.trim() === "" || name === null || name === undefined)
        return false;

    if (email.trim() === "" || email === null || email === undefined)
        return false;

    if (comment.trim() === "" || comment === null || comment === undefined)
        return false;


    return true;
};

const submitForm = (name, email, comment, ck_erp_val, nonce) => {
    return new Promise((resolve, reject) => {
        fetch("/contact", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                name: name,
                comment: comment,
                ck_erp_val: ck_erp_val,
                nonce: nonce
            })
        })
        .then((res) => {
            return res.json();
        })
        .then((res) => {
            resolve(res);
        })
        .catch((err) => {
            reject(err);
        })

    });
}

const contact = () => {

    if (document.getElementById("ctc-form")) {
        let name = document.getElementById("ctc-name"),
            email = document.getElementById("ctc-email"),
            comment = document.getElementById("ctc-comment"),
            anchor = document.getElementById("anchor"),
            ck_erp_val = document.getElementById("ck_erp_val"),
            btn_submit = document.getElementById("ctc-submit"),
            ctcFailure = document.getElementById("ctc-result-failure"),
            ctcSuccess = document.getElementById("ctc-result-success"),
            ctcForm = document.getElementById("ctc-form"),
            ctcFailMessage = document.getElementById("ctc-fail-message"),
            submitting = false;


        btn_submit.addEventListener("click", (e) => {
            e.preventDefault();

            let nameVal = name.value,
                emailVal = email.value,
                commentVal = comment.value,
                ck_erp_valVal = ck_erp_val.value,
                anchorVal = anchor.value;

            if (submitting)
                return;

            submitting = true;

            name.disabled = true;
            email.disabled = true;
            comment.disabled = true;
            btn_submit.value = "Submitting...";
            btn_submit.disabled = true;

            if (validateSubmission(name.value, email.value, comment.value)) {
                submitForm(nameVal, emailVal, commentVal, ck_erp_valVal, anchorVal)
                    .then(res => {
                        if (res.success) {
                            ctcForm.style.display = "none";
                            ctcSuccess.style.display = "block";
                        } else {
                            ctcFailure.style.display = "block";
                            switch(res.err) {
                                case "GH_SUBMIT_FAILED":
                                    ctcForm.style.display = "none";
                                    ctcFailMessage.innerText = "An unknown error occured. Please come back and try again later.";
                                    break;
                                case "ERR_NO_NAME":
                                    ctcFailMessage.innertText = "Please provide a valid name";
                                    break
                                case "ERR_NO_EMAIL":
                                    ctcFailMessage.innerText = "Please provide a valid email address";
                                    break;
                                case "ERR_NO_COMMENT":
                                    ctcFailMessage.innerText = "Please provide a valid comment";
                                    break;
                                case "ERR_INVALID_EMAIL":
                                    ctcFailMessage.innerText = "Please provide a valid email address";
                                    break;
                                case "ERR_RATE_LIMIT":
                                    ctcFailMessage.innerText = "Please come back and try again later.";
                                    break;
                                default:
                                    break;
                            }

                        }
                    })
                    .catch(err => {
                        ctcForm.style.display = "none";
                        ctcFailMessage.style.display = "block";
                        ctcFailMessage.innerText = "An unknown error occured. Please come back and try again later.";
                    });
            }

        });
    }
};

export default contact;
