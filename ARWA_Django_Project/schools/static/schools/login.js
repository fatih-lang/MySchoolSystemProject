/* =========================================================
   ARWA SCHOOL MANAGEMENT PLATFORM
   LOGIN PAGE JAVASCRIPT
   ========================================================= */


/* ---------------------------------------------------------
   1. FIND THE PASSWORD ELEMENTS
   --------------------------------------------------------- */

/*
    Find the password input field from the HTML.
*/
const passwordInput =
    document.getElementById("password");


/*
    Find the Show/Hide password button.
*/
const showPasswordButton =
    document.getElementById("show-password");


/* ---------------------------------------------------------
   2. SHOW / HIDE PASSWORD
   --------------------------------------------------------- */

/*
    Make sure both elements exist before
    trying to use them.

    This prevents JavaScript errors if
    the elements are not present.
*/
if (
    passwordInput &&
    showPasswordButton
) {

    /*
        Listen for the user tapping
        the Show/Hide button.
    */
    showPasswordButton.addEventListener(
        "click",
        function () {

            /*
                Check whether the password
                is currently hidden.
            */
            if (
                passwordInput.type === "password"
            ) {

                /*
                    Change the input to text.

                    The password will now
                    be visible to the user.
                */
                passwordInput.type = "text";


                /*
                    Change the button text
                    from Show to Hide.
                */
                showPasswordButton.textContent =
                    "Hide";

            }

            else {

                /*
                    Change the input back
                    to password.

                    The password is hidden again.
                */
                passwordInput.type =
                    "password";


                /*
                    Change the button text
                    back to Show.
                */
                showPasswordButton.textContent =
                    "Show";

            }

        }
    );

}