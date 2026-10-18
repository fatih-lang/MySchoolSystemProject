
/* ---------------------------------------------------------
  SIDEBAR SECTION TOGGLE
  Opens and closes a Principal sidebar section.
--------------------------------------------------------- */

    
/* ---------------------------------------------------------
   SIDEBAR SECTION TOGGLE
   Opens one section and closes the others.
--------------------------------------------------------- */
function toggleSidebarSection(menuId, button) {

        // Find the submenu that belongs to the clicked button.
        const menu = document.getElementById(menuId);

        // Find all currently open sidebar submenus.
        const openMenus = document.querySelectorAll(
            ".sidebar-submenu.open"
        );

        // Close every other open submenu.
        openMenus.forEach(function(openMenu) {

            if (openMenu !== menu) {

                // Remove the open class.
                openMenu.classList.remove("open");

                // Find the button belonging to this submenu.
                const otherButton =
                    openMenu.previousElementSibling;

                // Find its arrow.
                const otherArrow =
                    otherButton.querySelector(
                        ".sidebar-section-arrow"
                    );

                // Change the arrow back to the right.
                otherArrow.textContent = "▶";
            }
        });

        // Find the arrow of the clicked section.
        const arrow = button.querySelector(
            ".sidebar-section-arrow"
        );

        // Check whether the clicked menu is closed.
        if (!menu.classList.contains("open")) {

            // Open the clicked menu.
            menu.classList.add("open");

            // Change the arrow to down.
            arrow.textContent = "▼";

        } else {

            // Close the clicked menu.
            menu.classList.remove("open");

            // Change the arrow back to right.
            arrow.textContent = "▶";
        }
}

/* ---------------------------------------------------------
    LIVE DASHBOARD CLOCK
    Displays the current time and updates every second.
--------------------------------------------------------- */

function updateDashboardClock() {

        // Get the current date and time from the device.
        const now = new Date();

        // Convert the time into a readable format.
        const time = now.toLocaleTimeString();

        // Find the clock element in the header.
        const clock = document.getElementById("dashboard-clock");

        // Display the current time.
        clock.textContent = time;
}


// Run the clock immediately when the page loads.
updateDashboardClock();


// Update the clock every 1 second.
setInterval(updateDashboardClock, 1000);
    

/* ---------------------------------------------------------
   PRINCIPAL PROFILE MENU
   Opens and closes the profile dropdown menu.
--------------------------------------------------------- */

function togglePrincipalProfileMenu() {

        // Find the principal profile dropdown menu.
        const menu = document.getElementById(
            "principal-profile-menu"
        );

        // Add or remove the "open" class.
        menu.classList.toggle("open");
} 

/* ---------------------------------------------------------
    CLOSE PROFILE MENU WHEN CLICKING OUTSIDE
    Keeps the dashboard clean and user-friendly.
   --------------------------------------------------------- */

document.addEventListener("click", function(event) {

        // Find the profile container.
        const profileContainer =
            document.querySelector(
                ".principal-profile-container"
            );

        // Find the profile dropdown menu.
        const profileMenu =
            document.getElementById(
                "principal-profile-menu"
            );

        // Check whether the click happened outside
        // the profile area.
        if (
            !profileContainer.contains(event.target)
        ) {

            // Close the profile menu.
            profileMenu.classList.remove("open");
        }
});  


// =========================================================
// PRINCIPAL NOTIFICATION BUTTON
// =========================================================

// Find the principal notification button.
const principalNotificationButton =
    document.getElementById(
        "principal-notification-button"
    );


// Find the notification panel.
const principalNotificationPanel =
    document.getElementById(
        "principal-notification-panel"
    );
    
const principalNotificationCount =
    document.getElementById(
        "principal-notification-count"
    );    
    
// Find the unread count inside the notification panel.
const notificationPanelCount =
    document.getElementById(
        "notification-panel-count"
    );    


