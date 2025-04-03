// Global variables to store settings
let removeQuotesEnabled = false;
let copyAndOpenUrlEnabled = false;

// Load initial settings
chrome.storage.local.get(['removeQuotesEnabled', 'copyAndOpenUrlEnabled'], (result) => {
  removeQuotesEnabled = result.removeQuotesEnabled !== undefined ? result.removeQuotesEnabled : false;
  copyAndOpenUrlEnabled = result.copyAndOpenUrlEnabled !== undefined ? result.copyAndOpenUrlEnabled : false;
});

// Listen for changes to settings
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local') {
    if (changes.removeQuotesEnabled) {
      removeQuotesEnabled = changes.removeQuotesEnabled.newValue;
    }
    if (changes.copyAndOpenUrlEnabled) {
      copyAndOpenUrlEnabled = changes.copyAndOpenUrlEnabled.newValue;
    }
  }
});

// Function to remove quotes and open URLs when copying
document.addEventListener('copy', (event) => {
  if (window.location.href.includes('noco.bvmodel.cloud')) {
    // If both features are disabled, do nothing (default copy behavior)
    if (!removeQuotesEnabled && !copyAndOpenUrlEnabled) {
      return;
    }

    const selection = window.getSelection().toString();
    if (selection) {
      let cleanedText = selection;

      if (removeQuotesEnabled) {
        if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
          cleanedText = cleanedText.slice(1, -1);
        }
        cleanedText = cleanedText.replace(/""/g, '"');
      }

      if (copyAndOpenUrlEnabled) {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const match = cleanedText.match(urlRegex);
        if (match) {
          window.open(match[0], '_blank');
        }
      }

      event.clipboardData.setData('text/plain', cleanedText);
      event.preventDefault();
    }
  }
});