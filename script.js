const STORAGE_KEY = "embark-state-v1";
const USERS_STORAGE_KEY = "embark-users-v1";
const SESSION_STORAGE_KEY = "embark-session-v1";

const initialState = {
  dogs: [
    {
      id: 1,
      name: "Sunny",
      breed: "Golden Retriever",
      birthdate: "2021-05-14",
      sex: "Female",
      photo:
        "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80",
      saved: true,
      pedigree: {
        father: "Cedar Ridge Atlas",
        mother: "Willow Creek Nova",
        notes: "Strong working lineage with award-winning siblings."
      }
    },
    {
      id: 2,
      name: "Rex",
      breed: "Labrador Retriever",
      birthdate: "2019-09-02",
      sex: "Male",
      photo:
        "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?auto=format&fit=crop&w=900&q=80",
      saved: true,
      pedigree: {
        father: "Summit Harbor Ranger",
        mother: "Meadowfield Bella",
        notes: "Balanced temperament and excellent field record."
      }
    },
    {
      id: 3,
      name: "Mia",
      breed: "Bernese Mountain Dog",
      birthdate: "2020-11-21",
      sex: "Female",
      photo:
        "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=900&q=80",
      saved: false,
      pedigree: {
        father: "Northstar Bruno",
        mother: "Snowline Tessa",
        notes: "Gentle family dog with strong structure."
      }
    }
  ],
  owner: {
    name: "Jordan Lee",
    email: "jordan@example.com",
    dogsListed: 3
  },
  notifications: {
    email: true,
    inApp: true,
    pedigreeUpdates: true,
    reminders: true
  },
  preferences: {
    display: "Grid",
    privacy: "Shared with breeder network",
    defaultView: "Grid"
  }
};

let state = loadState();

function loadState() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (!stored) {
      return structuredClone(initialState);
    }

    return {
      dogs: stored.dogs || initialState.dogs,
      owner: { ...initialState.owner, ...(stored.owner || {}) },
      notifications: { ...initialState.notifications, ...(stored.notifications || {}) },
      preferences: { ...initialState.preferences, ...(stored.preferences || {}) }
    };
  } catch (error) {
    return structuredClone(initialState);
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(element, message, isError = false) {
  if (!element) return;
  element.textContent = message;
  element.className = `form-status${isError ? " error" : ""}`;
}

function normalizeEmail(email) {
  return email.trim().toLowerCase();
}

function passwordMeetsRequirements(password) {
  return password.length >= 8 && /[A-Z]/.test(password) && /[^A-Za-z0-9]/.test(password);
}

async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function getStoredUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_STORAGE_KEY)) || [];
  } catch (error) {
    return [];
  }
}

function saveStoredUsers(users) {
  localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
}

function getCurrentSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY));
  } catch (error) {
    return null;
  }
}

function setCurrentSession(user) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
}

function clearCurrentSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

function protectRoute() {
  const currentPage = window.location.pathname.split("/").pop();
  const protectedPages = ["homepage.html", "saved-dogs.html", "pedigrees.html", "profile.html", "notifications.html", "settings.html"];
  const publicPages = ["login.html", "create-account.html", "index.html"];

  if (protectedPages.includes(currentPage) && !getCurrentSession()) {
    window.location.href = "login.html";
    return;
  }

  if (publicPages.includes(currentPage) && getCurrentSession() && currentPage !== "index.html") {
    window.location.href = "homepage.html";
  }
}

function bindAuthForms() {
  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = document.getElementById("login-status");
      const email = normalizeEmail(loginForm.email.value);
      const password = loginForm.password.value;

      const users = getStoredUsers();
      const user = users.find((entry) => entry.email === email);

      if (!user) {
        setStatus(status, "No account found for that email.", true);
        return;
      }

      const enteredHash = await hashPassword(password);
      if (enteredHash !== user.passwordHash) {
        setStatus(status, "Incorrect password.", true);
        return;
      }

      setCurrentSession({ id: user.id, email: user.email, fullName: user.fullName });
      setStatus(status, "Signing you in...");
      window.location.href = "homepage.html";
    });
  }

  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = document.getElementById("signup-status");
      const fullName = signupForm.fullName.value.trim();
      const email = normalizeEmail(signupForm.email.value);
      const password = signupForm.password.value;
      const confirmPassword = signupForm.confirmPassword.value;

      if (!fullName) {
        setStatus(status, "Please enter your full name.", true);
        return;
      }

      if (password !== confirmPassword) {
        setStatus(status, "Passwords do not match.", true);
        return;
      }

      if (!passwordMeetsRequirements(password)) {
        setStatus(status, "Password must be at least 8 characters, include one capital letter, and one special character.", true);
        return;
      }

      const users = getStoredUsers();
      if (users.some((entry) => entry.email === email)) {
        setStatus(status, "An account with that email already exists.", true);
        return;
      }

      const passwordHash = await hashPassword(password);
      const newUser = {
        id: Date.now(),
        fullName,
        email,
        passwordHash,
        createdAt: new Date().toISOString()
      };

      users.push(newUser);
      saveStoredUsers(users);
      setCurrentSession({ id: newUser.id, email: newUser.email, fullName: newUser.fullName });
      setStatus(status, "Account created successfully. Redirecting...");
      window.location.href = "homepage.html";
    });
  }
}