// Listen for a click on the notification bell.
principalNotificationButton.addEventListener(
    "click",
    function () {

        // Add or remove the "show" class.
        principalNotificationPanel.classList.toggle(
            "show"
        );

    }
);

// =========================================================
// CLOSE NOTIFICATION PANEL WHEN CLICKING OUTSIDE
// =========================================================

document.addEventListener(
    "click",
    function (event) {

        // Check whether the user clicked
        // inside the notification container.
        const clickedInsideNotification =
            event.target.closest(
                ".principal-notification-container"
            );

        // If the user clicked somewhere outside
        // the notification container,
        // close the notification panel.
        if (!clickedInsideNotification) {

            principalNotificationPanel.classList.remove(
                "show"
            );

        }

    }
);

// =========================================================
// UPDATE UNREAD NOTIFICATION COUNT
// =========================================================

function updatePrincipalNotificationCount() {

    // Find all notifications that are still unread.
    const unreadNotifications =
        document.querySelectorAll(
            ".principal-notification-item.unread"
        );


    // Count the unread notifications.
    const unreadCount =
        unreadNotifications.length;


    // Display the current unread count
    // on the notification bell.
    principalNotificationCount.textContent =
        unreadCount;


    // Display the current unread count
    // inside the notification panel.
    notificationPanelCount.textContent =
        unreadCount;


    // Hide both red badges when there
    // are no unread notifications.
    if (unreadCount === 0) {
    
        principalNotificationCount.style.display =
            "none";
    
        notificationPanelCount.style.display =
            "none";
    
    } else {
    
        // Show both red badges when there
        // are unread notifications.
        principalNotificationCount.style.display =
            "flex";
    
        notificationPanelCount.style.display =
            "flex";
    
    }
    
}

// =========================================================
// PRINCIPAL INDIVIDUAL NOTIFICATIONS
// =========================================================

// Find all notification items.
const principalNotificationItems =
    document.querySelectorAll(
        ".principal-notification-item"
    );


// Listen for clicks on every notification.
principalNotificationItems.forEach(
    function (notification) {

        notification.addEventListener(
            "click",
            function () {

                // Remove the "unread" state.
                notification.classList.remove(
                    "unread"
                );
                
                principalNotificationPanel.classList.remove("show");
                
                // Read the type of notification that was clicked.
                const notificationType =
                    notification.dataset.notificationType;
                
                // Decide what to do based on the
                // type of notification clicked.
                switch (notificationType) {
                
                    case "registered_student":
                
                        console.log(
                            "Opening New student registration..."
                        );
                
                        break;
                
                
                    case "fees_paid":
                
                        console.log(
                            "Opening fees payment..."
                        );
                
                        break;
                
                
                    case "parents_meeting":
                
                        console.log(
                            "Opening parents meeting ..."
                        );
                
                        break;
                
                
                    default:
                
                        console.log(
                            "Unknown notification type."
                        );
                
                }
                
                
                /*  Update the unread notification count.
                    What this gives us
                    If there are:
                    3 unread → 🔔 3
                    2 unread → 🔔 2
                    1 unread → 🔔 1
                    0 unread → the badge disappears
                */
                updatePrincipalNotificationCount();

            }
        );

    }
);


// =========================================================
// PRINCIPAL CALENDAR
// =========================================================

/* Create each day of the month.
   What this function is doing
   This is the part that makes our calendar dynamic.
   JavaScript calculates:
   📅 Which month we're displaying
   🗓️ Which weekday the month starts on
   🔢 How many days the month contains
   🧱 How many empty spaces are needed before day 1
   ➕ Creates each date automatically
   For example, if the month starts on Thursday, JavaScript creates empty spaces for:
   Sun  Mon  Tue  Wed  Thu
                         1
   instead of us manually positioning the dates.
*/

// Get the calendar elements from the page.
const principalCalendarDays =
    document.getElementById(
        "principal-calendar-days"
    );

const calendarMonthYear =
    document.getElementById(
        "calendar-month-year"
    );
    
