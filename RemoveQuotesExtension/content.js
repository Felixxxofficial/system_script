// Function to remove quotes and open URLs when copying
document.addEventListener('copy', (event) => {
    if (window.location.href.includes('noco.bvmodel.cloud')) {
      const selection = window.getSelection().toString();
      if (selection) {
        // Remove leading and trailing double quotes
        let cleanedText = selection;
        if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
          cleanedText = cleanedText.slice(1, -1);
        }
        cleanedText = cleanedText.replace(/""/g, '"');
  
        // Regular expression to match URLs
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const match = cleanedText.match(urlRegex);
        if (match) {
          // Open the first URL in a new tab
          window.open(match[0], '_blank');
        }
  
        // Set the cleaned text in the clipboard
        event.clipboardData.setData('text/plain', cleanedText);
        event.preventDefault();
      }
    }
  });