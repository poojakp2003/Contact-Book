// Mobile Contacts Application JavaScript with Groups & Favorites

const state = {
  contacts: [],
  selectedContact: null,
  editingContact: null,
  currentFilter: 'all', // 'all', 'favorites', 'Family', 'Friends', 'Work', 'College', 'Other'
};

// DOM Elements
const listContainer = document.querySelector('#contactsAlphabeticalList');
const alphabetScrubber = document.querySelector('#alphabetScrubber');
const emptyState = document.querySelector('#emptyState');
const searchInput = document.querySelector('#searchInput');
const clearSearchBtn = document.querySelector('#clearSearch');
const contactCountEl = document.querySelector('#contactCount');
const filterTabs = document.querySelectorAll('.filter-tab');

const detailPane = document.querySelector('#detailPane');
const detailPlaceholder = document.querySelector('#detailPlaceholder');
const detailContent = document.querySelector('#detailContent');
const detailAvatar = document.querySelector('#detailAvatar');
const detailName = document.querySelector('#detailName');
const detailStarBtn = document.querySelector('#detailStarBtn');
const detailGroupBadge = document.querySelector('#detailGroupBadge');
const detailFavoriteBadge = document.querySelector('#detailFavoriteBadge');
const detailPhone = document.querySelector('#detailPhone');
const detailEmail = document.querySelector('#detailEmail');
const detailGroupText = document.querySelector('#detailGroupText');
const detailAddress = document.querySelector('#detailAddress');
const quickCallLink = document.querySelector('#quickCallLink');
const quickEmailLink = document.querySelector('#quickEmailLink');
const copyPhoneBtn = document.querySelector('#copyPhoneBtn');
const copyBtnLabel = document.querySelector('#copyBtnLabel');
const editContactBtn = document.querySelector('#editContactBtn');
const deleteContactBtn = document.querySelector('#deleteContactBtn');
const deleteConfirmWrapper = document.querySelector('#deleteConfirmWrapper');
const deleteConfirmContainer = document.querySelector('#deleteConfirmContainer');
const cancelDeleteBtn = document.querySelector('#cancelDeleteBtn');
const confirmDeleteBtn = document.querySelector('#confirmDeleteBtn');
const closeDetailMobile = document.querySelector('#closeDetailMobile');

const dialog = document.querySelector('#contactDialog');
const form = document.querySelector('#contactForm');
const formEyebrow = document.querySelector('#formEyebrow');
const formTitle = document.querySelector('#formTitle');
const saveButton = document.querySelector('#saveButton');
const formError = document.querySelector('#formError');
const originalNameInput = document.querySelector('#originalName');
const nameInput = document.querySelector('#name');
const phoneInput = document.querySelector('#phone');
const emailInput = document.querySelector('#email');
const groupSelect = document.querySelector('#group');
const formStarBtn = document.querySelector('#formFavoriteStarBtn');
const formStarSymbol = document.querySelector('#formStarSymbol');
const formStarLabel = document.querySelector('#formStarLabel');
const formFavoriteInput = document.querySelector('#formFavoriteInput');
const addressInput = document.querySelector('#address');
const cancelDialogBtn = document.querySelector('#cancelDialogBtn');
const dialogCancel = document.querySelector('#dialogCancel');
const addButton = document.querySelector('#addButton');
const emptyAddButton = document.querySelector('#emptyAddButton');
const toastEl = document.querySelector('#toast');

// API Request Wrapper
async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

// Utility: Sort contacts alphabetically by name (A–Z, case-insensitive)
function sortContactsAlphabetically(contacts) {
  return [...contacts].sort((a, b) =>
    a.name.trim().localeCompare(b.name.trim(), undefined, { sensitivity: 'base' })
  );
}

