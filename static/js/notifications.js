import { messaging, getToken, onMessage } from "./firebase.js";

export function requestNotificationPermission() {
  return Notification.requestPermission()
    .then((permission) => {
      if (permission === "granted") {
        return getToken(messaging, { vapidKey: "YOUR_VAPID_KEY" });
      } else {
        throw new Error("Notification permission denied");
      }
    })
    .then((token) => {
      console.log("FCM Token:", token);
      // Send the token to your backend server
      return token;
    })
    .catch((error) => {
      console.error("Error getting notification token:", error);
    });
}

export function setupOnMessageListener() {
  onMessage(messaging, (payload) => {
    console.log("Message received:", payload);
    // Handle the notification payload
    alert(`Notification: ${payload.notification.title}`);
  });
}
