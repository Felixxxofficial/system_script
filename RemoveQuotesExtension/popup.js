document.addEventListener('DOMContentLoaded', () => {
  const removeQuotesCheckbox = document.getElementById('removeQuotes');
  const copyAndOpenUrlCheckbox = document.getElementById('copyAndOpenUrl');

  // Load saved settings
  chrome.storage.local.get(['removeQuotesEnabled', 'copyAndOpenUrlEnabled'], (result) => {
    removeQuotesCheckbox.checked = result.removeQuotesEnabled !== undefined ? result.removeQuotesEnabled : false;
    copyAndOpenUrlCheckbox.checked = result.copyAndOpenUrlEnabled !== undefined ? result.copyAndOpenUrlEnabled : false;
  });

  // Save settings when checkboxes change
  removeQuotesCheckbox.addEventListener('change', () => {
    chrome.storage.local.set({ removeQuotesEnabled: removeQuotesCheckbox.checked });
  });

  copyAndOpenUrlCheckbox.addEventListener('change', () => {
    chrome.storage.local.set({ copyAndOpenUrlEnabled: copyAndOpenUrlCheckbox.checked });
  });
});