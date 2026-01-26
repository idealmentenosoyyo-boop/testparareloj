import React from 'react';
import type { DeviceData } from '../types';
import { Battery, Activity, MapPin, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface DeviceCardProps {
    device: DeviceData;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device }) => {
    const navigate = useNavigate();

    const isLowBattery = (device.last_battery || 0) < 20;
    const isOnline = device.online;
    // You might want to calculate specific logic for "online" based on last_seen vs now if online bool is not enough

    return (
        <div
            onClick={() => navigate(`/device/${device.id}`)}
            className="group bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 cursor-pointer hover:bg-white/10 hover:border-blue-500/30 transition-all duration-300"
        >
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-slate-500'}`}></div>
                    <h3 className="text-lg font-bold text-white tracking-wide">{device.id}</h3>
                </div>
                <div className="flex items-center gap-2 bg-black/20 px-2 py-1 rounded-lg">
                    <Battery className={`w-4 h-4 ${isLowBattery ? 'text-red-500' : 'text-emerald-500'}`} />
                    <span className="text-sm font-mono text-slate-300">{device.last_battery || 0}%</span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <Activity className="w-3 h-3" />
                        <span className="text-[10px] uppercase font-bold tracking-wider">Salud</span>
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-xl font-bold text-white">{device.last_hr || '--'}</span>
                        <span className="text-xs text-slate-500">BPM</span>
                    </div>
                </div>

                <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <MapPin className="w-3 h-3" />
                        <span className="text-[10px] uppercase font-bold tracking-wider">GPS</span>
                    </div>
                    <div className="text-xs text-slate-300 truncate">
                        {device.last_lat ? `${device.last_lat.toFixed(4)}, ${device.last_lng?.toFixed(4)}` : 'Sin señal'}
                    </div>
                </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 border-t border-white/5 pt-4">
                <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>
                        {device.last_seen
                            ? new Date(device.last_seen.seconds * 1000).toLocaleString()
                            : 'N/A'}
                    </span>
                </div>
                <span className="group-hover:translate-x-1 transition-transform text-blue-400 font-medium">Ver detalles →</span>
            </div>
        </div>
    );
};
