const express = require('express');
const admin = require('firebase-admin');
const cors = require('cors');
const bodyParser = require('body-parser');

// --- FIREBASE CONFIGURATION ---
// In Railway, you can set the environment variable FIREBASE_SERVICE_ACCOUNT
// with the content of your service account JSON file.
// Or locally, place 'service-account.json' in this folder.

let serviceAccount;
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
  } else {
    // Usando el archivo específico proporcionado por el usuario
    serviceAccount = require('./abuelink-cl-firebase-adminsdk-fbsvc-21d8f71394.json');
  }
} catch (error) {
  console.error("Error loading Firebase credentials. Make sure FIREBASE_SERVICE_ACCOUNT env var is set or service-account.json exists.");
  console.error(error.message);
  // We don't exit process so the server can at least start and respond with error on endpoints
}

if (serviceAccount) {
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    // databaseURL: "https://abuelink-cl.firebaseio.com" // Optional if using Firestore
  });
  console.log("Firebase Admin Initialized");
}

// Only initialize DB if Admin is initialized
const db = admin.apps.length > 0 ? admin.firestore() : null;
const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());

// --- ROUTES ---

app.get('/', (req, res) => {
  res.send('Abuelink Backend Running');
});

// Endpoint to receive data from Arduino
app.post('/api/data', async (req, res) => {
  try {
    if (!db) {
      console.warn("Data received but DB not connected (Missing Credentials)");
      return res.status(503).json({ error: "Service Unavailable: Firebase credentials missing on server." });
    }

    const data = req.body;
    console.log("Received data:", JSON.stringify(data));

    if (!data || !data.device_id) {
      return res.status(400).json({ error: "Invalid data format. device_id required." });
    }

    // Add server timestamp
    const payload = {
      ...data,
      server_timestamp: admin.firestore.FieldValue.serverTimestamp()
    };

    // Save to Firestore
    // Collection: 'telemetry' -> Document ID: (Auto)
    const docRef = await db.collection('telemetry').add(payload);

    // Optionally update the latest status for the device in a separate collection
    await db.collection('devices').doc(data.device_id).set({
      last_seen: admin.firestore.FieldValue.serverTimestamp(),
      latest_data: payload
    }, { merge: true });

    res.status(200).json({ message: "Data received and saved", id: docRef.id });

  } catch (error) {
    console.error("Error processing data:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
