// =========================================================
// TEACHER CALENDAR & LIVE CLOCK
// =========================================================


// =========================================================
// LIVE CLOCK
// =========================================================

// Find the HTML elements that will display the time and date.
const teacherClock = document.getElementById("teacher-clock");
const teacherCurrentDate =
    document.getElementById("teacher-current-date");


// Update the clock and date.
function updateTeacherClock() {

    // Get the current date and time from the device.
    const now = new Date();


    // Get the current hours, minutes and seconds.
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const seconds = String(now.getSeconds()).padStart(2, "0");


    // Convert the 24-hour clock into a 12-hour clock.
    const period = hours >= 12 ? "PM" : "AM";

    hours = hours % 12;

    // When the hour is 0, display 12 instead.
    hours = hours || 12;


    // Create the complete clock text.
    const currentTime =
        `${String(hours).padStart(2, "0")}:${minutes}:${seconds} ${period}`;


    // Display the current time.
    teacherClock.textContent = currentTime;


    // Create a readable date.
    const dateOptions = {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric"
    };


    // Convert the date into readable text.
    const currentDate =
        now.toLocaleDateString("en-ZA", dateOptions);


    // Display today's date.
    teacherCurrentDate.textContent = currentDate;
}


// Run the clock immediately.
updateTeacherClock();


// Run the clock every one second.
setInterval(updateTeacherClock, 1000);



// =========================================================
// SCHOOL CALENDAR
// =========================================================

// Find the calendar elements.
const calendarMonth =
    document.getElementById("calendar-month");

const calendarDays =
    document.getElementById("calendar-days");

const previousMonthButton =
    document.getElementById("previous-month");

const nextMonthButton =
    document.getElementById("next-month");


// Keep track of the month currently being displayed.
let calendarDate = new Date();


// =========================================================
// GENERATE CALENDAR
// =========================================================

function generateCalendar() {

    // Get the year and month currently being viewed.
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();


    // Names of the months.
    const monthNames = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ];


    // Display the current month and year.
    calendarMonth.textContent =
        `${monthNames[month]} ${year}`;


    // Find the first day of the month.
    const firstDay =
        new Date(year, month, 1).getDay();


    // Find how many days are in this month.
    const daysInMonth =
        new Date(year, month + 1, 0).getDate();


    // Clear the old calendar dates.
    calendarDays.innerHTML = "";


    // =====================================================
    // CREATE EMPTY SPACES
    // =====================================================

    // Add empty spaces before the first day.
    for (let i = 0; i < firstDay; i++) {

        const emptyDay =
            document.createElement("div");

        emptyDay.classList.add(
            "calendar-day",
            "empty"
        );

        calendarDays.appendChild(emptyDay);
    }


    // =====================================================
    // CREATE CALENDAR DATES
    // =====================================================

    // Create each day of the month.
    for (let day = 1; day <= daysInMonth; day++) {

        const dayElement =
            document.createElement("div");


        // Give the date the calendar-day class.
        dayElement.classList.add("calendar-day");


        // Display the day number.
        dayElement.textContent = day;


        // =================================================
        // CHECK IF THIS IS TODAY
        // =================================================

        const today = new Date();


        if (
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()
        ) {

            // Highlight today's date.
            dayElement.classList.add("today");
        }


        // Add the date to the calendar.
        calendarDays.appendChild(dayElement);
    }
}



// =========================================================
// PREVIOUS MONTH
// =========================================================

previousMonthButton.addEventListener(
    "click",
    function () {

        // Move the calendar one month backwards.
        calendarDate.setMonth(
            calendarDate.getMonth() - 1
        );


        // Generate the new calendar.
        generateCalendar();
    }
);



// =========================================================
// NEXT MONTH
// =========================================================

nextMonthButton.addEventListener(
    "click",
    function () {

        // Move the calendar one month forward.
        calendarDate.setMonth(
            calendarDate.getMonth() + 1
        );


        // Generate the new calendar.
        generateCalendar();
    }
);



