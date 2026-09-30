// Test message to confirm the phone is loading this JavaScript file.
alert("JavaScript is working on the phone!");


// Find all dashboard cards on the page.
const dashboardCards = document.querySelectorAll(".dashboard-card");


// Go through every dashboard card.
dashboardCards.forEach(function(card) {

    // Listen for a pointer press on this card.
    card.addEventListener("pointerdown", function() {

        // Add the shake class to the card.
        card.classList.add("shake");

        // Find the heading inside the card.
        const cardTitle = card.querySelector("h3");

        // Display the card title in the browser console.
        console.log("You clicked:", cardTitle.textContent);

        // Remove the shake class after the animation finishes.
        setTimeout(function() {
            card.classList.remove("shake");
        }, 500);

    });

});

// ==========================================================
// STUDENT REGISTRATION
// ==========================================================


// ----------------------------------------------------------
// Find the Student Registration section.
// ----------------------------------------------------------

const studentRegistration =
    document.getElementById("student-registration");


// ----------------------------------------------------------
// Find the Register Student button from Quick Actions.
// ----------------------------------------------------------

const registerStudentButton =
    document.getElementById("register-student");


// ----------------------------------------------------------
// Find the Submit Student button inside the registration form.
// ----------------------------------------------------------

const submitStudentButton =
        document.getElementById("submit-student");


// ----------------------------------------------------------
// Hide the registration form when the page first loads.
// ----------------------------------------------------------

studentRegistration.style.display = "none";


// ----------------------------------------------------------
// Listen for a click on the Quick Action
// "Register Student" button.
// ----------------------------------------------------------

registerStudentButton.addEventListener("click", function() {

    // Show a message in the browser console.
    console.log("Register Student button clicked!");

    // Show the Student Registration section.
    studentRegistration.style.display = "block";

});



// ==========================================================
// STUDENT REGISTRATION FORM
// ==========================================================


// ----------------------------------------------------------
// Connect JavaScript to all student registration fields.
// ----------------------------------------------------------

function connectStudentForm() {

    // ======================================================
    // STUDENT PERSONAL INFORMATION
    // ======================================================

    // Find the student's name input.
    const studentNameInput =
        document.getElementById("student-name");

    // Find the student's surname input.
    const studentSurnameInput =
        document.getElementById("student-surname");

    // Find the student's ID number input.
    const studentIdInput =
        document.getElementById("student-id");

    // Find the student's age input.
    const studentAgeInput =
        document.getElementById("student-age");

    // Find the student's gender selection.
    const studentGenderInput =
        document.getElementById("student-gender");

    // Find the student's nationality selection.
    const studentNationalityInput =
        document.getElementById("student-nationality");


    // ======================================================
    // SCHOOL INFORMATION
    // ======================================================

    // Find the student's grade selection.
    const studentGradeInput =
        document.getElementById("student-grade");

    // Find the student's classroom input.
    const studentClassroomInput =
        document.getElementById("student-classroom");


    // ======================================================
    // ACCOUNT INFORMATION
    // ======================================================

    // Find the student's password input.
    const studentPasswordInput =
        document.getElementById("student-password");

    // Find the password confirmation input.
    const studentConfirmPasswordInput =
        document.getElementById("student-confirm-password");


    // ======================================================
    // RETURN THE CONNECTED FIELDS
    // ======================================================

    // Return all the fields so other functions
    // can use them.
    return {

        studentNameInput,
        studentSurnameInput,
        studentIdInput,
        studentAgeInput,
        studentGenderInput,
        studentNationalityInput,

        studentGradeInput,
        studentClassroomInput,

        studentPasswordInput,
        studentConfirmPasswordInput
    };
}


// ----------------------------------------------------------
// Connect the registration form.
// ----------------------------------------------------------

const studentForm = connectStudentForm();

// Find the area where registration messages will be displayed.
const registrationMessage =
    document.getElementById("registration-message");


// ==========================================================
// GET STUDENT FORM DATA
// ==========================================================


// ----------------------------------------------------------
// Create a function that reads all information
// entered into the student registration form.
// ----------------------------------------------------------

function getStudentFormData() {

    // Read the student's name.
    const studentName =
        studentForm.studentNameInput.value;

    // Read the student's surname.
    const studentSurname =
        studentForm.studentSurnameInput.value;

    // Read the student's ID number.
    const studentId =
        studentForm.studentIdInput.value;

    // Read the student's age.
    const studentAge =
        studentForm.studentAgeInput.value;

    // Read the student's gender.
    const studentGender =
        studentForm.studentGenderInput.value;

    // Read the student's nationality.
    const studentNationality =
        studentForm.studentNationalityInput.value;


    // ------------------------------------------------------
    // SCHOOL INFORMATION
    // ------------------------------------------------------

    // Read the student's grade.
    const studentGrade =
        studentForm.studentGradeInput.value;

    // Read the student's classroom.
    const studentClassroom =
        studentForm.studentClassroomInput.value;


    // ------------------------------------------------------
    // ACCOUNT INFORMATION
    // ------------------------------------------------------

    // Read the student's password.
    const studentPassword =
        studentForm.studentPasswordInput.value;

    // Read the password confirmation.
    const studentConfirmPassword =
        studentForm.studentConfirmPasswordInput.value;


    // ------------------------------------------------------
    // RETURN ALL STUDENT INFORMATION
    // ------------------------------------------------------

    // Return all the values as one object.
    return {

        studentName,
        studentSurname,
        studentId,
        studentAge,
        studentGender,
        studentNationality,

        studentGrade,
        studentClassroom,

        studentPassword,
        studentConfirmPassword
    };
}

    
    

