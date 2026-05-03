import React, { useEffect, useState } from 'react';
import { getResumenOperativo } from '../services/api';
import MetricCard from './MetricCard';
import { BarChartComponent, PieChartComponent, LineChartComponent } from './Charts';

const DashboardOperativo = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

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
      <h1 className="text-2xl font-bold mb-6">Dashboard Operacional</h1>
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