// =========================================================
// CREATE THE CALENDAR WHEN THE PAGE LOADS
// =========================================================

generateCalendar();



// =========================================================
// TEACHER NAVIGATION
// =========================================================

// Find all navigation links inside the teacher dashboard.
const teacherNavigationLinks =
    document.querySelectorAll(".navigation-link");


// Listen for clicks on every navigation link.
teacherNavigationLinks.forEach(function (link) {

    link.addEventListener("click", function (event) {

        // Stop the normal action of href="#".
        event.preventDefault();


        // Remove the "active" class from every
        // navigation link.
        teacherNavigationLinks.forEach(
            function (navigationLink) {

                navigationLink.classList.remove(
                    "active"
                );

            }
        );


        // Add the "active" class to the link
        // that the teacher clicked.
        link.classList.add("active");


        // Read the section name from data-section.
        const selectedSection =
            link.dataset.section;
            
            
        // Decide what to do based on the section
        // selected by the teacher.
        switch (selectedSection) {
            
            // Smoothly scroll to the My Classes section
            case "my_classes":
            document.getElementById("my-classes").scrollIntoView({
                behavior: "smooth"
            });
            break;
                
                
            // Smoothly scroll to the My Subjects section
            case "subjects":
                document.getElementById("my-subjects").scrollIntoView({
                    behavior: "smooth"
                });
                break;
                
            
            // Smoothly scroll to the My Students section
            case "students":
                document.getElementById("my-students").scrollIntoView({
                    behavior: "smooth"
                });
                break;    
                
        
            // Smoothly scroll to the Attendance section
            case "attendance":
                document.getElementById("attendance").scrollIntoView({
                    behavior: "smooth"
                });
                break;    
        
            
            // Smoothly scroll to the Homework section
            case "homework":
                document.getElementById("homework").scrollIntoView({
                    behavior: "smooth"
                });
                break;    
                
                
            // Smoothly scroll to the My Timetable section
            case "timetable":
                document.getElementById("my-timetable").scrollIntoView({
                    behavior: "smooth"
                });
                break;
                
                
            // Smoothly scroll to the My Guardians section
            case "guardians":
                document.getElementById("my-guardians").scrollIntoView({
                    behavior: "smooth"
                });
                break;   
                
            // Smoothly scroll to the Marks and Results section
            case "marks_and_results":
                document.getElementById("marks-results").scrollIntoView({
                    behavior: "smooth"
                });
                break; 
                
            // Smoothly scroll to the Staff Meeting section
            case "staff_meetings":
                document.getElementById("staff-meeting").scrollIntoView({
                    behavior: "smooth"
                });
                break;  
                
            // Smoothly scroll to the My HOD
            case "hod":
                document.getElementById("hod").scrollIntoView({
                    behavior: "smooth"
                });
                break;                          
        
            // Smoothly scroll to the School News
            case "school_news":
                document.getElementById("news").scrollIntoView({
                    behavior: "smooth"
                });
                break;
                
            // Smoothly scroll to the My Profile 
            case "teacher_profile":
                document.getElementById("profile").scrollIntoView({
                    behavior: "smooth"
                });
                break;    
            
            
            default:
        
                console.log(
                    "No JavaScript action has been added yet."
                );
        
        }

        // Display the selected section in the
        // browser console.
        console.log(
            "Teacher selected:",
            selectedSection
        );

    });

});


// =========================================================
// TEACHER TOAST NOTIFICATION
// =========================================================

// Create a reusable function for displaying
// a small notification on the dashboard.
function showTeacherNotification(message) {

    // Create a new div element.
    const notification =
        document.createElement("div");


    // Give the notification its CSS class.
    notification.classList.add(
        "teacher-notification"
    );


    // Put the message inside the notification.
    notification.textContent = message;


    // Add the notification to the webpage.
    document.body.appendChild(
        notification
    );


    // Remove the notification automatically
    // after 3 seconds.
    setTimeout(function () {

        notification.remove();

    }, 3000);

}


