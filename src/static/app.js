document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear and rebuild select dropdown, keeping the placeholder
      while (activitySelect.options.length > 1) {
        activitySelect.remove(activitySelect.options.length - 1);
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Use innerHTML for app-controlled header content
        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <h5>Participants (${details.participants.length}):</h5>
        `;

        // Build participants list using DOM APIs to prevent XSS
        const participantsList = document.createElement("ul");
        participantsList.className = "participants-list";

        if (details.participants.length > 0) {
          details.participants.forEach(email => {
            const li = document.createElement("li");

            const emailSpan = document.createElement("span");
            emailSpan.textContent = email;
            li.appendChild(emailSpan);

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-btn";
            deleteBtn.setAttribute("data-activity", name);
            deleteBtn.setAttribute("data-email", email);
            deleteBtn.setAttribute("title", "Remove participant");
            deleteBtn.textContent = "×";
            li.appendChild(deleteBtn);

            participantsList.appendChild(li);
          });
        } else {
          const li = document.createElement("li");
          li.className = "no-participants";
          li.textContent = "No participants yet";
          participantsList.appendChild(li);
        }

        activityCard.appendChild(participantsList);

        // Add event listeners for delete buttons
        activityCard.querySelectorAll('.delete-btn').forEach(btn => {
          btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const activityName = btn.getAttribute('data-activity');
            const email = btn.getAttribute('data-email');

            if (confirm(`Remove ${email} from ${activityName}?`)) {
              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
                  { method: 'DELETE' }
                );

                if (response.ok) {
                  fetchActivities();
                  messageDiv.textContent = `${email} removed from ${activityName}`;
                  messageDiv.className = 'success';
                } else {
                  const error = await response.json();
                  messageDiv.textContent = error.detail || 'Failed to remove participant';
                  messageDiv.className = 'error';
                }
                messageDiv.classList.remove('hidden');
                setTimeout(() => messageDiv.classList.add('hidden'), 5000);
              } catch (error) {
                console.error('Error removing participant:', error);
                messageDiv.textContent = 'Failed to remove participant';
                messageDiv.className = 'error';
                messageDiv.classList.remove('hidden');
              }
            }
          });
        });

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
