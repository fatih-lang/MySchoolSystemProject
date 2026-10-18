/* =========================================================
   ARWA GUARDIAN PORTAL
   STEP 1 — LIVE CAMPUS CLOCK
   ========================================================= */


/*
    Find the clock element in the HTML.

    JavaScript uses this ID to know where
    the current time must be displayed.
*/

const guardianClock = document.getElementById(
    "guardian-clock"
);


/*
    Create a function that updates the clock.

    A function is a reusable block of code.
    We can run it repeatedly instead of
    writing the same instructions again.
*/

function updateGuardianClock() {

    /*
        Stop safely if the clock element
        cannot be found on the page.
    */

    if (!guardianClock) {
        return;
    }


    /*
        Create a Date object representing
        the current time on the device.
    */

    const currentTime = new Date();


    /*
        Format the time using 24-hour notation.

        Example: 14:35:08

        The browser's current locale is used,
        with hours, minutes and seconds displayed.
    */

    const formattedTime = currentTime.toLocaleTimeString(
        undefined,
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        }
    );


    /*
        Replace the placeholder inside the
        clock element with the formatted time.
    */

    guardianClock.textContent = formattedTime;

}


/*
    Update the clock immediately when
    this JavaScript file runs.
*/

updateGuardianClock();


/*
    Update the clock every 1,000 milliseconds.

    1,000 milliseconds = 1 second.

    This makes the seconds change automatically.
*/

setInterval(updateGuardianClock, 1000);


/* =========================================================
   STEP 2 — SCHOOL STATUS
   ========================================================= */

/*
    Find the HTML element that displays the
    current school status.
*/

const guardianSchoolStatus = document.getElementById(
    "guardian-school-status"
);


/*
    Update the status according to the current time.

    Times use the 24-hour clock.
*/

function updateGuardianSchoolStatus() {

    // Stop if the status element is not on this page.
    if (!guardianSchoolStatus) {
        return;
    }

    // Get the current hour and minute.
    const now = new Date();

    const currentMinutes =
        now.getHours() * 60 + now.getMinutes();


    // Convert the school timetable into minutes.
    const schoolStarts = 8 * 60;
    const morningBreakStarts = 10 * 60 + 30;
    const morningBreakEnds = 11 * 60 + 30;
    const lunchStarts = 13 * 60;
    const lunchEnds = 14 * 60;

    const foundationCloses = 13 * 60;
    const intermediateSeniorClose = 14 * 60 + 30;
    const fetCloses = 16 * 60 + 30;


    /*
        Display the appropriate status.

        This initial version describes the school day
        generally. We'll make it phase-specific later.
    */

    if (currentMinutes < schoolStarts) {

        guardianSchoolStatus.textContent =
            "School has not opened yet";

    } else if (currentMinutes < morningBreakStarts) {

        guardianSchoolStatus.textContent =
            "School is in session";

    } else if (currentMinutes < morningBreakEnds) {

        guardianSchoolStatus.textContent =
            "Morning break";

    } else if (
        currentMinutes >= lunchStarts &&
        currentMinutes < lunchEnds
    ) {

        guardianSchoolStatus.textContent =
            "Lunch time";

    } else if (currentMinutes < foundationCloses) {

        guardianSchoolStatus.textContent =
            "School is in session";

    } else if (currentMinutes < intermediateSeniorClose) {

        guardianSchoolStatus.textContent =
            "Foundation Phase has closed";

    } else if (currentMinutes < fetCloses) {

        guardianSchoolStatus.textContent =
            "Intermediate and Senior Phases have closed";

    } else {

        guardianSchoolStatus.textContent =
            "All phases have closed";

    }

}


/*
    Display the correct status immediately,
    then check again every minute.
*/

updateGuardianSchoolStatus();

setInterval(updateGuardianSchoolStatus, 60 * 1000);


/* =========================================================
   STEP 18 — INTERACTIVE GUARDIAN CALENDAR
   ========================================================= */

// Find the calendar container in the HTML.
const guardianCalendar = document.getElementById(
    "guardian-calendar"
);


// Find the area where school-event details will appear.
const guardianEventDetails = document.getElementById(
    "guardian-event-details"
);


// Find the calendar-event data provided by Django.
const guardianEventsData = document.getElementById(
    "guardian-school-events"
);

// Read the events safely from Django's JSON data.
const guardianSchoolEvents = guardianEventsData
    ? JSON.parse(guardianEventsData.textContent)
    : [];
    
    
// Check whether a date falls within a school event.
function guardianHasEventOnDate(dateString) {

    // Check every event supplied by Django.
    return guardianSchoolEvents.some(function (event) {

        // Include every date from the start through the end.
        return (
            dateString >= event.start_date &&
            dateString <= event.end_date
        );
    });
}


