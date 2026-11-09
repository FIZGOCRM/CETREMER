// checkout.js - Real-time checkout updates and simulated payment processing
document.addEventListener("DOMContentLoaded", function() {
    // Payment Tab Selection Logic
    const tabButtons = document.querySelectorAll(".payment-tab-btn");
    const creditCardForm = document.getElementById("credit-card-form-wrapper");
    const pixForm = document.getElementById("pix-form-wrapper");
    const paymentMethodInput = document.getElementById("payment_method_input");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", function() {
            tabButtons.forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            
            const selectedMethod = this.dataset.method;
            if (paymentMethodInput) {
                paymentMethodInput.value = selectedMethod;
            }

            if (selectedMethod === "CREDIT_CARD") {
                if (creditCardForm) creditCardForm.style.display = "block";
                if (pixForm) pixForm.style.display = "none";
            } else {
                if (creditCardForm) creditCardForm.style.display = "none";
                if (pixForm) pixForm.style.display = "block";
            }
        });
    });

    // Credit Card interactive preview updates
    const inputNumber = document.getElementById("card_number_input");
    const inputHolder = document.getElementById("card_holder_input");
    const inputExpiry = document.getElementById("card_expiry_input");

    const previewNumber = document.getElementById("card_preview_number");
    const previewHolder = document.getElementById("card_preview_holder");
    const previewExpiry = document.getElementById("card_preview_expiry");

    if (inputNumber && previewNumber) {
        inputNumber.addEventListener("input", function() {
            let val = this.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            let formatted = "";
            for (let i = 0; i < val.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formatted += " ";
                }
                formatted += val[i];
            }
            this.value = formatted;
            previewNumber.textContent = formatted || "•••• •••• •••• ••••";
        });
    }

    if (inputHolder && previewHolder) {
        inputHolder.addEventListener("input", function() {
            previewHolder.textContent = this.value.toUpperCase() || "NOME DO TITULAR";
        });
    }

    if (inputExpiry && previewExpiry) {
        inputExpiry.addEventListener("input", function() {
            let val = this.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            if (val.length > 2) {
                this.value = val.substring(0, 2) + "/" + val.substring(2, 4);
            } else {
                this.value = val;
            }
            previewExpiry.textContent = this.value || "MM/YY";
        });
    }

    // Order Bump real-time totals and form updates
    const bumpCheckboxes = document.querySelectorAll(".order-bump-checkbox");
    const baseCoursePriceText = document.getElementById("base-course-price");
    const summaryBumpsList = document.getElementById("summary-bumps-list");
    const totalAmountText = document.getElementById("total-checkout-amount");
    const selectedBumpsInput = document.getElementById("selected_bumps_input");

    function calculateTotal() {
        if (!baseCoursePriceText || !totalAmountText) return;

        let total = parseFloat(baseCoursePriceText.dataset.price);
        let selectedBumps = [];
        if (summaryBumpsList) {
            summaryBumpsList.innerHTML = "";
        }

        bumpCheckboxes.forEach(cb => {
            if (cb.checked) {
                const bumpId = cb.dataset.bumpId;
                const bumpPrice = parseFloat(cb.dataset.price);
                const bumpTitle = cb.dataset.title;
                total += bumpPrice;
                selectedBumps.push(bumpId);

                // Add to summary view
                if (summaryBumpsList) {
                    const row = document.createElement("div");
                    row.className = "summary-row";
                    row.innerHTML = `<span>+ ${bumpTitle}</span><span>$${bumpPrice.toFixed(2)}</span>`;
                    summaryBumpsList.appendChild(row);
                }
            }
        });

        totalAmountText.textContent = `$${total.toFixed(2)}`;
        if (selectedBumpsInput) {
            selectedBumpsInput.value = selectedBumps.join(",");
        }
    }

    bumpCheckboxes.forEach(cb => {
        cb.addEventListener("change", calculateTotal);
    });

    // Mock processing loader simulation on submission
    const checkoutForm = document.getElementById("checkout-main-form");
    const modalOverlay = document.getElementById("payment-loading-modal");

    if (checkoutForm && modalOverlay) {
        checkoutForm.addEventListener("submit", function(e) {
            e.preventDefault();
            
            // Open processing status dialog modal
            modalOverlay.style.display = "flex";

            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Wait 2.5 seconds to simulate authentication check
            setTimeout(() => {
                fetch(this.action, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": csrfToken
                    }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        // Redirect to the success dashboard
                        window.location.href = data.redirect_url;
                    } else {
                        alert(data.message || "Falha na verificação do cartão. Por favor, tente novamente.");
                        modalOverlay.style.display = "none";
                    }
                })
                .catch(err => {
                    console.error("An error occurred during submission:", err);
                    modalOverlay.style.display = "none";
                });
            }, 2500);
        });
    }
});
