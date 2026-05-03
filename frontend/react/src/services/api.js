import axios from 'axios';

const API_BASE = '/api';

export const getResumenOperativo = () => axios.get(`${API_BASE}/operativo/resumen`);
export const getMetricasGestion = (periodo = 'mes') => axios.get(`${API_BASE}/gestion/metricas?periodo=${periodo}`);
export const getTopPacientes = () => axios.get(`${API_BASE}/pacientes/top`);
