/**
 * upload.js – Drag-and-drop file handling for the upload page
 */

// Prevent default browser behavior for drag-and-drop globally
window.addEventListener("dragover", (e) => e.preventDefault(), false);
window.addEventListener("drop", (e) => e.preventDefault(), false);

document.addEventListener("DOMContentLoaded", () => {
    const dropArea = document.getElementById("drop-area");
    if (!dropArea) return;

    // Prevent default on all drag events
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Highlight on drag enter/over
    ["dragenter", "dragover"].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add("highlight");
        });
    });

    // Remove highlight on drag leave/drop
    ["dragleave", "drop"].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove("highlight");
        });
    });

    // Handle file drop
    dropArea.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const pdfInput = document.getElementById("pdf");
            if (pdfInput) {
                // Validate file type
                const file = files[0];
                if (file.type !== "application/pdf") {
                    alert("Please upload a PDF file only.");
                    return;
                }
                // Validate file size (max 50MB)
                if (file.size > 50 * 1024 * 1024) {
                    alert("File size must be less than 50MB.");
                    return;
                }
                try {
                    pdfInput.files = files;
                } catch (_) {
                    // Fallback: some browsers don't allow setting .files
                }
            }
        }
    });
});
