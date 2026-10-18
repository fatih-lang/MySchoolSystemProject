
// ---------------------------------------------------------
// ARWA STUDENT DASHBOARD: LIVE CLOCK
// ---------------------------------------------------------

// Find the HTML elements where the date and time will appear.
const studentDateElement = document.getElementById(
    "student-current-date"
);

const studentTimeElement = document.getElementById(
    "student-current-time"
);


// Update the displayed date and time.
function updateStudentClock() {

    // Get the current date and time from the student's device.
    const now = new Date();

    // Format the date in a readable style.
    const formattedDate = now.toLocaleDateString("en-ZA", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric"
    });

    // Format the time using the device's local time zone.
    const formattedTime = now.toLocaleTimeString("en-ZA", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
    });

    // Display the updated date and time on the dashboard.
    if (studentDateElement) {
        studentDateElement.textContent = formattedDate;
    }

    if (studentTimeElement) {
        studentTimeElement.textContent = formattedTime;
    }
}


// Display the time immediately when the page loads.
updateStudentClock();

// Refresh the clock every second.
setInterval(updateStudentClock, 1000);



// ---------------------------------------------------------
// ARWA STUDENT DASHBOARD: INTERACTIVE SCHOOL CALENDAR
// ---------------------------------------------------------

// Find the HTML container where the calendar will appear.
const studentCalendar = document.getElementById(
    "student-calendar"
);

// Find the container that will display school event details.
const studentEventDetails = document.getElementById(
    "student-event-details"
);

// Read the school events supplied by Django.
const studentEventsElement = document.getElementById(
    "student-school-events"
);

// Start with an empty list in case no events are available.
let studentSchoolEvents = [];

// Convert the JSON data from Django into JavaScript data.
if (studentEventsElement) {
    try {
        studentSchoolEvents = JSON.parse(
            studentEventsElement.textContent
        );
    } catch (error) {
        console.error("Could not read school calendar events:", error);
    }
}

// Store the month currently being displayed.
const studentCalendarToday = new Date();

let studentCalendarMonth = studentCalendarToday.getMonth();
let studentCalendarYear = studentCalendarToday.getFullYear();

// Remember which date the student selects.
let studentSelectedDate = null;



// ---------------------------------------------------------
// BUILD THE CALENDAR GRID
// ---------------------------------------------------------

// Create the calendar heading and month navigation.
function renderStudentCalendar() {

    // Stop if the calendar container is missing.
    if (!studentCalendar) {
        return;
    }

    // Clear the previous month's calendar.
    studentCalendar.innerHTML = "";

    // Create a heading showing the current month and year.
    const monthHeading = document.createElement("h4");

    monthHeading.textContent = new Date(
        studentCalendarYear,
        studentCalendarMonth
    ).toLocaleDateString("en-ZA", {
        month: "long",
        year: "numeric"
    });

    // Make the heading span all seven calendar columns.
    monthHeading.style.gridColumn = "1 / -1";
    monthHeading.style.textAlign = "center";
    monthHeading.style.margin = "0 0 8px";

    studentCalendar.appendChild(monthHeading);

    // Create buttons for moving between months.
    const previousMonthButton = document.createElement("button");
    previousMonthButton.type = "button";
    previousMonthButton.textContent = "‹ Previous";

    const nextMonthButton = document.createElement("button");
    nextMonthButton.type = "button";
    nextMonthButton.textContent = "Next ›";

    // Give the month buttons a clear, clickable appearance.
    [previousMonthButton, nextMonthButton].forEach((button) => {
        button.style.padding = "8px";
        button.style.border = "none";
        button.style.borderRadius = "8px";
        button.style.backgroundColor = "#EEF2FF";
        button.style.color = "#4338CA";
        button.style.cursor = "pointer";
    });

    // Place the navigation buttons across the calendar.
    previousMonthButton.style.gridColumn = "span 3";
    nextMonthButton.style.gridColumn = "span 4";

    studentCalendar.appendChild(previousMonthButton);
    studentCalendar.appendChild(nextMonthButton);

    // Move to the previous month when clicked.
    previousMonthButton.addEventListener("click", () => {
        studentCalendarMonth--;

        // Move to the previous year if necessary.
        if (studentCalendarMonth < 0) {
            studentCalendarMonth = 11;
            studentCalendarYear--;
        }

        renderStudentCalendar();
    });

    // Move to the next month when clicked.
    nextMonthButton.addEventListener("click", () => {
        studentCalendarMonth++;

        // Move to the next year if necessary.
        if (studentCalendarMonth > 11) {
            studentCalendarMonth = 0;
            studentCalendarYear++;
        }

        renderStudentCalendar();
    });

    // Monday-to-Sunday order.
    const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    // Add the weekday headings.
    weekdays.forEach((weekday) => {
        const heading = document.createElement("div");

        heading.className = "calendar-day";
        heading.textContent = weekday;
        heading.style.fontWeight = "700";
        heading.style.backgroundColor = "#FFFFFF";

        studentCalendar.appendChild(heading);
    });

    // Find the weekday of the first day of the month.
    // JavaScript uses Sunday = 0, so convert to Monday = 0.
    const firstWeekday = new Date(
        studentCalendarYear,
        studentCalendarMonth,
        1
    ).getDay();

    const startingOffset = (firstWeekday + 6) % 7;

    // Find how many days are in this month.
    const daysInMonth = new Date(
        studentCalendarYear,
        studentCalendarMonth + 1,
        0
    ).getDate();

    // Add empty spaces before the first day.
    for (let space = 0; space < startingOffset; space++) {
        const emptyDay = document.createElement("div");
        studentCalendar.appendChild(emptyDay);
    }
    
    // Build today's date key so it is available after the loop.
    const todayKey = [
        studentCalendarToday.getFullYear(),
        String(studentCalendarToday.getMonth() + 1).padStart(2, "0"),
        String(studentCalendarToday.getDate()).padStart(2, "0")
    ].join("-");

    // Add one button for each date in the month.
    for (let day = 1; day <= daysInMonth; day++) {
        const dateButton = document .createElement("button");

        dateButton.type = "button";
        dateButton.className = "calendar-day";
        dateButton.textContent = day;

        // Give each date an accessible label.
        dateButton.setAttribute(
            "aria-label",
            `${day} ${monthHeading.textContent}`
        );

        // Build a date key such as 2026-10-09.
        const dateKey = [
            studentCalendarYear,
            String(studentCalendarMonth + 1).padStart(2, "0"),
            String(day).padStart(2, "0")
        ].join("-");

        // Compare the date with today's date.
        const todayKey = [
            studentCalendarToday.getFullYear(),
            String(studentCalendarToday.getMonth() + 1).padStart(2, "0"),
            String(studentCalendarToday.getDate()).padStart(2, "0")
        ].join("-");

        // Highlight today's date.
        if (dateKey === todayKey) {
            dateButton.classList.add("today");
        }

        // Highlight a previously selected date.
        if (dateKey === studentSelectedDate) {
            dateButton.classList.add("selected-date");
        }

        // Find events that include this date.
        const eventsForDate = studentSchoolEvents.filter((event) => {
            return (
                event.start_date <= dateKey &&
                event.end_date >= dateKey
            );
        });

        // Mark dates that have school events.
        if (eventsForDate.length > 0) {
            dateButton.classList.add("has-event");
            dateButton.title = `${eventsForDate.length} school event(s)`;
        }

        // Display events when the student taps a date.
        dateButton.addEventListener("click", () => {
            studentSelectedDate = dateKey;

            renderStudentCalendar();
            showStudentEvents(dateKey);
        });

        studentCalendar.appendChild(dateButton);
    }

    // Show today's events when opening the current month.
    if (
        studentSelectedDate === null &&
        studentCalendarYear === studentCalendarToday.getFullYear() &&
        studentCalendarMonth === studentCalendarToday.getMonth()
    ) {
        showStudentEvents(todayKey);
    } else if (studentSelectedDate) {
        showStudentEvents(studentSelectedDate);
    }
}



