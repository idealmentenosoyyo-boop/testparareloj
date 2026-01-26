import { useState, useEffect } from 'react';
import { collection, onSnapshot, query, orderBy } from 'firebase/firestore';
import { db } from '../services/firebase';
import type { DeviceData } from '../types';

export const useDevices = () => {
    const [devices, setDevices] = useState<DeviceData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Escuchar cambios en la colección 'devices'
        // Se puede ordenar por 'updated_at' o 'last_seen'
        const q = query(collection(db, 'devices'), orderBy('last_seen', 'desc'));

        const unsubscribe = onSnapshot(q,
            (snapshot) => {
                const docs = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data()
                })) as DeviceData[];
                setDevices(docs);
                setLoading(false);
            },
            (err) => {
                console.error("Error fetching devices:", err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, []);

    return { devices, loading, error };
};
