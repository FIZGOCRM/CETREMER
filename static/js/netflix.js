// Premium Netflix layout and interactive lesson controls
document.addEventListener("DOMContentLoaded", function() {
    // Accordion functionality for sidebar modules
    const moduleButtons = document.querySelectorAll(".module-title-btn");
    moduleButtons.forEach(btn => {
        btn.addEventListener("click", function() {
            const lessonsList = this.nextElementSibling;
            const icon = this.querySelector(".module-toggle-icon");
            
            // Toggle lesson visibility
            if (lessonsList.classList.contains("hidden")) {
                lessonsList.classList.remove("hidden");
                if (icon) icon.style.transform = "rotate(180deg)";
            } else {
                lessonsList.classList.add("hidden");
                if (icon) icon.style.transform = "rotate(0deg)";
            }
        });
    });

    // Handle AJAX toggle completion for student lessons
    const completeButtons = document.querySelectorAll(".btn-toggle-complete");
    completeButtons.forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            const lessonId = this.dataset.lessonId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const buttonElement = this;
            
            fetch(`/courses/lesson/${lessonId}/toggle-progress/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    // Update main progress bar percentage
                    const progressFill = document.querySelector(".progress-fill");
                    const progressPercentageText = document.querySelector(".progress-percent");
                    const progressFractionText = document.querySelector(".progress-fraction");
                    
                    if (progressFill) {
                        progressFill.style.width = `${data.percentage}%`;
                    }
                    if (progressPercentageText) {
                        progressPercentageText.textContent = `${Math.round(data.percentage)}% concluído`;
                    }
                    if (progressFractionText) {
                        progressFractionText.textContent = `${data.completed_count}/${data.total_count}`;
                    }

                    // Update UI indicators
                    const statusDot = document.querySelector(`#status-dot-${lessonId}`);
                    if (data.is_completed) {
                        buttonElement.classList.remove("btn-secondary");
                        buttonElement.classList.add("btn-primary");
                        buttonElement.innerHTML = `<span>✓ Concluído</span>`;
                        if (statusDot) {
                            statusDot.classList.add("completed");
                        }
                    } else {
                        buttonElement.classList.remove("btn-primary");
                        buttonElement.classList.add("btn-secondary");
                        buttonElement.innerHTML = `<span>Marcar como Concluído</span>`;
                        if (statusDot) {
                            statusDot.classList.remove("completed");
                        }
                    }
                }
            })
            .catch(error => {
                console.error("Failed to update progress:", error);
            });
        });
    });
});
