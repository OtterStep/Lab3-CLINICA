import React from 'react';

const MetricCard = ({ title, value, icon, color }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm uppercase tracking-wide">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
        {icon && <div className="text-3xl">{icon}</div>}
      </div>
    </div>
  );
};

export default MetricCard;
