// src/components/AdminOrderStatsChart.js
import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import Chart from 'chart.js/auto';

const AdminOrderStatsChart = () => {
  const [chartData, setChartData] = useState({
    labels: ['Total Orders', 'Ended Orders', 'Ongoing Orders'],
    datasets: [
      {
        label: 'Number of Orders',
        data: [0, 0, 0], // Placeholder data
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(255, 206, 86, 1)'
        ],
        borderWidth: 1,
      },
    ],
  });

  useEffect(() => {
    const fetchOrderStats = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/admin/order-stats');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setChartData({
          labels: ['Total Orders', 'Ended Orders', 'Ongoing Orders'],
          datasets: [
            {
              label: 'Number of Orders',
              data: [data.total_orders, data.ended_orders, data.ongoing_orders],
              backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(255, 206, 86, 0.6)'
              ],
              borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 206, 86, 1)'
              ],
              borderWidth: 1,
            },
          ],
        });
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchOrderStats();
  }, []);

  return (
    <div style={{ width: '100%', height: '400px' }}> {/* Set a fixed height for the container */}
      <h2>Order Statistics</h2>
      <Bar data={chartData} options={{ indexAxis: 'y' }} />
    </div>
  );
};

export default AdminOrderStatsChart;
