import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export const BarChartComponent = ({ data, xKey, yKey, title }) => (
  <div className="bg-white p-4 rounded shadow">
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    <BarChart width={500} height={300} data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey={xKey} />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey={yKey} fill="#8884d8" />
    </BarChart>
  </div>
);

export const PieChartComponent = ({ data, title }) => (
  <div className="bg-white p-4 rounded shadow">
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    <PieChart width={400} height={300}>
      <Pie data={data} cx="50%" cy="50%" labelLine={false} label={entry => entry.name} outerRadius={80} fill="#8884d8" dataKey="value">
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip />
    </PieChart>
  </div>
);

export const LineChartComponent = ({ data, xKey, yKey, title }) => (
  <div className="bg-white p-4 rounded shadow">
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    <LineChart width={600} height={300} data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey={xKey} />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey={yKey} stroke="#8884d8" />
    </LineChart>
  </div>
);
