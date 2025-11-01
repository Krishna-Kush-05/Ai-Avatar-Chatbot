// === Prevent default behavior globally (avoid file opening in browser) ===
window.addEventListener("dragover", function(e) {
  e.preventDefault();
}, false);

window.addEventListener("drop", function(e) {
  e.preventDefault();
}, false);

// === Handle drop-area styling & file capture ===
const dropArea = document.getElementById("drop-area");

["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
  dropArea.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});

["dragenter", "dragover"].forEach(eventName => {
  dropArea.classList.add("highlight");
});

["dragleave", "drop"].forEach(eventName => {
  dropArea.classList.remove("highlight");
});

dropArea.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    document.getElementById("pdf-input").files = files;

    // Optional: auto-submit the form if desired
    // document.getElementById("preview-form").submit();
  }
});
