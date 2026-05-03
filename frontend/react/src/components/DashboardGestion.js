import React, { useEffect, useState } from 'react';
import { getMetricasGestion, getTopPacientes } from '../services/api';
import MetricCard from './MetricCard';
import { BarChartComponent, LineChartComponent, PieChartComponent } from './Charts';

const DashboardGestion = () => {
  const [metricas, setMetricas] = useState(null);
  const [topPacientes, setTopPacientes] = useState([]);
  const [periodo, setPeriodo] = useState('mes');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [metricasRes, topRes] = await Promise.all([
          getMetricasGestion(periodo),
          getTopPacientes()
        ]);
        setMetricas(metricasRes.data);
        setTopPacientes(topRes.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [periodo]);

  if (loading) return <div className="text-center p-10">Cargando...</div>;
  if (!metricas) return <div className="text-center p-10">No hay métricas disponibles</div>;

  const evolucionData = (metricas.evolucion || []).map(e => ({
    periodo: periodo === 'mes' ? new Date(e.mes).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }) : e.anio,
    total: e.total
  }));
  const usuariosData = (metricas.triajes_por_usuario || []).map(u => ({ name: u.nombre_usuario, value: u.total }));
  const nivelesGlobalData = (metricas.niveles_global || []).map(n => ({ name: n.nivel_urgencia, value: n.total }));
  const pacientesData = (topPacientes || []).map(p => ({ nombre: p.nombre_completo, cantidad: p.cantidad }));

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard de Gestión</h1>
      <div className="mb-4">
        <label className="mr-2">Período:</label>
        <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="border rounded p-1">
          <option value="mes">Últimos 12 meses</option>
          <option value="anio">Por año</option>
        </select>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard title="Cumplimiento de Conductas Sugeridas" value={`${metricas.cumplimiento_conductas}%`} icon="✅" color="#F59E0B" />
        <MetricCard title="Tiempo Promedio de Atención" value={`${metricas.tiempo_promedio_atencion_min} min`} icon="⏲️" color="#EF4444" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <LineChartComponent data={evolucionData} xKey="periodo" yKey="total" title="Evolución de Triajes" />
        <PieChartComponent data={usuariosData} title="Triajes por Usuario" />
        <PieChartComponent data={nivelesGlobalData} title="Distribución Global de Urgencia" />
        <BarChartComponent data={pacientesData} xKey="nombre" yKey="cantidad" title="Top 10 Pacientes" />
      </div>
    </div>
  );
};

export default DashboardGestion;