// ==========================================================
// VALIDATE STUDENT REGISTRATION FORM
// ==========================================================

// ----------------------------------------------------------
// Check all information entered into the student form.
// The function receives the student data object from
// getStudentFormData().
// ----------------------------------------------------------

function validateStudentForm(studentData) {

    // Create an empty string.
    // We will add every validation error to this string.
    let errors = "";


    // ======================================================
    // STUDENT PERSONAL INFORMATION
    // ======================================================

    // Check student name.
    if (studentData.studentName === "") {
        errors += "• Please enter the student's name.\n";
    }

    // Check student surname.
    if (studentData.studentSurname === "") {
        errors += "• Please enter the student's surname.\n";
    }

    // Check student ID number.
    if (studentData.studentId === "") {
        errors += "• Please enter the student's ID number.\n";
    }

    // Check student age.
    if (studentData.studentAge === "") {
        errors += "• Please enter the student's age.\n";
    }

    // Check gender.
    if (studentData.studentGender === "") {
        errors += "• Please select the student's gender.\n";
    }

    // Check nationality.
    if (studentData.studentNationality === "") {
        errors += "• Please select the student's nationality.\n";
    }


    // ======================================================
    // SCHOOL INFORMATION
    // ======================================================

    // Check grade.
    if (studentData.studentGrade === "") {
        errors += "• Please select the student's grade.\n";
    }

    // Check classroom.
    if (studentData.studentClassroom === "") {
        errors += "• Please enter the student's classroom.\n";
    }


    // ======================================================
    // ACCOUNT INFORMATION
    // ======================================================

    // Check password.
    if (studentData.studentPassword === "") {
        errors += "• Please enter a password.\n";
    }

    // Check password confirmation.
    if (studentData.studentConfirmPassword === "") {
        errors += "• Please confirm the password.\n";
    }


    // ======================================================
    // PASSWORD VALIDATION
    // ======================================================

    // Only compare the passwords when both fields
    // contain something.
    if (
        studentData.studentPassword !== "" &&
        studentData.studentConfirmPassword !== "" &&
        studentData.studentPassword !==
        studentData.studentConfirmPassword
    ) {
        errors += "• The passwords do not match.\n";
    }

    // Check that the password contains at least
    // 5 characters.
    if (
        studentData.studentPassword !== "" &&
        studentData.studentPassword.length < 5
    ) {
        errors += "• Password must be at least 5 characters long.\n";
    }
    
    // ======================================================
    // CHECK PASSWORD REQUIREMENTS
    // ======================================================
    
    // Check that the password contains at least one letter.
    if (
        studentData.studentPassword !== "" &&
        !/[A-Za-z]/.test(studentData.studentPassword)
    ) {
        errors += "• Password must contain at least one letter.\n";
    }
    
    
    // Check that the password contains at least one number.
    if (
        studentData.studentPassword !== "" &&
        !/[0-9]/.test(studentData.studentPassword)
    ) {
        errors += "• Password must contain at least one number.\n";
    }
    
    
    // Check that the password contains at least one symbol.
    if (
        studentData.studentPassword !== "" &&
        !/[!@#$%^&*(),.?":{}|<>_\-\\[\]/;'`~+=]/.test(studentData.studentPassword)
    ) {
        errors += "• Password must contain at least one symbol.\n";
    }
    
    
        // ======================================================
        // RETURN VALIDATION RESULTS
        // ======================================================
    
        // Return all errors to whoever calls this function.
        return errors;
    }
    

// ==========================================================
// DISPLAY REGISTRATION MESSAGE
// ==========================================================

// ----------------------------------------------------------
// Display a message to the user inside the registration
// form.
// ----------------------------------------------------------

function showRegistrationMessage(message) {

    // Display the message inside the registration
    // message area.
    registrationMessage.textContent = message;

}    


submitStudentButton.addEventListener("click", function() {

    // ======================================================
    // GET THE INFORMATION FROM THE FORM
    // ======================================================

    // Call getStudentFormData() to collect everything
    // the user entered into the registration form.
    const studentData = getStudentFormData();


    // ======================================================
    // VALIDATE THE INFORMATION
    // ======================================================

    // Send the student data to our validation function.
    // The function will return an error message if
    // something is wrong.
    const errors = validateStudentForm(studentData);


    // ======================================================
    // CHECK FOR VALIDATION ERRORS
    // ======================================================

    if (errors !== "") {

        // Display the validation errors using our
        // message display function.
        showRegistrationMessage(errors);
    
        // Stop the registration process because
        // the information is not valid.
        return;
    }
    
    
    // Display only non-sensitive student information
    // while we are testing the registration process.
    console.log("Student Registration Data:", {
        name: studentData.studentName,
        surname: studentData.studentSurname,
        id: studentData.studentId,
        age: studentData.studentAge,
        gender: studentData.studentGender,
        nationality: studentData.studentNationality,
        grade: studentData.studentGrade,
        classroom: studentData.studentClassroom
    });
    
    // ------------------------------------------------------
    // Tell the user that the information passed validation.
    // ------------------------------------------------------
    
    showRegistrationMessage(
        "Student information is valid and ready to be submitted."
    );

});    