// ---------------------------------------------------------
// DISPLAY EVENTS FOR THE SELECTED DATE
// ---------------------------------------------------------

function showStudentEvents(dateKey) {

    // Stop if the event details container is missing.
    if (!studentEventDetails) {
        return;
    }

    // Clear event details from the previously selected date.
    studentEventDetails.innerHTML = "";

    // Display the selected date as a readable heading.
    const selectedDate = new Date(`${dateKey}T12:00:00`);

    const dateHeading = document.createElement("h4");

    dateHeading.textContent = selectedDate.toLocaleDateString("en-ZA", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric"
    });

    studentEventDetails.appendChild(dateHeading);

    // Find events that include the selected date.
    const eventsForDate = studentSchoolEvents.filter((event) => {
        return (
            event.start_date <= dateKey &&
            event.end_date >= dateKey
        );
    });

    // Explain when there are no school events on this date.
    if (eventsForDate.length === 0) {
        const noEventsMessage = document.createElement("p");

        noEventsMessage.textContent =
            "There are no school events scheduled for this date.";

        studentEventDetails.appendChild(noEventsMessage);
        return;
    }

    // Display every event scheduled for the selected date.
    eventsForDate.forEach((event) => {

        // Create a container for this event.
        const eventContainer = document.createElement("div");
        eventContainer.className = "calendar-event";

        // Display the event title.
        const eventTitle = document.createElement("strong");
        eventTitle.textContent = event.title;

        eventContainer.appendChild(eventTitle);

        // Display the event type when available.
        if (event.event_type) {
            const eventType = document.createElement("p");

            eventType.textContent = `Type: ${event.event_type}`;

            eventContainer.appendChild(eventType);
        }

        // Display the event description when available.
        if (event.description) {
            const eventDescription = document.createElement("p");

            eventDescription.textContent = event.description;

            eventContainer.appendChild(eventDescription);
        }

        // Display the event's date range.
        const eventDates = document.createElement("p");

        eventDates.textContent =
            `From ${event.start_date} to ${event.end_date}`;

        eventContainer.appendChild(eventDates);

        // Add this event to the page.
        studentEventDetails.appendChild(eventContainer);
    });
}

// ---------------------------------------------------------
// START THE STUDENT SCHOOL CALENDAR
// ---------------------------------------------------------

// Build and display the calendar when the page loads.
renderStudentCalendar();