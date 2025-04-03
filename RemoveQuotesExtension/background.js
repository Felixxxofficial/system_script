chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['removeQuotesEnabled', 'copyAndOpenUrlEnabled'], (result) => {
    if (result.removeQuotesEnabled === undefined) {
      chrome.storage.local.set({ removeQuotesEnabled: false });
    }
    if (result.copyAndOpenUrlEnabled === undefined) {
      chrome.storage.local.set({ copyAndOpenUrlEnabled: false });
    }
  });
});