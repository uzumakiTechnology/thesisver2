import React from 'react'
import AdminOrderStatsChart from './AdminOrderStatsChart';
import ProcessingTimeChart from './ProcessingTimeChart';

const AdminDashboard = () => {

  return (

    <div>
        <h1>Admin Dashboard</h1>
        <AdminOrderStatsChart />
        <br></br>
        <br></br>

        <ProcessingTimeChart />

    </div>
  )
}

export default AdminDashboard