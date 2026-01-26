import { useDevices } from "../hooks/useDevices";
import { useAuth } from "../contexts/AuthContext";
import { DeviceCard } from "../components/DeviceCard";
import { Activity, LogOut, Plus } from "lucide-react";
import { signOut } from "firebase/auth";
import { auth } from "../services/firebase";

const Dashboard = () => {
  const { user } = useAuth();
  const { devices, loading, error } = useDevices();

  const handleSignOut = () => signOut(auth);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-t-2 border-l-2 border-blue-500 rounded-full animate-spin"></div>
        <p className="text-slate-500 font-mono text-sm animate-pulse">SEARCHING_SIGNALS...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-slate-200 font-sans selection:bg-blue-500/30">

      {/* Header Premium */}
      <header className="h-16 border-b border-white/5 bg-black/50 backdrop-blur-md flex items-center justify-between px-6 lg:px-12 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">ABUELINK <span className="text-blue-500 font-mono text-xs ml-1">MASTER</span></span>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden md:flex flex-col items-end">
            <span className="text-sm font-medium text-white">{user?.displayName}</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Admin Console</span>
          </div>
          <button
            onClick={handleSignOut}
            className="p-2 hover:bg-white/5 rounded-full transition-colors text-slate-400 hover:text-white"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto p-6 lg:p-12">

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Dispositivos Activos</h1>
            <p className="text-slate-400">Monitoreo en tiempo real de {devices.length} unidades.</p>
          </div>

          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl transition-all font-medium shadow-lg shadow-blue-900/20">
            <Plus className="w-4 h-4" /> Agregar Dispositivo
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-8 text-red-400">
            Error cargando dispositivos: {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {devices.map(device => (
            <DeviceCard key={device.id} device={device} />
          ))}

          {devices.length === 0 && !loading && (
            <div className="col-span-full py-20 text-center border-2 border-dashed border-white/5 rounded-3xl">
              <Activity className="w-12 h-12 text-slate-700 mx-auto mb-4" />
              <p className="text-slate-500 text-lg">No hay dispositivos registrados</p>
            </div>
          )}
        </div>

      </main>
    </div>
  );
};

export default Dashboard;