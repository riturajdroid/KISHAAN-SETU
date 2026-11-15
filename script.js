const isHostedOnBackend = window.location.protocol.startsWith('http') && window.location.port === '8000';
const API_URL = isHostedOnBackend ? `${window.location.origin}/api/contact` : 'http://localhost:8000/api/contact';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('contactForm');
  const submitBtn = document.getElementById('submitBtn');
  const btnSpinner = document.getElementById('btnSpinner');
  const btnText = submitBtn.querySelector('.btn-text');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlerts();
    clearFieldErrors();

    const nameVal = document.getElementById('name').value.trim();
    const emailVal = document.getElementById('email').value.trim();
    const phoneVal = document.getElementById('phone').value.trim();
    const subjectVal = document.getElementById('subject').value.trim();
    const messageVal = document.getElementById('message').value.trim();

    let hasError = false;

    if (!nameVal || nameVal.length < 2) {
      setFieldError('name', 'Please enter your full name (at least 2 characters).');
      hasError = true;
    }

    if (!emailVal || !isValidEmail(emailVal)) {
      setFieldError('email', 'Please provide a valid email address.');
      hasError = true;
    }

    if (!subjectVal || subjectVal.length < 3) {
      setFieldError('subject', 'Please enter a subject (at least 3 characters).');
      hasError = true;
    }

    if (!messageVal || messageVal.length < 5) {
      setFieldError('message', 'Message must be at least 5 characters long.');
      hasError = true;
    }

    if (hasError) return;

    submitBtn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    btnText.textContent = 'Submitting...';

    const payload = {
      name: nameVal,
      email: emailVal,
      phone: phoneVal || null,
      subject: subjectVal,
      message: messageVal
    };

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned error (${response.status})`);
      }

      const result = await response.json();

      showSuccess(
        'Response Received!',
        result.message || 'Your response has been stored in the database.'
      );

      form.reset();

    } catch (err) {
      showError(
        'Submission Failed',
        `${err.message}. Please ensure the FastAPI server (python main.py) and XAMPP are running.`
      );
    } finally {
      submitBtn.disabled = false;
      btnSpinner.style.display = 'none';
      btnText.textContent = 'Submit Response';
    }
  });
});

function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function setFieldError(fieldId, errorMsg) {
  const input = document.getElementById(fieldId);
  const errorSpan = document.getElementById(`${fieldId}Error`);
  if (input) input.classList.add('invalid');
  if (errorSpan) errorSpan.textContent = errorMsg;
}

function clearFieldErrors() {
  ['name', 'email', 'phone', 'subject', 'message'].forEach(id => {
    const input = document.getElementById(id);
    const errorSpan = document.getElementById(`${id}Error`);
    if (input) input.classList.remove('invalid');
    if (errorSpan) errorSpan.textContent = '';
  });
}

function showSuccess(title, message) {
  const alertEl = document.getElementById('alertSuccess');
  document.getElementById('successTitle').textContent = title;
  document.getElementById('successMessage').textContent = message;
  alertEl.style.display = 'flex';
}

function showError(title, message) {
  const alertEl = document.getElementById('alertError');
  document.getElementById('errorTitle').textContent = title;
  document.getElementById('errorMessage').textContent = message;
  alertEl.style.display = 'flex';
}

function hideAlerts() {
  const s = document.getElementById('alertSuccess');
  const e = document.getElementById('alertError');
  if (s) s.style.display = 'none';
  if (e) e.style.display = 'none';
}
