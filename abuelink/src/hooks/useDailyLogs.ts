import { useState, useEffect } from 'react';
import { collection, onSnapshot, query, orderBy } from 'firebase/firestore';
import { db } from '../services/firebase';
import type { DeviceEvent } from '../types';

export const useDailyLogs = (deviceId: string, dateStr: string) => {
    const [events, setEvents] = useState<DeviceEvent[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!deviceId || !dateStr) {
            setEvents([]);
            return;
        }

        const path = `devices/${deviceId}/days/${dateStr}/events`;
        const q = query(collection(db, path), orderBy('timestamp', 'asc'));

        const unsubscribe = onSnapshot(q, (snapshot) => {
            const docs = snapshot.docs.map(doc => ({
                id: doc.id,
                ...doc.data()
            })) as DeviceEvent[];
            setEvents(docs);
            setLoading(false);
        });

        return () => unsubscribe();
    }, [deviceId, dateStr]);

    return { events, loading };
};
