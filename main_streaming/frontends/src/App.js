// src/App.js
import React, {useState} from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import OrderChart from './components/OrderChart';
import Login from './components/Login'
import UserStats from './components/UserStats'
import AdminDashboard from './components/AdminDashboard';


const App = () => {

  const [userUuid, setUserUuid] = useState(null);


  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login onLogin={setUserUuid} />} />
        <Route path="/order/:uuid" element={<OrderChart />} />
        <Route path="/user-stats" element={<UserStats />} /> 
        <Route path="/admin" element={<AdminDashboard/>} />

      </Routes>
    </Router>
    
  );
};

export default App;