const schoolEventDetails =
    document.getElementById(
        "school-event-details"
    );

// Read the school events safely from Django.
const principalSchoolEvents =
    JSON.parse(
        document.getElementById(
            "principal-school-events-data"
        ).textContent
    );

// Keep track of the month currently being displayed.
let calendarCurrentDate = new Date();


// =========================================================
// DISPLAY THE CALENDAR
// =========================================================

function renderPrincipalCalendar() {

    // Get the current month and year.
    const year =
        calendarCurrentDate.getFullYear();

    const month =
        calendarCurrentDate.getMonth();

    // Find the first day of the month.
    const firstDay =
        new Date(
            year,
            month,
            1
        ).getDay();

    // Find the number of days in the month.
    const daysInMonth =
        new Date(
            year,
            month + 1,
            0
        ).getDate();

    // Display the month and year.
    const monthName =
        calendarCurrentDate.toLocaleString(
            "default",
            {
                month: "long"
            }
        );

    calendarMonthYear.textContent =
        monthName + " " + year;


    // Clear any dates already displayed.
    principalCalendarDays.innerHTML = "";


    // Add empty spaces before the first day.
    for (
        let i = 0;
        i < firstDay;
        i++
    ) {

        const emptyDay =
            document.createElement(
                "div"
            );

        principalCalendarDays.appendChild(
            emptyDay
        );
    }


    // Create each day of the month.
    for (
        let day = 1;
        day <= daysInMonth;
        day++
    ) {

        const dayButton =
            document.createElement(
                "button"
            );

        dayButton.type = "button";

        dayButton.className =
            "principal-calendar-day";
        
        // Check whether this date is today.
        const today = new Date();
        
        if (
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()
        ) {
        
            dayButton.classList.add(
                "today"
            );
        
        } 
        
        // Check whether this date has a school event.
        const hasSchoolEvent =
            principalSchoolEvents.some(
                function (event) {
        
                    const dateKey =
                        `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        
                    return (
                        event.start_date <= dateKey &&
                        event.end_date >= dateKey
                    );
                }
            );
        
        if (hasSchoolEvent) {
        
            dayButton.classList.add(
                "has-event"
            );
        }
            

        dayButton.textContent =
            day;
            
        // Create the full date in YYYY-MM-DD format.
        const dateKey =
            `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        
        // Show school events when this date is selected.
        dayButton.addEventListener(
            "click",
            function () {
        
                showSchoolEvents(dateKey);
        
            }
        );    

        principalCalendarDays.appendChild(
            dayButton
        );
    }
}


// ---------------------------------------------------------
// DISPLAY EVENTS FOR THE SELECTED DATE
// ---------------------------------------------------------

/*
    renderPrincipalCalendar() → creates the dates.
    showSchoolEvents(dateKey) → displays events for a selected date.
    principalSchoolEvents → holds the school's events.
    schoolEventDetails → the place where event details will appear.
*/

function showSchoolEvents(dateKey) {

    // Stop if the event details container is missing.
    if (!schoolEventDetails) {
        return;
    }

    // Clear event details from the previously selected date.
    schoolEventDetails.innerHTML = "";

    // Convert the selected date into a JavaScript Date object.
    const selectedDate =
        new Date(`${dateKey}T12:00:00`);

    // Create a heading for the selected date.
    const dateHeading =
        document.createElement("h4");

    // Display the date in a readable format.
    dateHeading.textContent =
        selectedDate.toLocaleDateString(
            "en-ZA",
            {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );

    // Add the date heading to the page.
    schoolEventDetails.appendChild(
        dateHeading
    );


    // ---------------------------------------------------------
    // FIND EVENTS FOR THE SELECTED DATE
    // ---------------------------------------------------------

    const eventsForDate =
        principalSchoolEvents.filter(
            function (event) {

                return (
                    event.start_date <= dateKey &&
                    event.end_date >= dateKey
                );

            }
        );


    // ---------------------------------------------------------
    // NO EVENTS FOUND
    // ---------------------------------------------------------

    if (eventsForDate.length === 0) {

        const noEventsMessage =
            document.createElement("p");

        noEventsMessage.textContent =
            "There are no school events scheduled for this date.";

        schoolEventDetails.appendChild(
            noEventsMessage
        );

        return;
    }


    // ---------------------------------------------------------
    // DISPLAY EVENTS
    // ---------------------------------------------------------

    eventsForDate.forEach(
        function (event) {

            // Create a container for the event.
            const eventContainer =
                document.createElement("div");

            eventContainer.className =
                "calendar-event";


            // Display the event title.
            const eventTitle =
                document.createElement("strong");

            eventTitle.textContent =
                event.title;

            eventContainer.appendChild(
                eventTitle
            );


            // Display the event type when available.
            if (event.event_type) {

                const eventType =
                    document.createElement("p");

                eventType.textContent =
                    `Type: ${event.event_type}`;

                eventContainer.appendChild(
                    eventType
                );
            }


            // Display the event description when available.
            if (event.description) {

                const eventDescription =
                    document.createElement("p");

                eventDescription.textContent =
                    event.description;

                eventContainer.appendChild(
                    eventDescription
                );
            }


            // Display the event date range.
            const eventDates =
                document.createElement("p");

            eventDates.textContent =
                `From ${event.start_date} to ${event.end_date}`;

            eventContainer.appendChild(
                eventDates
            );


            // Add the event to the page.
            schoolEventDetails.appendChild(
                eventContainer
            );
        }
    );
}

// Display the calendar when the page loads.
renderPrincipalCalendar();
 

// =========================================================
// OPEN AND CLOSE PRINCIPAL CALENDAR
// =========================================================

/*
    What this does
    When you tap:
    📅
    JavaScript toggles the:
    show
    class.
    And remember we already created:
    .principal-calendar-panel.show {
        display: block;
    }
    So:
    Tap 📅 → panel opens
    Tap 📅 again → panel closes
*/

const principalCalendarButton =
    document.getElementById(
        "principal-calendar-button"
    );

const principalCalendarPanel =
    document.getElementById(
        "principal-calendar-panel"
    );

principalCalendarButton.addEventListener(
    "click",
    function () {

        principalCalendarPanel.classList.toggle(
            "show"
        );

    }
);

// =========================================================
// CALENDAR MONTH NAVIGATION
// =========================================================

/*
    What happens now?
    If you're viewing October 2026:
    ◀        October 2026        ▶
    Tap ◀:
    ◀       September 2026       ▶
    Tap ▶:
    ◀        October 2026        ▶
    And the dates will automatically regenerate for the selected month.
    This is possible because we already have:
    renderPrincipalCalendar();
    which rebuilds the calendar whenever calendarCurrentDate changes.
*/

// Go to the previous month.
document.getElementById(
    "calendar-previous-month"
).addEventListener(
    "click",
    function () {

        calendarCurrentDate.setMonth(
            calendarCurrentDate.getMonth() - 1
        );

        renderPrincipalCalendar();
    }
);


// Go to the next month.
document.getElementById(
    "calendar-next-month"
).addEventListener(
    "click",
    function () {

        calendarCurrentDate.setMonth(
            calendarCurrentDate.getMonth() + 1
        );

        renderPrincipalCalendar();
    }
);


// =========================================================
// CLOSE CALENDAR WHEN CLICKING OUTSIDE
// =========================================================

document.addEventListener(
    "click",
    function (event) {

        // Check whether the click happened
        // inside the calendar container.
        const clickedInsideCalendar =
            event.target.closest(
                ".principal-calendar-container"
            );

        // If the click happened outside
        // the calendar container, close the panel.
        if (!clickedInsideCalendar) {

            principalCalendarPanel.classList.remove(
                "show"
            );

        }

    }
);