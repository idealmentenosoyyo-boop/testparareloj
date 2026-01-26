import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
    apiKey: "AIzaSyCeSqOfqHkMhAfhP4m7f-5OiUE2s_oRPww",
    authDomain: "abuelink-cl.firebaseapp.com",
    projectId: "abuelink-cl",
    storageBucket: "abuelink-cl.firebasestorage.app",
    messagingSenderId: "848244683032",
    appId: "1:848244683032:web:77030e1f2600455082ae6d",
    measurementId: "G-Z70TBH5JSB"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
export const analytics = typeof window !== "undefined" ? getAnalytics(app) : null;

export default app;