// Load Contacts from Server
async function loadContacts() {
  try {
    const query = searchInput.value.trim();
    const data = await request(`/api/contacts?q=${encodeURIComponent(query)}`);
    // Ensure all contacts are sorted alphabetically by name (A-Z)
    state.contacts = sortContactsAlphabetically(data);
    render();

    // Maintain selection if previously selected contact still exists
    if (state.selectedContact) {
      const stillExists = state.contacts.find(
        (c) => c.name.toLowerCase() === state.selectedContact.name.toLowerCase()
      );
      if (stillExists) {
        selectContact(stillExists);
      } else {
        clearSelectedContact();
      }
    }
  } catch (error) {
    showToast(error.message);
  }
}

// Toggle Favorite Status for a Contact
async function toggleFavorite(contactName) {
  try {
    const toggled = await request(`/api/contacts/favorite?name=${encodeURIComponent(contactName)}`, {
      method: 'POST',
    });

    // Update local state
    const local = state.contacts.find((c) => c.name.toLowerCase() === contactName.toLowerCase());
    if (local) {
      local.favorite = toggled.favorite;
    }

    if (state.selectedContact && state.selectedContact.name.toLowerCase() === contactName.toLowerCase()) {
      state.selectedContact.favorite = toggled.favorite;
      updateDetailFavoriteUI(toggled.favorite);
    }

    render();
    const starText = toggled.favorite ? 'Marked as favorite ★' : 'Removed from favorites ☆';
    showToast(`${contactName}: ${starText}`);
  } catch (error) {
    showToast(error.message);
  }
}

// Get Filtered Contacts based on current tab selection
function getFilteredContacts() {
  let list = state.contacts;

  if (state.currentFilter === 'favorites') {
    list = list.filter((c) => c.favorite === true);
  } else if (state.currentFilter !== 'all') {
    list = list.filter((c) => (c.group || 'Other').toLowerCase() === state.currentFilter.toLowerCase());
  }

  return sortContactsAlphabetically(list);
}

// Render Alphabetical Contact List
function render() {
  const visibleContacts = getFilteredContacts();
  const total = visibleContacts.length;

  let countLabel = `${total} ${total === 1 ? 'contact' : 'contacts'}`;
  if (state.currentFilter === 'favorites') {
    countLabel = `${total} favorite ${total === 1 ? 'contact' : 'contacts'}`;
  } else if (state.currentFilter !== 'all') {
    countLabel = `${total} ${state.currentFilter} ${total === 1 ? 'contact' : 'contacts'}`;
  }
  contactCountEl.textContent = countLabel;

  clearFormErrors();

  if (total === 0) {
    listContainer.innerHTML = '';
    alphabetScrubber.innerHTML = '';
    listContainer.hidden = true;
    alphabetScrubber.hidden = true;
    emptyState.hidden = false;

    if (searchInput.value.trim()) {
      document.querySelector('#emptyTitle').textContent = 'No matching contacts';
      document.querySelector('#emptyMessage').textContent = `No contacts found for "${searchInput.value.trim()}".`;
      emptyAddButton.hidden = true;
    } else if (state.currentFilter === 'favorites') {
      document.querySelector('#emptyTitle').textContent = 'No favorites yet';
      document.querySelector('#emptyMessage').textContent = 'Click the star icon (☆) on any contact to mark them as a favorite.';
      emptyAddButton.hidden = false;
    } else if (state.currentFilter !== 'all') {
      document.querySelector('#emptyTitle').textContent = `No ${state.currentFilter} contacts`;
      document.querySelector('#emptyMessage').textContent = `Assign contacts to the "${state.currentFilter}" group to see them here.`;
      emptyAddButton.hidden = false;
    } else {
      document.querySelector('#emptyTitle').textContent = 'No contacts yet';
      document.querySelector('#emptyMessage').textContent = 'Add your first contact to get started.';
      emptyAddButton.hidden = false;
    }
    clearSelectedContact();
    return;
  }

  listContainer.hidden = false;
  alphabetScrubber.hidden = false;
  emptyState.hidden = true;

  // Group visible contacts by first character (A-Z or #)
  const groups = {};
  visibleContacts.forEach((contact) => {
    const firstChar = (contact.name.trim()[0] || '#').toUpperCase();
    const key = /[A-Z]/.test(firstChar) ? firstChar : '#';
    if (!groups[key]) groups[key] = [];
    groups[key].push(contact);
  });

  const sortedKeys = Object.keys(groups).sort((a, b) => {
    if (a === '#') return 1;
    if (b === '#') return -1;
    return a.localeCompare(b);
  });

  // Render Section Headers and Contact Items (sorted A-Z within each group)
  let html = '';
  sortedKeys.forEach((key) => {
    groups[key] = sortContactsAlphabetically(groups[key]);
    html += `
      <div class="alphabet-section" id="section-${key}">
        <div class="alphabet-section-header">${key}</div>
        <div class="alphabet-section-items">
          ${groups[key]
            .map((contact) => {
              const isSelected = state.selectedContact && state.selectedContact.name.toLowerCase() === contact.name.toLowerCase();
              const isFav = contact.favorite === true;
              const groupName = contact.group || 'Other';
              const groupClass = `group-${groupName.toLowerCase()}`;

              return `
                <div class="contact-item ${isSelected ? 'active' : ''}" data-name="${escapeAttribute(contact.name)}" role="button" tabindex="0">
                  <button type="button" class="star-btn contact-row-star ${isFav ? 'is-favorite' : ''}" data-star="${escapeAttribute(contact.name)}" title="${isFav ? 'Remove Favorite' : 'Mark Favorite'}" aria-label="Toggle Favorite">
                    ${isFav ? '★' : '☆'}
                  </button>
                  <div class="avatar">${getInitials(contact.name)}</div>
                  <div class="contact-info">
                    <div class="contact-name-row">
                      <span class="contact-name">${escapeHtml(contact.name)}</span>
                      <span class="badge badge-group ${groupClass}">${escapeHtml(groupName)}</span>
                    </div>
                    <div class="contact-sub-row">
                      <span class="contact-phone-preview">${escapeHtml(contact.phone)}</span>
                    </div>
                  </div>
                  <div class="contact-arrow" aria-hidden="true">›</div>
                </div>
              `;
            })
            .join('')}
        </div>
      </div>
    `;
  });
  listContainer.innerHTML = html;

  // Render Alphabet Scrubber
  renderScrubber(sortedKeys);
}

