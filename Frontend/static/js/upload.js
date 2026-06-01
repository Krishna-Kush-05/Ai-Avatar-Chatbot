/**
 * upload.js
 * Unified upload system
 */

window.addEventListener("dragover", e => e.preventDefault(), false);
window.addEventListener("drop", e => e.preventDefault(), false);

document.addEventListener("DOMContentLoaded", () => {

    const dropArea = document.getElementById("drop-area");
    const fileInput = document.getElementById("pdf");
    const uploadBtn = document.getElementById("upload-btn");
    const preview = document.getElementById("selected-files-preview");
    const status = document.getElementById("upload-status");
    const chatbotSelect = document.getElementById("chatbot_id");

    let selectedFiles = [];

    if (!dropArea || !fileInput) return;

    // Click to browse
    dropArea.addEventListener("click", () => {
        fileInput.click();
    });

    // File picker
    fileInput.addEventListener("change", () => {

        selectedFiles = Array.from(fileInput.files);

        renderFiles();
    });

    // Drag over
    dropArea.addEventListener("dragover", e => {

        e.preventDefault();

        dropArea.classList.add("dragover");
    });

    // Drag leave
    dropArea.addEventListener("dragleave", () => {

        dropArea.classList.remove("dragover");
    });

    // Drop files
    dropArea.addEventListener("drop", e => {

        e.preventDefault();

        dropArea.classList.remove("dragover");

        const files = Array.from(e.dataTransfer.files);

        const allowedExtensions = [
            ".pdf",
            ".txt",
            ".docx",
            ".md"
        ];

        selectedFiles = files.filter(file => {

            const lower = file.name.toLowerCase();

            return allowedExtensions.some(ext =>
                lower.endsWith(ext)
            );
        });

        if (!selectedFiles.length) {

            alert("Only PDF, TXT, DOCX, MD files allowed.");

            return;
        }

        renderFiles();
    });

    // Render selected files
    function renderFiles() {

        preview.innerHTML = "";

        selectedFiles.forEach(file => {

            const div = document.createElement("div");

            div.className = "selected-file";

            div.innerHTML = `📄 ${file.name}`;

            preview.appendChild(div);
        });
    }

    // Upload button
    uploadBtn.addEventListener("click", async () => {

        if (!selectedFiles.length) {

            alert("Please select files.");

            return;
        }

        const chatbotId = chatbotSelect.value;

        if (!chatbotId) {

            alert("Please select an assistant.");

            return;
        }

        const formData = new FormData();

        // IMPORTANT:
        // Backend expects "files"

        selectedFiles.forEach(file => {

            formData.append("files", file);
        });

        formData.append("chatbot_id", chatbotId);

        try {

            uploadBtn.disabled = true;

            uploadBtn.innerText = "Uploading...";

            status.innerHTML =
                "⏳ Uploading and indexing documents...";

            status.style.color = "#64748b";

            const response = await fetch("/api/upload", {

                method: "POST",

                body: formData
            });

            const data = await response.json();

            if (response.ok) {

                status.innerHTML =
                    "✅ Upload successful!";

                status.style.color = "#059669";

                preview.innerHTML = "";

                selectedFiles = [];

                fileInput.value = "";

            } else {

                console.error(data);

                status.innerHTML =
                    `❌ ${data.error || "Upload failed"}`;

                status.style.color = "#dc2626";
            }

        } catch (err) {

            console.error(err);

            status.innerHTML =
                `❌ Network error: ${err.message}`;

            status.style.color = "#dc2626";

        } finally {

            uploadBtn.disabled = false;

            uploadBtn.innerText =
                "Upload & Index →";
        }

    });

});
