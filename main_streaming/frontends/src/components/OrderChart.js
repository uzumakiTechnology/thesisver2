import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import * as d3 from "d3";
import io from 'socket.io-client';
import Table from "./Table";

const OrderChart = () => {

  const { uuid } = useParams();
  const [orderData, setOrderData] = useState([]);
  const d3Chart = useRef();
  const socketRef = useRef();   
  const [sellOrderMessage, setSellOrderMessage] = useState('');
  const [countNewPriceMessage, setCountNewPriceMessage] = useState('');
  const [orderEvaluation, setOrderEvaluation] = useState('');
  const [percentChange, setPercentChange] = useState('')
  const starPaths = "M10,0 L12.9,7 H20 L14.5,11.25 L17.4,18 L10,13.75 L2.6,18 L5.5,11.25 L0,7 H7.1 L10,0 Z";


  const currentTime = new Date();
  const xDomain = new Date(currentTime.getTime() + 3 * 60 * 60 * 1000);
  const margin = { top: 20, right: 20, bottom: 30, left: 50 };
  const width = 960 - margin.left - margin.right;
  const height = 500 - margin.top - margin.bottom;  
  const xScale = useRef(d3.scaleTime().domain([currentTime, xDomain]).range([0, width])).current;
  const yScale = useRef(d3.scaleLinear().domain([50, 150]).range([height, 0])).current;

  useEffect(() => {
    const fetchOrderData = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/orders/${uuid}/history`);
        if (!response.ok) {
          throw new Error("Network response was not ok"); 
        }
        const historyData = await response.json();
        const sortedData = historyData.map(d => ({
          ...d,
          time: new Date(d.timestamp)
        })).sort((a, b) => a.time - b.time);
        setOrderData(sortedData); 

    } catch (error) {
        console.error('Fetching order data failed:', error);
      }
    };
    const fetchPercentChange = async () =>{
      try {
        const response = await fetch(`http://127.0.0.1:8000/orders/${uuid}/percent_change`);
        const data  = await response.json();
        console.log('%', data)
        setPercentChange(data.percentage_change);
        if (!response.ok) {
          throw new Error("Network response was not ok"); 
        }
      } catch (error) {
        console.error('Fetching order data failed:', error);

      }
    }

    fetchOrderData(); 
    fetchPercentChange();
  }, [uuid]);

  const fetchOrderStatus = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/orders/${uuid}/status`);
      if (!response.ok) {
        throw new Error("Failed to fetch order status");
      }
      const statusData = await response.json();
      console.log('status', statusData);
      if (statusData.is_matched) {
        const countResponse = await fetch(`http://127.0.0.1:8000/orders/${uuid}/count_new_price_come`);
        const evaluationResponse = await fetch(`http://127.0.0.1:8000/orders/${uuid}/evaluation`);

        if(!countResponse.ok){
          throw new Error("Failed to fetch price update count");
        }
        if(!evaluationResponse.ok){
          throw new Error("Failed to fetch price update count");
        }

        const countData = await countResponse.json();
        const evaluateData = await evaluationResponse.json();

        const message = `Sell order triggered for order ${uuid} at price ${statusData.selling_price}`;
        const countMessage = `Sell order triggered for order ${uuid} after ${countData.price_update_count} times new price sent`;
        const evaluationMessage = evaluateData.explanation || 'Evaluation details not available';

        setSellOrderMessage(message);
        setCountNewPriceMessage(countMessage);
        setOrderEvaluation(evaluationMessage);

      }
    } catch (error) {
      console.error("Error fetching order status:", error);
    }
  };


 
  useEffect(() => {
    const svg = d3.select(d3Chart.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .style('border', '1px solid black');

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    xScale.nice();

    const xAxis = d3.axisBottom(xScale)
      .ticks(d3.timeHour.every(0.5)) // Change this to a larger interval if needed
      .tickFormat(d3.timeFormat("%H:%M"));
    
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .attr('class', 'x-axis')
      .call(xAxis);

    g.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(yScale));

    socketRef.current = io(`http://127.0.0.1:8000`, {
      transports: ['websocket'], 
    });

    socketRef.current.on('connect', () => {
      console.log('Socket connected:', socketRef.current.id);
    });

    socketRef.current.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    socketRef.current.on(`order_update_${uuid}`, (newData) => {
      console.log('New data from socket:', newData);
      setOrderData(currentData => {
        const newDataWithDate = {
          ...newData,
          time: new Date(newData.timestamp)
        };
        if (!currentData.some(d => d.time.getTime() === newDataWithDate.time.getTime())) {
          return [...currentData, newDataWithDate].sort((a, b) => a.time - b.time); // Keep data sorted
        }
    
        return currentData; 
      }); 
    });  

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    }; 
  }, [uuid, width, height,xScale, yScale]);

  useEffect(() => {
    if (orderData.length > 0) {
      updateChart();
    }
  }, [orderData]);


  const updateChart = (newData, initialize = false) =>{    
    d3.select(d3Chart.current).selectAll('.market-point, .stop-loss-point, .market-line, .stop-loss-line').remove();

    const svg = d3.select(d3Chart.current);
    const g = svg.select('g');

    const processedData = orderData.map(d =>({
      time: new Date(d.time),
      market_price: +d.market_price,
      stoploss: +d.stoploss,
      is_matched: d.is_matched === "True", 
    }));

    console.log("Process data 🤡", processedData);

    const sellTriggerIndex = processedData.findIndex(d => d.is_matched);
    const stopLossLineData = sellTriggerIndex !== -1 ? processedData.slice(0, sellTriggerIndex + 1) : processedData;


    const timeExtent = d3.extent(processedData, d => d.time);
    let newDomainStart = timeExtent[0] < currentTime ? timeExtent[0] : currentTime;
    let newDomainEnd = timeExtent[1] > xDomain ? timeExtent[1] : xDomain;

    if (timeExtent[0] < newDomainStart) {
      newDomainStart = timeExtent[0];
    }
    if (timeExtent[1] > newDomainEnd) {
      newDomainEnd = timeExtent[1];
    }

    xScale.domain([newDomainStart, newDomainEnd]);

    const marketLine = d3.line()
      .x(d => xScale(d.time))
      .y(d => yScale(d.market_price))
      .curve(d3.curveMonotoneX);
      

    g.selectAll('.market-line')
    .data([processedData]) 
    .join(
      enter => enter.append('path')
        .attr('class', 'market-line')
        .attr('d', marketLine)
        .attr('fill', 'none')
        .attr('stroke', 'orange')
        .attr('stroke-width', 2),
      update => update.call(update => update.transition().attr('d', marketLine))
    );

    const stopLossLine = d3.line()
      .x(d => xScale(d.time))
      .y(d => yScale(d.stoploss))
      .curve(d3.curveMonotoneX);

    g.selectAll('.stop-loss-line')
    .data([stopLossLineData]) 
    .join(
      enter => enter.append('path')
        .attr('class', 'stop-loss-line')
        .attr('d', stopLossLine)
        .attr('fill', 'none')
        .attr('stroke', 'red')
        .attr('stroke-width', 2),
      update => update.call(update => update.transition().attr('d', stopLossLine))
    );

    g.selectAll('.market-point')
      .data(processedData)
      .join('circle')
      .attr('class', 'market-point')
      .attr('cx', d => xScale(d.time))
      .attr('cy', d => yScale(d.market_price))
      .attr('r', 4)
      .attr('fill', 'orange');

    g.selectAll('.stoploss-point')
      .data(stopLossLineData)
      .join('circle')
      .attr('class', 'stoploss-point')
      .attr('cx', d => xScale(d.time))
      .attr('cy', d => yScale(d.stoploss))
      .attr('r', 4)
      .attr('fill', 'red');

      if (sellTriggerIndex !== -1) {
        const intersectionPoint = stopLossLineData[sellTriggerIndex];
        const starPath = starPaths; 
        
        g.append('path')
          .datum(intersectionPoint) // Bind the intersection point data
          .attr('class', 'star-marker')
          .attr('d', starPath)
          .attr('transform', d => `translate(${xScale(d.time) - 10},${yScale(d.stoploss) - 10})`) // Adjust translation as needed
          .attr('fill', 'gold');
      }
};
const renderLegend = () => {
  return (
    <div style={styles.legendContainer}>
      <h4 style={styles.legendTitle}>Symbol Meaning</h4>
      <div style={styles.legendItem}>
        <div style={styles.marketLineSymbol}></div>
        <p style={styles.legendText}>Market Line</p>
      </div>
      <div style={styles.legendItem}>
        <div style={styles.stopLossLineSymbol}></div>
        <p style={styles.legendText}>Stop Loss Line</p>
      </div>
      <div style={styles.legendItem}>
        <svg width="20" height="20" viewBox="0 0 20 20" style={styles.starSymbol}>
          <path d={starPaths} fill="yellow" />
        </svg>
        <p style={styles.legendText}>Trigger Point</p>
      </div>
    </div>
  );
};