// =========================================================
// TEACHER QUICK ACTIONS
// =========================================================


// Find all Quick Action cards.
const teacherQuickActions =
    document.querySelectorAll(".quick-action-card");


// Listen for clicks on every Quick Action.
teacherQuickActions.forEach(function (quickAction) {

    quickAction.addEventListener(
    "click",
    function (event) {

        // Stop the temporary href="#"
        // from jumping to the top of the page.
        event.preventDefault();


        // Read the action name from
        // data-action.
        const selectedAction =
            quickAction.dataset.action;


        // Decide what to do based on the
        // Quick Action selected by the teacher.
        switch (selectedAction) {

            case "create_homework":

                showTeacherNotification(
                    "📝 Create Homework — Opening homework..."
                );

                break;


            case "mark_attendance":

                showTeacherNotification(
                    "✅ Mark Attendance — Opening attendance..."
                );

                break;


            case "enter_marks":

                showTeacherNotification(
                    "📊 Enter Marks — Opening marks..."
                );

                break;


            case "view_students":

                showTeacherNotification(
                    "✅ View Students — Opening students..."
                );

                break;


            case "timetable":

                showTeacherNotification(
                    "✅ Timetable — Opening timetable..."
                );

                break;


            case "school_news":

                showTeacherNotification(
                    "✅ School News — Opening School news..."
                );

                break;


            default:

                console.log(
                    "No Quick Action has been configured."
                );

        }


        // Add a temporary visual effect to
        // the Quick Action that was clicked.
        quickAction.classList.add(
            "quick-action-clicked"
        );


        // Remove the effect shortly afterwards.
        setTimeout(function () {

            quickAction.classList.remove(
                "quick-action-clicked"
            );

        }, 150);


        // Display the selected action
        // in the browser console.
        console.log(
            "Teacher selected action:",
            selectedAction
        );

    }
);

});


// =========================================================
// TEACHER NOTIFICATION BUTTON
// =========================================================

// Find the teacher notification button.
const teacherNotificationButton =
    document.getElementById(
        "teacher-notification-button"
    );


// Find the notification panel.
const teacherNotificationPanel =
    document.getElementById(
        "teacher-notification-panel"
    );
    
const teacherNotificationCount =
    document.getElementById(
        "teacher-notification-count"
    );    
    
// Find the unread count inside the notification panel.
const notificationPanelCount =
    document.getElementById(
        "notification-panel-count"
    );    


// Listen for a click on the notification bell.
teacherNotificationButton.addEventListener(
    "click",
    function () {

        // Add or remove the "show" class.
        teacherNotificationPanel.classList.toggle(
            "show"
        );

    }
);

// =========================================================
// CLOSE NOTIFICATION PANEL WHEN CLICKING OUTSIDE
// =========================================================

// Listen for clicks anywhere on the webpage.
document.addEventListener(
    "click",
    function (event) {

        // Check whether the click happened
        // inside the notification area.
        const clickedInsideNotification =
            event.target.closest(
                ".teacher-notification-wrapper"
            );


        // If the teacher clicked outside the
        // notification area, close the panel.
        if (!clickedInsideNotification) {

            teacherNotificationPanel.classList.remove(
                "show"
            );

        }

    }
);

// =========================================================
// UPDATE UNREAD NOTIFICATION COUNT
// =========================================================

function updateTeacherNotificationCount() {

    // Find all notifications that are still unread.
    const unreadNotifications =
        document.querySelectorAll(
            ".teacher-notification-item.unread"
        );


    // Count the unread notifications.
    const unreadCount =
        unreadNotifications.length;


    // Display the current unread count
    // on the notification bell.
    teacherNotificationCount.textContent =
        unreadCount;


    // Display the current unread count
    // inside the notification panel.
    notificationPanelCount.textContent =
        unreadCount;


    // Hide both red badges when there
    // are no unread notifications.
    if (unreadCount === 0) {
    
        teacherNotificationCount.style.display =
            "none";
    
        notificationPanelCount.style.display =
            "none";
    
    } else {
    
        // Show both red badges when there
        // are unread notifications.
        teacherNotificationCount.style.display =
            "flex";
    
        notificationPanelCount.style.display =
            "flex";
    
    }
    
}

