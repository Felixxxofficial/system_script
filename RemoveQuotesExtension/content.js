// Listen for the copy event
document.addEventListener('copy', (event) => {
    // Only run on noco.bvmodel.cloud
    if (window.location.href.includes('noco.bvmodel.cloud')) {
      // Get the selected text
      const selection = window.getSelection().toString();
      if (selection) {
        // Remove leading and trailing double quotes
        let cleanedText = selection;
        if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
          cleanedText = cleanedText.slice(1, -1);
        }
        // Replace any doubled double quotes (CSV escaping) with single quotes
        cleanedText = cleanedText.replace(/""/g, '"');
        // Write the cleaned text to the clipboard
        event.clipboardData.setData('text/plain', cleanedText);
        event.preventDefault();
      }
    }
  });