// ProcessingTimeChart.js
import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

const ProcessingTimeChart = () => {
  const [chartData, setChartData] = useState({
    labels: [], // This will hold time points
    datasets: [{
      label: 'Processing Time (seconds)',
      data: [], // Data points for processing time
      fill: false,
      borderColor: 'rgba(255, 99, 132, 0.6)',
      tension: 0.1
    }]
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/processing-times'); // Replace with your backend URL
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        // Assuming 'data' is an array of objects with 'time' and 'processingTime' properties
        setChartData({
          labels: data.map(item => item.time),
          datasets: [{
            ...chartData.datasets[0],
            data: data.map(item => item.processingTime)
          }]
        });
      } catch (error) {
        console.error('Error fetching processing time data:', error);
      }
    };

    fetchData();
  }, []);

  return (
    <div>
      <h2>Processing Time Chart</h2>
      <Line data={chartData} />
    </div>
  );
};

export default ProcessingTimeChart;