// Find and display school events for the selected calendar date.
function guardianShowEventsForDate(dateString) {

    // Stop if the event-details area is missing.
    if (!guardianEventDetails) {
        return;
    }

    // Find every event that includes the selected date.
    const matchingEvents = guardianSchoolEvents.filter(
        function (event) {
            return (
                dateString >= event.start_date &&
                dateString <= event.end_date
            );
        }
    );

    // Split YYYY-MM-DD into numbers to avoid date-format issues.
    const dateParts = dateString.split("-").map(Number);

    // Create the selected date using the local calendar.
    const selectedDate = new Date(
        dateParts[0],
        dateParts[1] - 1,
        dateParts[2]
    );

    // Format the date so it is easy to read.
    const readableDate = selectedDate.toLocaleDateString(
        undefined,
        {
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );

    // Clear the previous event details.
    guardianEventDetails.replaceChildren();

    // Display the selected date as a heading.
    const dateHeading = document.createElement("h4");
    dateHeading.textContent = "Events for " + readableDate;
    guardianEventDetails.appendChild(dateHeading);

    // Display a message if there are no events.
    if (matchingEvents.length === 0) {
        const noEventsMessage = document.createElement("p");
        noEventsMessage.textContent =
            "No school events on this date.";

        guardianEventDetails.appendChild(noEventsMessage);
        return;
    }

    // Display each event scheduled for the selected date.
    matchingEvents.forEach(function (event) {

        // Display the event title.
        const eventTitle = document.createElement("h5");
        eventTitle.textContent = event.title;
        guardianEventDetails.appendChild(eventTitle);

        // Display the event description.
        const eventDescription = document.createElement("p");
        eventDescription.textContent =
            event.description || "No additional details.";

        guardianEventDetails.appendChild(eventDescription);

        // Display the event type.
        const eventType = document.createElement("p");
        eventType.textContent =
            "Type: " + event.event_type;

        guardianEventDetails.appendChild(eventType);
    });
}



// Remember which month the calendar is displaying.
// Start with the current month.
let displayedCalendarDate = new Date();

displayedCalendarDate.setDate(1);


/* ---------------------------------------------------------
   BUILD AND DISPLAY THE CALENDAR
   --------------------------------------------------------- */

function renderGuardianCalendar() {

    // Stop safely if the calendar is not on the page.
    if (!guardianCalendar) {
        return;
    }

    // Clear the previous calendar before drawing a new one.
    guardianCalendar.replaceChildren();

    // Get the month and year currently being displayed.
    const year = displayedCalendarDate.getFullYear();
    const month = displayedCalendarDate.getMonth();

    // Get today's date from the device.
    const today = new Date();

    // Create the calendar heading.
    const calendarHeader = document.createElement("div");
    calendarHeader.className = "calendar-header";

    // Previous-month button.
    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.textContent = "‹";
    previousButton.setAttribute(
        "aria-label",
        "Previous month"
    );

    // Display the current calendar month and year.
    const monthTitle = document.createElement("h3");

    monthTitle.textContent = displayedCalendarDate.toLocaleDateString(
        undefined,
        {
            month: "long",
            year: "numeric"
        }
    );

    // Next-month button.
    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.textContent = "›";
    nextButton.setAttribute(
        "aria-label",
        "Next month"
    );

    // Place the buttons and heading inside the header.
    calendarHeader.append(
        previousButton,
        monthTitle,
        nextButton
    );

    guardianCalendar.appendChild(calendarHeader);


    /* -----------------------------------------------------
       WEEKDAY NAMES — MONDAY TO SUNDAY
       ----------------------------------------------------- */

    const weekdays = document.createElement("div");
    weekdays.className = "calendar-weekdays";

    const weekdayNames = [
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    ];

    weekdayNames.forEach(function (dayName) {

        const weekday = document.createElement("div");

        weekday.textContent = dayName;

        weekdays.appendChild(weekday);
    });

    guardianCalendar.appendChild(weekdays);


    /* -----------------------------------------------------
       CALCULATE AND DISPLAY THE DAYS
       ----------------------------------------------------- */

    const calendarDays = document.createElement("div");
    calendarDays.className = "calendar-days";

    // Find the weekday of the first day of this month.
    const firstDay = new Date(year, month, 1);

    // Convert Sunday-first numbering to Monday-first.
    const startingDay = (firstDay.getDay() + 6) % 7;

    // Find the number of days in this month.
    const numberOfDays = new Date(
        year,
        month + 1,
        0
    ).getDate();

    // Add empty spaces before day 1 where necessary.
    for (let i = 0; i < startingDay; i++) {

        const emptyDay = document.createElement("div");

        emptyDay.className = "calendar-day empty";

        calendarDays.appendChild(emptyDay);
    }

    // Add every date in the month.
    for (let day = 1; day <= numberOfDays; day++) {

        const dayCell = document.createElement("div");

        dayCell.className = "calendar-day";
        dayCell.textContent = day;

        // Highlight today's date.
        const isToday =
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear();

        if (isToday) {
            dayCell.classList.add("today");
        }
        
        // Build this date in YYYY-MM-DD format.
        const eventDate = [
            year,
            String(month + 1).padStart(2, "0"),
            String(day).padStart(2, "0")
        ].join("-");
        
        // Highlight dates that contain school events.
        if (guardianHasEventOnDate(eventDate)) {
            dayCell.classList.add("has-event");
        }
        
        
        // Allow the guardian to select a calendar date.
        dayCell.addEventListener("click", function () {
        
            // Remove the previous selection from every calendar day.
            document.querySelectorAll(
                "#guardian-calendar .calendar-day"
            ).forEach(function (calendarDay) {
                calendarDay.classList.remove("selected-date");
            });
        
            // Highlight the date that was just tapped.
            dayCell.classList.add("selected-date");
        
            // Display events for the selected date.
            guardianShowEventsForDate(eventDate);
        
        });


        calendarDays.appendChild(dayCell);
    }

    guardianCalendar.appendChild(calendarDays);


    /* -----------------------------------------------------
       MONTH NAVIGATION BUTTONS
       ----------------------------------------------------- */

    // Move backwards by one month.
    previousButton.addEventListener("click", function () {

        displayedCalendarDate.setMonth(
            displayedCalendarDate.getMonth() - 1
        );

        renderGuardianCalendar();
    });

    // Move forwards by one month.
    nextButton.addEventListener("click", function () {

        displayedCalendarDate.setMonth(
            displayedCalendarDate.getMonth() + 1
        );

        renderGuardianCalendar();
    });
}


// Display the calendar when the page loads.
renderGuardianCalendar();