// Render quick jump sidebar
function renderScrubber(activeKeys) {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'.split('');
  alphabetScrubber.innerHTML = letters
    .map((letter) => {
      const isAvailable = activeKeys.includes(letter);
      return `
        <button type="button" class="scrubber-letter ${isAvailable ? 'active' : ''}" data-letter="${letter}" ${!isAvailable ? 'style="opacity: 0.25;"' : ''}>
          ${letter}
        </button>
      `;
    })
    .join('');
}

// Update Detail View Favorite UI
function updateDetailFavoriteUI(isFav) {
  if (isFav) {
    detailStarBtn.textContent = '★';
    detailStarBtn.classList.add('is-favorite');
    detailFavoriteBadge.hidden = false;
  } else {
    detailStarBtn.textContent = '☆';
    detailStarBtn.classList.remove('is-favorite');
    detailFavoriteBadge.hidden = true;
  }
}

// Contact Selection
function selectContact(contact) {
  state.selectedContact = contact;

  // Update selection UI in list
  document.querySelectorAll('.contact-item').forEach((item) => {
    if (item.dataset.name.toLowerCase() === contact.name.toLowerCase()) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Populate details
  detailPlaceholder.hidden = true;
  detailContent.hidden = false;

  detailAvatar.textContent = getInitials(contact.name);
  detailName.textContent = contact.name;
  detailPhone.textContent = contact.phone;
  detailEmail.textContent = contact.email || '—';
  detailAddress.textContent = contact.address || '(Not provided)';

  const groupName = contact.group || 'Other';
  detailGroupText.textContent = groupName;
  detailGroupBadge.textContent = groupName;
  detailGroupBadge.className = `badge badge-group group-${groupName.toLowerCase()}`;

  updateDetailFavoriteUI(contact.favorite === true);

  quickCallLink.href = `tel:${contact.phone}`;
  if (contact.email) {
    quickEmailLink.href = `mailto:${contact.email}`;
    quickEmailLink.style.opacity = '1';
    quickEmailLink.style.pointerEvents = 'auto';
  } else {
    quickEmailLink.href = '#';
    quickEmailLink.style.opacity = '0.5';
    quickEmailLink.style.pointerEvents = 'none';
  }
  hideDeleteConfirm();

  // Reset copy button
  copyBtnLabel.textContent = 'Copy';

  // Mobile layout open
  detailPane.classList.add('mobile-open');
}

function clearSelectedContact() {
  state.selectedContact = null;
  detailPlaceholder.hidden = false;
  detailContent.hidden = true;
  detailPane.classList.remove('mobile-open');
  document.querySelectorAll('.contact-item').forEach((item) => item.classList.remove('active'));
  hideDeleteConfirm();
}

// Form Star Button State
function setFormStarState(isFav) {
  formFavoriteInput.value = isFav ? 'true' : 'false';
  if (isFav) {
    formStarBtn.classList.add('is-favorite');
    formStarSymbol.textContent = '★';
    formStarLabel.textContent = 'Favorite ★';
  } else {
    formStarBtn.classList.remove('is-favorite');
    formStarSymbol.textContent = '☆';
    formStarLabel.textContent = 'Not Favorite';
  }
}

// Open Form Dialog (for Add or Edit)
function openForm(contact = null) {
  hideDeleteConfirm();
  state.editingContact = contact;
  clearFormErrors();

  if (contact) {
    formEyebrow.textContent = 'EDIT ENTRY';
    formTitle.textContent = 'Edit Contact';
    saveButton.textContent = 'Save Changes';
    originalNameInput.value = contact.name;
    nameInput.value = contact.name;
    phoneInput.value = contact.phone;
    emailInput.value = contact.email;
    addressInput.value = contact.address || '';
    groupSelect.value = contact.group || 'Other';
    setFormStarState(contact.favorite === true);
  } else {
    formEyebrow.textContent = 'NEW ENTRY';
    formTitle.textContent = 'Add Contact';
    saveButton.textContent = 'Save Contact';
    originalNameInput.value = '';
    nameInput.value = '';
    phoneInput.value = '';
    emailInput.value = '';
    addressInput.value = '';
    groupSelect.value = state.currentFilter !== 'all' && state.currentFilter !== 'favorites' ? state.currentFilter : 'Other';
    setFormStarState(state.currentFilter === 'favorites');
  }

  dialog.showModal();
  nameInput.focus();
}

function closeForm() {
  dialog.close();
  clearFormErrors();
}

function showFormError(message, targetInput = null) {
  if (formError) {
    formError.textContent = '';
    formError.hidden = true;
  }
  if (targetInput) {
    targetInput.classList.add('input-error');
    targetInput.focus();
  }
  showToast(message);
}

function clearFormErrors() {
  if (formError) {
    formError.textContent = '';
    formError.hidden = true;
  }
  [nameInput, phoneInput, emailInput, addressInput].forEach((input) => {
    if (input) input.classList.remove('input-error');
  });
}

// Strict Client-Side Validations
function validateContactInputs(formData, originalName = null) {
  const name = formData.name.trim();
  const phone = formData.phone.trim();
  const email = formData.email.trim();

  // 1. Name validation
  if (!name) {
    showFormError('Contact name cannot be empty. Please enter a valid name.', nameInput);
    return false;
  }

  // Duplicate contact detection (case-insensitive)
  const isDuplicate = state.contacts.some((c) => {
    const isSameAsOriginal = originalName && c.name.toLowerCase() === originalName.toLowerCase();
    return !isSameAsOriginal && c.name.toLowerCase() === name.toLowerCase();
  });

  if (isDuplicate) {
    showFormError(`A contact named '${name}' already exists. Duplicate contacts are not allowed. Please enter a different contact name.`, nameInput);
    return false;
  }

  // 2. Phone validation rules:
  // - Exactly 10 digits
  // - Only numbers accepted
  // - Do not allow letters
  // - Do not allow special characters
  // - Do not allow an empty phone number
  if (!phone) {
    showFormError('Phone number cannot be empty. Please enter the phone number again.', phoneInput);
    return false;
  }

  if (/[a-zA-Z]/.test(phone)) {
    showFormError('Phone number cannot contain letters. Only numbers are accepted. Please enter the phone number again.', phoneInput);
    return false;
  }

  if (/[^0-9]/.test(phone)) {
    showFormError('Phone number cannot contain special characters or spaces. Only numbers are accepted. Please enter the phone number again.', phoneInput);
    return false;
  }

  if (phone.length !== 10) {
    showFormError(`Phone number must contain exactly 10 digits (currently ${phone.length} digits). Please enter the phone number again.`, phoneInput);
    return false;
  }

  // 3. Email validation:
  // Email is optional. If provided, it must not start with capital letters, underscore, or special characters,
  // and must follow standard email format constraints.
  if (email) {
    if (/^[A-Z]/.test(email)) {
      showFormError('Email address cannot start with a capital letter. Please enter the email again.', emailInput);
      return false;
    }

    if (/^_/.test(email)) {
      showFormError("Email address cannot start with an underscore ('_'). Please enter the email again.", emailInput);
      return false;
    }

    if (/^[^a-z]/.test(email)) {
      showFormError('Email address must start with a lowercase letter. Please enter the email again.', emailInput);
      return false;
    }

    if (/\s/.test(email)) {
      showFormError('Email address cannot contain spaces. Please enter the email again.', emailInput);
      return false;
    }

    if (/\.\./.test(email)) {
      showFormError('Email address cannot contain consecutive dots. Please enter the email again.', emailInput);
      return false;
    }

    const emailRegex = /^[a-z][a-zA-Z0-9_.+-]*@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRegex.test(email)) {
      showFormError('Invalid email address format (e.g. name@example.com). Please enter the email again.', emailInput);
      return false;
    }
  }

  return true;
}

// Event Listeners

// Filter Tabs Click
filterTabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    filterTabs.forEach((t) => {
      t.classList.remove('active');
      t.setAttribute('aria-selected', 'false');
    });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    state.currentFilter = tab.dataset.filter;
    render();
  });
});

