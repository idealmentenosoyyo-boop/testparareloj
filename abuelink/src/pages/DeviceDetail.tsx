import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDailyLogs } from '../hooks/useDailyLogs';
import { useDevice } from '../hooks/useDevice';
import { ArrowLeft, Calendar, Activity, MapPin, Footprints, Battery, Radio, Heart } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { DivIcon } from 'leaflet';
import { db } from '../services/firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

// Custom Marker Icon
const createMarkerIcon = (color: string) => new DivIcon({
    className: 'custom-icon',
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${color};"></div>`
});

const DeviceDetail = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    // Use local date instead of UTC to avoid timezone issues
    const [date, setDate] = useState(() => {
        const d = new Date();
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d.toISOString().split('T')[0];
    });

    const { events, loading: eventsLoading } = useDailyLogs(id || '', date);
    const { device, loading: deviceLoading } = useDevice(id || '');

    const [commandStatus, setCommandStatus] = useState<string | null>(null);
    const [showPhantom, setShowPhantom] = useState(false);

    // Filter events (Support both 'event_type' and 'type' for compatibility)
    const positionEvents = events.filter(e =>
        (e.event_type === 'POSITION' || e.type === 'POSITION') && e.lat && e.lng
    );

    // Filter for chart (Historical for selected day)
    const healthEvents = events.filter(e => {
        const type = e.event_type || e.type;
        return type === 'HEALTH' || type === 'bphrt' || type === 'oxygen';
    });

    // Chart Data
    const chartData = healthEvents.map(e => ({
        time: e.timestamp ? new Date(e.timestamp.seconds * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        hr: Number(e.hr || 0),
        spo2: Number(e.spo2 || 0),
        bp_sys: Number(e.bp_sys || 0),
        bp_dia: Number(e.bp_dia || 0)
    })).filter(d => d.hr > 0 || d.spo2 > 0 || d.bp_sys > 0);

    // Map Path
    const pathOptions = { color: '#3b82f6', weight: 4, opacity: 0.7 };
    const positions: [number, number][] = positionEvents.map(e => [e.lat!, e.lng!]);

    const getGradientColor = (index: number, total: number) => {
        const ratio = index / total;
        const minVal = 0;
        const maxVal = 220;
        const val = Math.floor(maxVal * (1 - ratio) + minVal);
        return `rgb(255, ${val}, ${val})`;
    };

    const sendCommand = async (cmd: string) => {
        if (!id) return;
        setCommandStatus('Enviando...');
        try {
            await addDoc(collection(db, `devices/${id}/pending_commands`), {
                command_raw: cmd,
                status: 'PENDING',
                timestamp: serverTimestamp(),
                user_id: 'admin_dashboard',
                description: cmd === 'CR' ? 'Solicitud de Ubicación'
                    : cmd.startsWith('UPLOAD') ? `Cambio de Intervalo (${cmd.split(',')[1]}s)`
                        : cmd.startsWith('LSSET') ? `Sensibilidad Caída (Lv ${cmd.split(',')[1].split('+')[0]})`
                            : cmd.startsWith('hrtstart') ? 'Medición de Salud'
                                : cmd === 'FIND' ? 'Buscar Dispositivo'
                                    : 'Comando Remoto'
            });
            setCommandStatus('Comando Enviado 🚀');
            setTimeout(() => setCommandStatus(null), 3000);
        } catch (e) {
            console.error(e);
            setCommandStatus('Error al enviar ❌');
        }
    };

    if (eventsLoading || deviceLoading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="text-blue-500 animate-pulse font-mono tracking-widest">LOADING_DATA...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-slate-200 font-sans pb-20 lg:pb-0">
            {/* Header */}
            <header className="border-b border-white/5 bg-black/50 backdrop-blur-md px-4 py-4 lg:px-6 lg:h-16 sticky top-0 z-50 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex items-center gap-4 w-full lg:w-auto justify-between lg:justify-start">
                    <div className="flex items-center gap-4">
                        <button onClick={() => navigate('/')} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <h1 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                                <span className="hidden sm:inline">Dispositivo:</span>
                                <span className="text-blue-500 font-mono">{id}</span>
                                {device?.online ? (
                                    <span className="flex items-center gap-1 text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full border border-green-500/30">
                                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                                        ONLINE
                                    </span>
                                ) : (
                                    <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full border border-red-500/30">OFFLINE</span>
                                )}
                            </h1>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3 w-full lg:w-auto">
                    {commandStatus && (
                        <span className="text-sm font-bold text-center text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full animate-pulse mb-2 lg:mb-0">{commandStatus}</span>
                    )}

                    <div className="grid grid-cols-2 lg:flex items-center gap-2">
                        {/* Status Bar for Mobile */}
                        <div className="col-span-2 flex items-center justify-between bg-white/5 p-2 rounded-lg lg:hidden mb-2">
                            <div className="flex items-center gap-2">
                                <Battery className={`w-4 h-4 ${device?.last_battery && device.last_battery < 20 ? 'text-red-500' : 'text-green-500'}`} />
                                <span className="text-xs font-mono">{device?.last_battery || 0}%</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Heart className="w-4 h-4 text-red-500" />
                                <span className="text-xs font-mono">{device?.last_hr || '--'} bpm</span>
                            </div>
                        </div>

                        <div className="flex items-center bg-white/5 border border-white/10 rounded-lg p-0.5 col-span-2 lg:col-span-1">
                            <select
                                onChange={(e) => {
                                    if (e.target.value) sendCommand(`UPLOAD,${e.target.value}`);
                                }}
                                className="bg-transparent text-white text-sm px-2 py-1.5 focus:outline-none [&>option]:bg-black w-full"
                                defaultValue=""
                            >
                                <option value="" disabled>Intervalo GPS ⏱️</option>
                                <option value="60">1 Min</option>
                                <option value="300">5 Min</option>
                                <option value="600">10 Min</option>
                                <option value="3600">60 Min</option>
                            </select>
                        </div>

                        <div className="flex items-center bg-white/5 border border-white/10 rounded-lg p-0.5 col-span-2 lg:col-span-1">
                            <select
                                onChange={(e) => {
                                    if (e.target.value) sendCommand(`LSSET,${e.target.value}+8`);
                                }}
                                className="bg-transparent text-white text-sm px-2 py-1.5 focus:outline-none [&>option]:bg-black w-full"
                                defaultValue=""
                            >
                                <option value="" disabled>Sensibilidad Caída ⚠️</option>
                                <option value="1">Lv 1 (Máx - Test)</option>
                                <option value="2">Lv 2</option>
                                <option value="3">Lv 3</option>
                                <option value="4">Lv 4</option>
                                <option value="5">Lv 5 (Medio)</option>
                                <option value="6">Lv 6</option>
                                <option value="7">Lv 7</option>
                                <option value="8">Lv 8 (Mín)</option>
                            </select>
                        </div>

                        <button
                            onClick={() => setShowPhantom(!showPhantom)}
                            className={`col-span-2 lg:col-span-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white px-3 py-2 rounded-lg text-xs lg:text-sm font-medium transition-colors flex items-center justify-center gap-2 ${showPhantom ? 'text-red-400 border-red-500/30 bg-red-500/10' : ''}`}
                        >
                            <Footprints className={`w-4 h-4 ${showPhantom ? 'text-red-400' : 'text-slate-400'}`} /> <span className="hidden sm:inline">Ruta Fantasma</span><span className="sm:hidden">Ruta</span>
                        </button>

                        <button
                            onClick={() => sendCommand('CR')}
                            className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-3 py-2 rounded-lg text-xs lg:text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        >
                            <MapPin className="w-4 h-4 text-blue-400" /> <span className="hidden sm:inline">Ubicación</span><span className="sm:hidden">GPS</span>
                        </button>
                        <button
                            onClick={() => sendCommand('FIND')}
                            className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-3 py-2 rounded-lg text-xs lg:text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        >
                            <Radio className="w-4 h-4 text-yellow-400" /> <span className="hidden sm:inline">Buscar</span>
                        </button>
                        <button
                            onClick={() => sendCommand('hrtstart,1')}
                            className="col-span-2 lg:col-span-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white px-3 py-2 rounded-lg text-xs lg:text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        >
                            <Activity className="w-4 h-4 text-red-400" /> <span className="hidden sm:inline">Medir Salud</span><span className="sm:hidden">Salud</span>
                        </button>
                    </div>
                </div>
            </header>

            <main className="p-4 lg:p-10 max-w-[1600px] mx-auto space-y-6 lg:space-y-8">

                {/* Status Cards (Desktop) */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-[#111] border border-white/5 p-4 rounded-2xl flex flex-col gap-1">
                        <span className="text-xs text-slate-500 uppercase font-bold tracking-wider flex items-center gap-2">
                            <Battery className="w-3 h-3" /> Batería
                        </span>
                        <span className="text-2xl font-mono text-white">{device?.last_battery || 0}<span className="text-sm text-slate-500">%</span></span>
                    </div>
                    <div className="bg-[#111] border border-white/5 p-4 rounded-2xl flex flex-col gap-1">
                        <span className="text-xs text-slate-500 uppercase font-bold tracking-wider flex items-center gap-2">
                            <Heart className="w-3 h-3 text-red-500" /> Ritmo (Actual)
                        </span>
                        <span className="text-2xl font-mono text-white">{device?.last_hr || '--'} <span className="text-sm text-slate-500">bpm</span></span>
                    </div>
                    <div className="bg-[#111] border border-white/5 p-4 rounded-2xl flex flex-col gap-1">
                        <span className="text-xs text-slate-500 uppercase font-bold tracking-wider flex items-center gap-2">
                            <Activity className="w-3 h-3 text-blue-500" /> Presión (Actual)
                        </span>
                        <span className="text-2xl font-mono text-white">{device?.last_bp || '--'} <span className="text-sm text-slate-500">mmHg</span></span>
                    </div>
                    <div className="bg-[#111] border border-white/5 p-4 rounded-2xl flex flex-col gap-1 items-end justify-center">
                        <div className="relative w-full lg:w-auto">
                            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="date"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                className="w-full bg-[#000] border border-white/10 text-white pl-10 pr-4 py-2 rounded-xl focus:outline-none focus:border-blue-500 transition-colors text-sm"
                            />
                        </div>
                    </div>
                </div>

                {/* Map Section */}
                <div className="bg-[#111] border border-white/5 rounded-3xl overflow-hidden h-[350px] lg:h-[500px] relative">
                    {positionEvents.length === 0 ? (
                        <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                            <p>No hay datos de ubicación para este día.</p>
                        </div>
                    ) : (
                        <MapContainer
                            center={positions[positions.length - 1]}
                            zoom={15}
                            style={{ height: '100%', width: '100%' }}
                            className="z-0"
                        >
                            <TileLayer
                                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                            />

                            {!showPhantom ? (
                                <Polyline pathOptions={pathOptions} positions={positions} />
                            ) : (
                                positions.map((_, i) => {
                                    if (i === positions.length - 1) return null;
                                    return (
                                        <Polyline
                                            key={i}
                                            positions={[positions[i], positions[i + 1]]}
                                            pathOptions={{
                                                color: getGradientColor(i, positions.length),
                                                weight: 4,
                                                opacity: 0.9
                                            }}
                                        />
                                    );
                                })
                            )}

                            {/* Start Marker */}
                            {positions.length > 0 && (
                                <Marker position={positions[0]} icon={createMarkerIcon('#10b981')}>
                                    <Popup>Inicio del día</Popup>
                                </Marker>
                            )}

                            {/* End Marker (Latest) */}
                            {positions.length > 0 && (
                                <Marker position={positions[positions.length - 1]} icon={createMarkerIcon('#ef4444')}>
                                    <Popup>Última posición reportada</Popup>
                                </Marker>
                            )}
                        </MapContainer>
                    )}

                    <div className="absolute top-4 left-4 bg-black/80 backdrop-blur border border-white/10 p-3 lg:p-4 rounded-xl z-[400]">
                        <h3 className="text-[10px] lg:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 lg:mb-2">Ruta del Día</h3>
                        <div className="text-xl lg:text-2xl font-bold text-white font-mono">{positions.length} <span className="text-xs lg:text-sm text-slate-500">puntos</span></div>
                    </div>
                </div>

                {/* Health Chart */}
                <div className="bg-[#111] border border-white/5 rounded-3xl p-4 lg:p-8 h-[350px] lg:h-[400px] relative">
                    <h3 className="text-lg lg:text-xl font-bold text-white mb-4 lg:mb-6 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-red-500" /> Signos Vitales (Historial del Día)
                    </h3>

                    {chartData.length === 0 ? (
                        <div className="absolute inset-0 flex items-center justify-center text-slate-500 bg-black/50 backdrop-blur-sm rounded-3xl">
                            <div className="text-center">
                                <Activity className="w-12 h-12 mx-auto mb-2 opacity-20" />
                                <p>No hay mediciones de salud para este día.</p>
                                <button onClick={() => setDate('2026-01-23')} className="mt-4 text-xs text-blue-500 hover:text-blue-400 underline">
                                    Ver datos de ejemplo (23 Ene)
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full w-full pb-8" key={date}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorHr" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorSpo2" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis
                                        dataKey="time"
                                        stroke="#666"
                                        tick={{ fill: '#666' }}
                                        tickLine={false}
                                        axisLine={false}
                                        padding={{ left: 20, right: 20 }}
                                    />
                                    <YAxis stroke="#666" tick={{ fill: '#666' }} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px' }}
                                    />
                                    <Legend
                                        verticalAlign="top"
                                        height={60}
                                        iconType="circle"
                                        wrapperStyle={{ paddingBottom: '20px', fontSize: '12px' }}
                                    />
                                    <Area type="monotone" dataKey="hr" name="Ritmo Cardíaco" stroke="#ef4444" fillOpacity={1} fill="url(#colorHr)" strokeWidth={2} connectNulls={true} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                    <Area type="monotone" dataKey="spo2" name="Oxígeno" stroke="#3b82f6" fillOpacity={1} fill="url(#colorSpo2)" strokeWidth={2} connectNulls={true} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                    <Area type="monotone" dataKey="bp_sys" name="P. A. Sistólica" stroke="#eab308" fill="none" strokeWidth={2} strokeDasharray="5 5" connectNulls={true} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                    <Area type="monotone" dataKey="bp_dia" name="P. A. Diastólica" stroke="#a855f7" fill="none" strokeWidth={2} strokeDasharray="5 5" connectNulls={true} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>

            </main>
        </div>
    );
};

export default DeviceDetail;
