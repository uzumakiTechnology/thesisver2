import React from 'react';
import '../App.css';

const Table = ({ data }) => { // Change 'orderData' to 'data' to match the prop name
    // Check if data is undefined or empty
    if (!data || data.length === 0) {
      console.log('No data available');
      return (
        <div className="table-container">
          <p>No data available</p>
        </div>
      );
    }
  
    return (
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Market Price</th>
              <th>Stop Size</th>
              <th>Stop Loss</th>
            </tr>
          </thead>
          <tbody>
            {data.map((dataItem, index) => { // Rename 'data' to 'dataItem' to avoid shadowing
              return (
                <tr key={index}>
                  <td>{dataItem.market_price}</td>
                  <td>{dataItem.stopsize}</td>
                  <td>{dataItem.stoploss}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

export default Table;
