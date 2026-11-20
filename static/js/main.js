/**
 * IQAC Activity Tracking System - Client-side validation & constraints
 * Enforces character limits, date constraints, and file constraints strictly.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Highlight active sidebar navigation item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.parentElement.classList.add('active');
            link.style.backgroundColor = '#1e293b';
            link.style.color = '#ffffff';
        }
    });

    // 2. Strict character limit enforcement on EVERY textbox and textarea
    // "everytextbox charlimit and then cant add more"
    const textControls = document.querySelectorAll('input[maxlength], textarea[maxlength]');
    textControls.forEach(el => {
        const max = parseInt(el.getAttribute('maxlength'), 10);
        if (!max || isNaN(max)) return;

        // Block typing beyond character limit
        el.addEventListener('keydown', function (e) {
            // Allow control keys: Backspace, Tab, Enter, Escape, Arrow keys, Delete, and shortcuts (Ctrl/Meta)
            const allowedControlKeys = [
                'Backspace', 'Tab', 'Enter', 'Escape', 'ArrowLeft', 'ArrowRight', 
                'ArrowUp', 'ArrowDown', 'Delete', 'Home', 'End'
            ];
            if (allowedControlKeys.includes(e.key) || e.ctrlKey || e.metaKey || e.altKey) {
                return;
            }

            // Check selected text length; if replacing selected text, allow typing
            const selectedTextLength = (this.selectionEnd - this.selectionStart) || 0;
            if (this.value.length >= max && selectedTextLength === 0) {
                e.preventDefault();
            }
        });

        // Enforce limit on paste and composition events
        el.addEventListener('input', function () {
            if (this.value.length > max) {
                this.value = this.value.slice(0, max);
            }
        });
    });

    // 3. File input client-side validator (FR-026, FR-027, BR-013)
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(fileInput => {
        fileInput.addEventListener('change', function () {
            if (!this.files || this.files.length === 0) return;
            const file = this.files[0];
            const maxBytes = 10 * 1024 * 1024; // 10 MB limit
            const allowedExtensions = ['pdf', 'docx', 'jpg', 'jpeg', 'png'];

            const parts = file.name.split('.');
            const ext = parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';

            if (!allowedExtensions.includes(ext)) {
                alert('Unsupported format. Allowed: PDF, DOCX, JPG, PNG (FR-026, BR-013).');
                this.value = '';
                return;
            }

            if (file.size > maxBytes) {
                alert('File exceeds the maximum size limit (10 MB). Upload rejected (FR-027, BR-013).');
                this.value = '';
                return;
            }
        });
    });

    // 4. Date validator for Create Activity (BR-003)
    const startInput = document.getElementById('planned_start') || document.getElementById('plannedStart');
    const deadlineInput = document.getElementById('deadline');
    if (startInput && deadlineInput) {
        const checkDates = function () {
            if (startInput.value && deadlineInput.value) {
                if (deadlineInput.value < startInput.value) {
                    alert('Deadline cannot be before the planned start date (BR-003).');
                    deadlineInput.value = '';
                }
            }
        };
        deadlineInput.addEventListener('change', checkDates);
        startInput.addEventListener('change', checkDates);
    }
});