useEffect(() => {
  updateChart();
}, [orderData]);

useEffect(() => {
  const statusCheckInterval = setInterval(fetchOrderStatus, 3000); // Check every 5 seconds

  return () => {
    clearInterval(statusCheckInterval);
  };
}, [uuid]);

  return (
<div>
      <h2 style={styles.header}>Order Data for UUID: {uuid}</h2>
      <div style={styles.chartContainer}>
      {renderLegend()}
        <svg ref={d3Chart} className="svg-container" style={styles.svgContainer} />
        {sellOrderMessage && <div style={styles.message}>{sellOrderMessage}</div>}
        {countNewPriceMessage && <div style={styles.message}>{countNewPriceMessage}</div>}
        {orderEvaluation && <div style={styles.message}>{orderEvaluation}</div>}
        <h1>Percentage Change: {percentChange}%</h1>

      </div>
      <Table data={orderData} />
    </div>
  );
};





const styles = {
  message: {
    color: '#dc3545', 
    fontSize: '1rem',
    marginTop: '1rem',
    padding: '0.5rem',
    border: '1px solid #dc3545',
    borderRadius: '0.25rem',
    backgroundColor: '#f8d7da', 
    textAlign: 'center', 
    maxWidth: '80%', 
    margin: '20px auto' 
  },
  chartContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginTop: '2rem',
  },
  svgContainer: {
    boxShadow: '0px 0px 10px rgba(0, 0, 0, 0.1)',
    borderRadius: '0.25rem',
    overflow: 'hidden',
    margin: '20px 0' 
  },
  header: {
    textAlign: 'center',
    color: '#333', 
    marginBottom: '1rem' 
  },
  legendContainer: {
    marginTop: '20px',
    padding: '10px',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    position:'absolute',
    left:200,
    top:200
    },
    legendTitle: {
    textAlign: 'center',
    marginBottom: '10px',
    },
    legendItem: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '5px',
    },
    marketLineSymbol: {
    width: '20px',
    height: '2px',
    backgroundColor: 'orange',
    marginRight: '5px',
    },
    stopLossLineSymbol: {
    width: '20px',
    height: '2px',
    backgroundColor: 'red',
    marginRight: '5px',
    },
    triggerPointSymbol: {
    display: 'inline-block',
    color: 'blue',
    marginRight: '5px',
    content: '',
    svg:'M10,0 L12.9,7 H20 L14.5,11.25 L17.4,18 L10,13.75 L2.6,18 L5.5,11.25 L0,7 H7.1 L10,0 Z' // This is a simple unicode star
    },
    legendText: {
    marginLeft: '5px',
    },
};

export default OrderChart;