// Form Star Button Toggle
formStarBtn.addEventListener('click', () => {
  const current = formFavoriteInput.value === 'true';
  setFormStarState(!current);
});

// Detail View Star Button Toggle
detailStarBtn.addEventListener('click', () => {
  if (state.selectedContact) {
    toggleFavorite(state.selectedContact.name);
  }
});

// Form Submit
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearFormErrors();

  const formData = {
    name: nameInput.value,
    phone: phoneInput.value,
    email: emailInput.value,
    address: addressInput.value,
    group: groupSelect.value,
    favorite: formFavoriteInput.value === 'true',
  };

  const editingName = originalNameInput.value.trim();

  // Validate according to all rules
  if (!validateContactInputs(formData, editingName)) {
    return;
  }

  try {
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';

    if (editingName) {
      // Update Contact
      const updated = await request(`/api/contacts?name=${encodeURIComponent(editingName)}`, {
        method: 'PUT',
        body: JSON.stringify(formData),
      });
      closeForm();
      showToast('Contact updated successfully');
      await loadContacts();
      selectContact(updated);
    } else {
      // Add Contact
      const created = await request('/api/contacts', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
      closeForm();
      showToast('Contact added successfully');

      // Sort all contacts alphabetically by name (A–Z) before displaying them
      state.contacts.push(created);
      state.contacts = sortContactsAlphabetically(state.contacts);
      render();

      // Also refresh from server to ensure complete sync
      await loadContacts();
      selectContact(created);
      const activeItem = document.querySelector(`.contact-item[data-name="${escapeAttribute(created.name)}"]`);
      if (activeItem) {
        activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  } catch (error) {
    // Show error from backend gracefully without crashing
    showFormError(error.message);
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = editingName ? 'Save Changes' : 'Save Contact';
  }
});

// Click in Contacts List (Select contact or Toggle Star)
listContainer.addEventListener('click', (event) => {
  // Check if star button was clicked
  const starBtn = event.target.closest('.contact-row-star');
  if (starBtn) {
    event.stopPropagation();
    const contactName = starBtn.dataset.star;
    toggleFavorite(contactName);
    return;
  }

  // Otherwise select contact
  const item = event.target.closest('.contact-item');
  if (item) {
    const contactName = item.dataset.name;
    const contact = state.contacts.find((c) => c.name.toLowerCase() === contactName.toLowerCase());
    if (contact) {
      selectContact(contact);
    }
  }
});

// Alphabet Scrubber Navigation Jump
alphabetScrubber.addEventListener('click', (event) => {
  const btn = event.target.closest('.scrubber-letter');
  if (btn) {
    const letter = btn.dataset.letter;
    const targetSection = document.querySelector(`#section-${letter}`);
    if (targetSection) {
      targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
});

// Quick Search
searchInput.addEventListener('input', () => {
  clearSearchBtn.hidden = !searchInput.value;
  loadContacts();
});

clearSearchBtn.addEventListener('click', () => {
  searchInput.value = '';
  clearSearchBtn.hidden = true;
  loadContacts();
  searchInput.focus();
});

// Add Contact Buttons
addButton.addEventListener('click', () => openForm());
emptyAddButton.addEventListener('click', () => openForm());

// Cancel Dialog Buttons
cancelDialogBtn.addEventListener('click', closeForm);
dialogCancel.addEventListener('click', closeForm);

// Edit & Delete on Detail View
editContactBtn.addEventListener('click', () => {
  if (state.selectedContact) {
    openForm(state.selectedContact);
  }
});

// Delete Confirmation Container Handlers
function showDeleteConfirm() {
  if (deleteConfirmContainer) {
    deleteConfirmContainer.hidden = false;
  }
}

function hideDeleteConfirm() {
  if (deleteConfirmContainer) {
    deleteConfirmContainer.hidden = true;
  }
}

deleteContactBtn.addEventListener('click', (event) => {
  event.stopPropagation();
  if (!state.selectedContact) return;
  if (deleteConfirmContainer.hidden) {
    showDeleteConfirm();
  } else {
    hideDeleteConfirm();
  }
});

cancelDeleteBtn.addEventListener('click', (event) => {
  event.stopPropagation();
  hideDeleteConfirm();
});

confirmDeleteBtn.addEventListener('click', async (event) => {
  event.stopPropagation();
  if (!state.selectedContact) return;
  const nameToDelete = state.selectedContact.name;
  hideDeleteConfirm();

  try {
    await request(`/api/contacts?name=${encodeURIComponent(nameToDelete)}`, {
      method: 'DELETE',
    });
    showToast(`Deleted ${nameToDelete}`);
    clearSelectedContact();
    await loadContacts();
  } catch (error) {
    showToast(error.message);
  }
});

// Close delete confirmation container if clicked outside or Escape pressed
document.addEventListener('click', (event) => {
  if (deleteConfirmWrapper && !deleteConfirmWrapper.contains(event.target)) {
    hideDeleteConfirm();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    hideDeleteConfirm();
  }
});

// Close Detail on Mobile
closeDetailMobile.addEventListener('click', () => {
  detailPane.classList.remove('mobile-open');
});

// Copy Phone Action
copyPhoneBtn.addEventListener('click', () => {
  if (!state.selectedContact) return;
  navigator.clipboard.writeText(state.selectedContact.phone).then(() => {
    copyBtnLabel.textContent = 'Copied!';
    setTimeout(() => {
      copyBtnLabel.textContent = 'Copy';
    }, 2000);
  }).catch(() => {
    showToast('Failed to copy number');
  });
});

// Helpers
function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[char]));
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.add('visible');
  setTimeout(() => {
    toastEl.classList.remove('visible');
  }, 2800);
}

// Initial Load
loadContacts();
