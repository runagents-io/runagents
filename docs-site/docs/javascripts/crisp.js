/* Crisp live chat — lead capture
   Replace CRISP_WEBSITE_ID with your ID from crisp.chat/en/settings/website/
   Free tier: up to 2 seats, unlimited chats */
(function () {
  var CRISP_WEBSITE_ID = 'YOUR_CRISP_WEBSITE_ID'; // replace with real ID
  if (!CRISP_WEBSITE_ID || CRISP_WEBSITE_ID === 'YOUR_CRISP_WEBSITE_ID') return;
  window.$crisp = [];
  window.CRISP_WEBSITE_ID = CRISP_WEBSITE_ID;
  var s = document.createElement('script');
  s.src = 'https://client.crisp.chat/l.js';
  s.async = true;
  document.head.appendChild(s);
  // Pre-fill page context
  document.addEventListener('DOMContentLoaded', function () {
    if (window.$crisp) {
      window.$crisp.push(['set', 'session:data', [[['page', document.title], ['url', location.href]]]]);
    }
  });
})();
