// Global variables to store settings
let removeQuotesEnabled = false;
let copyAndOpenUrlEnabled = false;

// Load initial settings
chrome.storage.local.get(['removeQuotesEnabled', 'copyAndOpenUrlEnabled'], (result) => {
  removeQuotesEnabled = result.removeQuotesEnabled !== undefined ? result.removeQuotesEnabled : false;
  copyAndOpenUrlEnabled = result.copyAndOpenUrlEnabled !== undefined ? result.copyAndOpenUrlEnabled : false;
  console.log('Initial settings loaded:', { removeQuotesEnabled, copyAndOpenUrlEnabled });
});

// Listen for changes to settings
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local') {
    if (changes.removeQuotesEnabled) {
      removeQuotesEnabled = changes.removeQuotesEnabled.newValue;
      console.log('removeQuotesEnabled updated to:', removeQuotesEnabled);
    }
    if (changes.copyAndOpenUrlEnabled) {
      copyAndOpenUrlEnabled = changes.copyAndOpenUrlEnabled.newValue;
      console.log('copyAndOpenUrlEnabled updated to:', copyAndOpenUrlEnabled);
    }
  }
});

// Function to remove quotes and open URLs when copying
document.addEventListener('copy', (event) => {
  if (window.location.href.includes('noco.bvmodel.cloud')) {
    console.log('Copy event triggered');

    if (!removeQuotesEnabled && !copyAndOpenUrlEnabled) {
      console.log('Both features disabled, skipping');
      return;
    }

    const selection = window.getSelection().toString();
    console.log('Selection:', selection);

    if (selection) {
      console.log('Raw selection (stringified):', JSON.stringify(selection));
      console.log('Raw selection (plain):', selection);

      // Split the selected text into rows based on newlines
      const rows = selection.split('\n');
      console.log('Split rows:', rows);

      const cleanedRows = [];

      // Process each row
      for (let row of rows) {
        let cleanedText = row.trim();

        if (removeQuotesEnabled && cleanedText) {
          if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
            cleanedText = cleanedText.slice(1, -1);
          }
          cleanedText = cleanedText.replace(/""/g, '"');
        }

        if (copyAndOpenUrlEnabled && cleanedText) {
          const urlRegex = /(https?:\/\/[^\s]+)/g;
          const match = cleanedText.match(urlRegex);
          if (match) {
            window.open(match[0], '_blank');
          }
        }

        cleanedRows.push(cleanedText);
      }

      // Rejoin the rows with newlines
      const finalText = cleanedRows.join('\n');
      console.log('Final text:', finalText);

      event.clipboardData.setData('text/plain', finalText);
      event.preventDefault();
    } else {
      console.log('No selection found');
    }
  } else {
    console.log('Not on noco.bvmodel.cloud');
  }
});