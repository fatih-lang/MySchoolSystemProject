// Wait until the entire Admin page has finished loading.
document.addEventListener("DOMContentLoaded", function () {

    // Find the School dropdown after the page is ready.
    const schoolField = document.getElementById("id_school");

    // Make sure the School field actually exists.
    if (!schoolField) {
        return;
    }

    // Run this code whenever the administrator
    // changes the selected school.
    schoolField.addEventListener("change", function () {

        // Get the ID of the selected school.
        const schoolId = this.value;

        // Do nothing if no school has been selected.
        if (!schoolId) {
            return;
        }

        // Get the current Admin page URL.
        const currentUrl = new URL(window.location.href);

        // Add the selected school ID to the URL.
        currentUrl.searchParams.set("school", schoolId);

        // Reload the page using the new URL.
        window.location.href = currentUrl.toString();
    });
});