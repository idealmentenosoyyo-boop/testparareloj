import { useState, useEffect } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';
import { db } from '../services/firebase';
import type { DeviceData } from '../types';

export const useDevice = (deviceId: string) => {
    const [device, setDevice] = useState<DeviceData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!deviceId) return;

        const docRef = doc(db, 'devices', deviceId);

        const unsubscribe = onSnapshot(docRef,
            (docSnap) => {
                if (docSnap.exists()) {
                    setDevice({
                        id: docSnap.id,
                        ...docSnap.data()
                    } as DeviceData);
                } else {
                    setDevice(null);
                    setError("Device not found");
                }
                setLoading(false);
            },
            (err) => {
                console.error("Error fetching device:", err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, [deviceId]);

    return { device, loading, error };
};
