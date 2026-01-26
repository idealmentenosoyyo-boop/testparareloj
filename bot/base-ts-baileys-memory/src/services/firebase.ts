import { initializeApp } from "firebase/app";
import { getFirestore, collectionGroup, query, where, onSnapshot, Timestamp } from "firebase/firestore";

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
export const db = getFirestore(app);

export const monitorFalls = (callback: (data: any) => Promise<void>) => {
    console.log("Starting fall monitoring...");

    // We only want to listen for falls that happen AFTER the bot starts
    // to avoid flooding with old alerts.
    const startTime = new Date();

    // Query only for falls to avoid composite index requirement
    const q = query(
        collectionGroup(db, 'events'),
        where('alarm_fall', '==', true)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
        snapshot.docChanges().forEach((change) => {
            if (change.type === "added") {
                const data = change.doc.data();
                const eventDate = data.timestamp?.toDate ? data.timestamp.toDate() : new Date(0); // Default to epoch if no timestamp

                // Filter out old events (happened before bot started)
                if (eventDate > startTime) {
                    console.log("🚨 Fall detected:", change.doc.id, data);
                    callback(data);
                }
            }
        });
    }, (error) => {
        console.error("Error monitoring falls:", error);
    });

    return unsubscribe;
};
