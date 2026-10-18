// Wait until the Django Admin page has finished loading.
document.addEventListener("DOMContentLoaded", function () {

    // Find the Period Type dropdown.
    const periodTypeField = document.getElementById(
        "id_period_type"
    );

    // Find the Period Name dropdown.
    const periodNameField = document.getElementById(
        "id_name"
    );

    // Stop if either field cannot be found.
    if (!periodTypeField || !periodNameField) {
        return;
    }

    // Define the Period Name options available
    // for each academic period type.
    const periodNameChoices = {
        TERM: [
            ["1", "Term 1"],
            ["2", "Term 2"],
            ["3", "Term 3"],
            ["4", "Term 4"]
        ],

        SEMESTER: [
            ["1", "Semester 1"],
            ["2", "Semester 2"]
        ],

        TRIMESTER: [
            ["1", "Trimester 1"],
            ["2", "Trimester 2"],
            ["3", "Trimester 3"]
        ],

        QUARTER: [
            ["1", "Quarter 1"],
            ["2", "Quarter 2"],
            ["3", "Quarter 3"],
            ["4", "Quarter 4"]
        ],

        YEAR: [
            ["1", "Year"]
        ]
    };

    // Rebuild the Period Name dropdown
    // whenever the Period Type changes.
    function updatePeriodNames() {

        // Get the selected Period Type.
        const selectedType = periodTypeField.value;

        // Clear the current Period Name options.
        periodNameField.innerHTML = "";

        // Add an instruction at the top.
        const placeholder = document.createElement("option");

        placeholder.value = "";
        placeholder.textContent = "Select Period Name";

        periodNameField.appendChild(placeholder);

        // Get the choices for the selected type.
        const choices = periodNameChoices[selectedType] || [];

        // Add each valid Period Name to the dropdown.
        choices.forEach(function (choice) {

            const option = document.createElement("option");

            option.value = choice[0];
            option.textContent = choice[1];

            periodNameField.appendChild(option);
        });
    }

    // Update the Period Name dropdown
    // whenever Period Type changes.
    periodTypeField.addEventListener(
        "change",
        updatePeriodNames
    );

    // Populate the Period Name dropdown
    // when the page first opens.
    updatePeriodNames();
});