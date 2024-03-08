import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

const MetricsChart = () => {
    const [metricsData, setMetricsData] = useState({
        labels: [],
        datasets: [
            {
                label: 'CPU Usage (%)',
                data: [],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            // Add more datasets for memory, disk, etc.
        ]
    });

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:6789');
        ws.onmessage = (event) => {
          const metric = JSON.parse(event.data);
          setMetricsData(prevData => ({
            ...prevData,
            labels: [...prevData.labels, metric.time],
            datasets: prevData.datasets.map(ds => {
              switch (ds.label) {
                case 'CPU Usage (%)':
                  return { ...ds, data: [...ds.data, metric.cpu] };
                case 'Memory Usage (%)': // Example for additional metric
                  return { ...ds, data: [...ds.data, metric.memory] };
                // Add more cases as needed
                default:
                  return ds;
              }
            })
          }));
        };
        return () => ws.close();
      }, []);
    
      return <Line data={metricsData} />;
    };
    

export default MetricsChart;
