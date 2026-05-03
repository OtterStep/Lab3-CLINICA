import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DashboardOperativo from './components/DashboardOperativo';
import DashboardGestion from './components/DashboardGestion';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-md p-4">
          <div className="container mx-auto flex space-x-4">
            <Link to="/" className="text-blue-600 hover:text-blue-800 font-semibold">Operativo</Link>
            <Link to="/gestion" className="text-blue-600 hover:text-blue-800 font-semibold">Gestión</Link>
          </div>
        </nav>
        <div className="container mx-auto">
          <Routes>
            <Route path="/" element={<DashboardOperativo />} />
            <Route path="/gestion" element={<DashboardGestion />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
