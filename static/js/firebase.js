// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.1.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.1.0/firebase-analytics.js";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyA8qkhDDdL5rip21UTg9iObtgrPkE25j7o",
  authDomain: "foodhub-de353.firebaseapp.com",
  projectId: "foodhub-de353",
  storageBucket: "foodhub-de353.firebasestorage.app",
  messagingSenderId: "332108019705",
  appId: "1:332108019705:web:73b0edae4d4ec7e982af28",
  measurementId: "G-2LVHYFXHE8"
};

const firebaseApp = initializeApp(firebaseConfig);

const messaging = getMessaging(firebaseApp);
const analytics = getAnalytics(app);

export { messaging, getToken, onMessage };
  