function renderDogList(container, mode) {
  if (!container) return;

  const dogs = mode === "saved" ? state.dogs.filter((dog) => dog.saved) : state.dogs;

  if (!dogs.length) {
    container.innerHTML = '<p class="empty-state">No dogs to show yet.</p>';
    return;
  }

  container.innerHTML = dogs
    .map(
      (dog) => `
        <article class="dog-card">
          <img src="${dog.photo}" alt="${escapeHtml(dog.name)}" />
          <div class="dog-info">
            <div class="card-header">
              <h3>${escapeHtml(dog.name)}</h3>
              <button type="button" class="secondary-btn small-btn edit-dog-toggle" data-dog-id="${dog.id}">Edit</button>
            </div>
            <p><strong>Breed:</strong> ${escapeHtml(dog.breed)}</p>
            <p><strong>Birthdate:</strong> ${escapeHtml(dog.birthdate)}</p>
            <p><strong>Sex:</strong> ${escapeHtml(dog.sex)}</p>
            <div class="card-actions">
              <button type="button" class="secondary-btn toggle-save-btn" data-dog-id="${dog.id}">${dog.saved ? "Unsave" : "Save Dog"}</button>
              <a class="secondary-btn inline-link" href="pedigrees.html">View Pedigree</a>
            </div>
            <form class="editor-form dog-edit-form hidden" data-dog-form="${dog.id}">
              <label>
                <span>Name</span>
                <input type="text" name="name" value="${escapeHtml(dog.name)}" required />
              </label>
              <label>
                <span>Breed</span>
                <input type="text" name="breed" value="${escapeHtml(dog.breed)}" required />
              </label>
              <label>
                <span>Birthdate</span>
                <input type="date" name="birthdate" value="${dog.birthdate}" required />
              </label>
              <label>
                <span>Sex</span>
                <input type="text" name="sex" value="${escapeHtml(dog.sex)}" required />
              </label>
              <label>
                <span>Photo URL</span>
                <input type="url" name="photo" value="${escapeHtml(dog.photo)}" required />
              </label>
              <div class="form-actions">
                <button type="submit">Save</button>
              </div>
            </form>
          </div>
        </article>
      `
    )
    .join("");

  container.querySelectorAll(".edit-dog-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const form = container.querySelector(`[data-dog-form="${button.dataset.dogId}"]`);
      if (form) {
        form.classList.toggle("hidden");
      }
    });
  });

  container.querySelectorAll(".toggle-save-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const dogId = Number(button.dataset.dogId);
      const dog = state.dogs.find((entry) => entry.id === dogId);
      if (dog) {
        dog.saved = !dog.saved;
        saveState();
        renderDogList(container, mode);
      }
    });
  });

  container.querySelectorAll(".dog-edit-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const dogId = Number(form.dataset.dogForm);
      const dog = state.dogs.find((entry) => entry.id === dogId);
      if (!dog) return;

      dog.name = form.name.value.trim();
      dog.breed = form.breed.value.trim();
      dog.birthdate = form.birthdate.value;
      dog.sex = form.sex.value.trim();
      dog.photo = form.photo.value.trim();
      saveState();
      renderDogList(container, mode);
    });
  });
}

