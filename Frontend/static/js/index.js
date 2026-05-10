/**
 * index.js – Greeting & dropdown logic for the chat page
 */
document.addEventListener("DOMContentLoaded", () => {
    // Time-based greeting using the current user's name from the DOM
    const greetingLine1 = document.getElementById("greeting-line1");
    if (greetingLine1) {
        const hour = new Date().getHours();
        let greeting;
        if (hour < 12) greeting = "Good morning";
        else if (hour < 17) greeting = "Good afternoon";
        else greeting = "Good evening";

        // Get the user's display name from the data attribute on the body or greeting element
        const userName = greetingLine1.dataset.username || "";
        greetingLine1.textContent = userName ? `${greeting}, ${userName}` : greeting;
    }
});
