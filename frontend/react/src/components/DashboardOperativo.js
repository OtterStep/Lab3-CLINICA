import React, { useEffect, useState } from 'react';
import { getResumenOperativo, buscarPacientePorDni } from '../services/api';
import MetricCard from './MetricCard';
import { BarChartComponent, PieChartComponent, LineChartComponent } from './Charts';

const DashboardOperativo = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dni, setDni] = useState('');
  const [pacienteInfo, setPacienteInfo] = useState(null);
  const [searchError, setSearchError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setSearchError('');
    setPacienteInfo(null);
    try {
      const res = await buscarPacientePorDni(dni);
      setPacienteInfo(res.data);
    } catch (err) {
      setSearchError('Paciente no encontrado o error en servidor');
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getResumenOperativo();
        setData(res.data);
      } catch (error) {
        console.error('Error fetching data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="text-center p-10">Cargando...</div>;
  if (!data) return <div className="text-center p-10">No hay datos disponibles</div>;

  const nivelesData = (data.niveles || []).map(n => ({ name: n.nivel_urgencia, value: n.count }));
  const horasData = (data.triajes_por_hora || []).map(h => ({ hora: `${h.hora}:00`, cantidad: h.count }));
  const sintomasData = (data.sintomas_top || []).map(s => ({ sintoma: (s.sintomas || "").substring(0, 20), count: s.count }));

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard Operacional</h1>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input 
            type="text" 
            placeholder="Buscar por DNI..." 
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={dni}
            onChange={(e) => setDni(e.target.value)}
          />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
            🔍 Buscar
          </button>
        </form>
      </div>

      {pacienteInfo && (
        <div className="bg-blue-50 p-4 rounded-xl border border-blue-200 mb-8 animate-fade-in">
          <h3 className="text-blue-800 font-bold mb-2">Información del Paciente</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="font-semibold">Nombre:</span> {pacienteInfo.nombre_completo}</div>
            <div><span className="font-semibold">DNI:</span> {pacienteInfo.documento_identidad}</div>
            <div><span className="font-semibold">Última Urgencia:</span> 
              <span className={`ml-2 px-2 py-1 rounded text-xs font-bold uppercase ${
                pacienteInfo.ultima_urgencia === 'crítico' ? 'bg-red-500 text-white' :
                pacienteInfo.ultima_urgencia === 'alto' ? 'bg-orange-500 text-white' :
                pacienteInfo.ultima_urgencia === 'moderado' ? 'bg-yellow-500 text-black' : 'bg-green-500 text-white'
              }`}>
                {pacienteInfo.ultima_urgencia || 'N/A'}
              </span>
            </div>
            <div><span className="font-semibold">Contacto:</span> {pacienteInfo.contacto}</div>
          </div>
        </div>
      )}
      {searchError && <div className="text-red-500 text-sm mb-4">{searchError}</div>}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <MetricCard title="Total Triajes Hoy" value={data.total_triajes} icon="📊" color="#3B82F6" />
        <MetricCard title="Tiempo Promedio entre Triajes" value={`${data.tiempo_promedio_entre_triajes} min`} icon="⏱️" color="#10B981" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PieChartComponent data={nivelesData} title="Distribución de Urgencia Hoy" />
        <BarChartComponent data={horasData} xKey="hora" yKey="cantidad" title="Triajes por Hora" />
        <BarChartComponent data={sintomasData} xKey="sintoma" yKey="count" title="Síntomas más Frecuentes" />
      </div>
    </div>
  );
};

export default DashboardOperativo;