function renderPedigreeList(container) {
  if (!container) return;

  container.innerHTML = state.dogs
    .map(
      (dog) => `
        <article class="info-card">
          <h3>${escapeHtml(dog.name)}</h3>
          <p><strong>Father:</strong> ${escapeHtml(dog.pedigree.father)}</p>
          <p><strong>Mother:</strong> ${escapeHtml(dog.pedigree.mother)}</p>
          <p><strong>Notes:</strong> ${escapeHtml(dog.pedigree.notes)}</p>
          <form class="editor-form pedigree-form" data-pedigree-form="${dog.id}">
            <label>
              <span>Father</span>
              <input type="text" name="father" value="${escapeHtml(dog.pedigree.father)}" />
            </label>
            <label>
              <span>Mother</span>
              <input type="text" name="mother" value="${escapeHtml(dog.pedigree.mother)}" />
            </label>
            <label>
              <span>Notes</span>
              <textarea name="notes">${escapeHtml(dog.pedigree.notes)}</textarea>
            </label>
            <div class="form-actions">
              <button type="submit">Save</button>
            </div>
          </form>
        </article>
      `
    )
    .join("");

  container.querySelectorAll(".pedigree-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const dogId = Number(form.dataset.pedigreeForm);
      const dog = state.dogs.find((entry) => entry.id === dogId);
      if (!dog) return;
      dog.pedigree.father = form.father.value.trim();
      dog.pedigree.mother = form.mother.value.trim();
      dog.pedigree.notes = form.notes.value.trim();
      saveState();
      renderPedigreeList(container);
    });
  });
}

function bindProfileForm() {
  const form = document.getElementById("profile-form");
  const status = document.getElementById("profile-status");
  if (!form) return;

  form.name.value = state.owner.name;
  form.email.value = state.owner.email;
  form.dogsListed.value = state.owner.dogsListed;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.owner.name = form.name.value.trim();
    state.owner.email = form.email.value.trim();
    state.owner.dogsListed = Number(form.dogsListed.value) || state.dogs.length;
    saveState();
    setStatus(status, "Profile updated successfully.");
  });
}

function bindNotificationForm() {
  const form = document.getElementById("notification-form");
  const status = document.getElementById("notification-status");
  if (!form) return;

  form.email.checked = state.notifications.email;
  form.inApp.checked = state.notifications.inApp;
  form.pedigreeUpdates.checked = state.notifications.pedigreeUpdates;
  form.reminders.checked = state.notifications.reminders;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.notifications.email = form.email.checked;
    state.notifications.inApp = form.inApp.checked;
    state.notifications.pedigreeUpdates = form.pedigreeUpdates.checked;
    state.notifications.reminders = form.reminders.checked;
    saveState();
    setStatus(status, "Notification settings updated.");
  });
}

function bindPreferencesForm() {
  const form = document.getElementById("preferences-form");
  const status = document.getElementById("preferences-status");
  if (!form) return;

  form.display.value = state.preferences.display;
  form.privacy.value = state.preferences.privacy;
  form.defaultView.value = state.preferences.defaultView;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    state.preferences.display = form.display.value;
    state.preferences.privacy = form.privacy.value;
    state.preferences.defaultView = form.defaultView.value;
    saveState();
    setStatus(status, "Preferences updated.");
  });
}

function bindAddDogForm() {
  const form = document.getElementById("add-dog-form");
  const toggleButton = document.getElementById("toggle-add-dog-form");
  const cancelButton = document.getElementById("cancel-add-dog");
  const status = document.getElementById("add-dog-status");

  if (!form) return;

  const toggleForm = () => {
    form.classList.toggle("hidden");
  };

  toggleButton?.addEventListener("click", toggleForm);
  cancelButton?.addEventListener("click", toggleForm);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const newDog = {
      id: Date.now(),
      name: form.name.value.trim(),
      breed: form.breed.value.trim(),
      birthdate: form.birthdate.value,
      sex: form.sex.value.trim(),
      photo: form.photo.value.trim() || "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80",
      saved: false,
      pedigree: {
        father: "",
        mother: "",
        notes: ""
      }
    };

    state.dogs.unshift(newDog);
    state.owner.dogsListed = state.dogs.length;
    saveState();
    form.reset();
    form.classList.add("hidden");
    setStatus(status, `${newDog.name} added to your dog profiles.`);
    renderDogList(document.getElementById("dog-list"), "home");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  protectRoute();
  bindAuthForms();
  renderDogList(document.getElementById("dog-list"), "home");
  renderDogList(document.getElementById("saved-dogs-list"), "saved");
  renderPedigreeList(document.getElementById("pedigree-list"));
  bindProfileForm();
  bindNotificationForm();
  bindPreferencesForm();
  bindAddDogForm();
});
