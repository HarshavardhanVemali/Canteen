import { requestNotificationPermission, setupOnMessageListener } from "./notifications.js";

document.addEventListener("DOMContentLoaded", () => {
  requestNotificationPermission().then((token) => {
    console.log("Token registered:", token);
  });

  setupOnMessageListener();
});