// =========================================================
// TEACHER INDIVIDUAL NOTIFICATIONS
// =========================================================

// Find all notification items.
const teacherNotificationItems =
    document.querySelectorAll(
        ".teacher-notification-item"
    );


// Listen for clicks on every notification.
teacherNotificationItems.forEach(
    function (notification) {

        notification.addEventListener(
            "click",
            function () {

                // Remove the "unread" state.
                notification.classList.remove(
                    "unread"
                );
                
                teacherNotificationPanel.classList.remove("show");
                
                // Read the type of notification that was clicked.
                const notificationType =
                    notification.dataset.notificationType;
                
                // Decide what to do based on the
                // type of notification clicked.
                switch (notificationType) {
                
                    case "homework":
                
                        console.log(
                            "Opening Homework..."
                        );
                
                        break;
                
                
                    case "school_news":
                
                        console.log(
                            "Opening School News..."
                        );
                
                        break;
                
                
                    case "attendance":
                
                        console.log(
                            "Opening Attendance..."
                        );
                
                        break;
                
                
                    default:
                
                        console.log(
                            "Unknown notification type."
                        );
                
                }
                
                
                // Update the unread notification count.
                updateTeacherNotificationCount();

            }
        );

    }
);

// =========================================================
// TEACHER PROFILE MENU
// =========================================================

// Find the teacher profile button.
const teacherProfileButton =
    document.getElementById(
        "teacher-profile-button"
    );


// Find the teacher profile menu.
const teacherProfileMenu =
    document.getElementById(
        "teacher-profile-menu"
    );


// Listen for a click on the teacher profile.
teacherProfileButton.addEventListener(
    "click",
    function () {

        // Open or close the profile menu.
        teacherProfileMenu.classList.toggle(
            "show"
        );

    }
);

// =========================================================
// TEACHER PROFILE MENU ACTIONS
// =========================================================

// Find all profile menu items that have
// a profile action.
const teacherProfileActions =
    document.querySelectorAll(
        ".teacher-profile-menu-item[data-profile-action]"
    );

// Listen for clicks on each profile menu action.
teacherProfileActions.forEach(
    function (profileAction) {

        profileAction.addEventListener(
            "click",
            function (event) {

                // Stop the temporary href="#"
                // from jumping to the top of the page.
                event.preventDefault();

                // Read the selected profile action.
                const selectedProfileAction =
                    profileAction.dataset.profileAction;


                // Decide what should happen
                // based on the selected action.
                switch (selectedProfileAction) {

                    case "profile":

                        showTeacherNotification(
                            "👤 My Profile — Opening profile..."
                        );

                        break;


                    case "settings":

                        showTeacherNotification(
                            "⚙️ Account Settings — Opening settings..."
                        );

                        break;


                    case "change_password":

                        showTeacherNotification(
                            "🔐 Change Password — Opening password settings..."
                        );

                        break;


                    default:

                        console.log(
                            "No profile action has been configured."
                        );

                }


                // Show the selected action
                // in the browser console.
                console.log(
                    "Teacher selected profile action:",
                    selectedProfileAction
                );

            }
        );

    }
);


// =========================================================
// CLOSE PROFILE MENU WHEN CLICKING OUTSIDE
// =========================================================

// Listen for clicks anywhere on the webpage.
document.addEventListener(
    "click",
    function (event) {

        // Check whether the teacher clicked
        // inside the profile button or profile menu.
        const clickedInsideProfile =
            event.target.closest(
                ".teacher-profile"
            ) ||
            event.target.closest(
                ".teacher-profile-menu"
            );


        // If the teacher clicked outside both
        // the profile button and its menu,
        // close the profile menu.
        if (!clickedInsideProfile) {

            teacherProfileMenu.classList.remove(
                "show"
            );

        }

    }
);