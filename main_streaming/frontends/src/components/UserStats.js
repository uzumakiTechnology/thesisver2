import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Sparklines, SparklinesLine } from "react-sparklines";
import { FaArrowUp, FaArrowDown } from "react-icons/fa";

const OrderDetail = ({ order }) => {
  const [percentageChange, setPercentageChange] = useState(null);

  useEffect(() => {
    // Ensure that order has a uuid before making the call
    const fetchPercentage = async () => {
    fetch(`http://127.0.0.1:8000/orders/${order.uuid}/percent_change`)
        .then((response) => response.json())
        .then((data) => {
          setPercentageChange(data.percentage_change);
        })
        .catch((error) => console.error('Error:', error));

      const response = await fetch(`http://127.0.0.1:8000/orders/${order.uuid}/percent_change`)
      const data = await response.json();
      console.log('percent', data)

    }
    fetchPercentage();
  }, [order]);

  return (
    <div style={styles.orderItem}>
      <span style={styles.orderUuidText}>Percentage Change</span>
      <div>
      <Sparklines data={percentageChange ? [percentageChange] : []} width={100} height={20}>
      <SparklinesLine color="blue" />
      </Sparklines>
        {percentageChange !== null && (
          <span>
            {percentageChange > 0 ? (
              <FaArrowUp color="green" />
            ) : (
              <FaArrowDown color="red" />
            )}
            {Math.abs(percentageChange).toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
};

const UserStats = () => {
  const [orderStats, setOrderStats] = useState(null);
  const [orders, setOrders] = useState([]); // state to hold individual orders
  const navigate = useNavigate();
  const location = useLocation();
  const userUuid = location.state?.user_id;
  
  console.log('Location state:', location.state);
  

  const renderStatusLine = (status) => {
    if (status === "matched") {
      // Straight line for 'matched'
      return (
        <svg style={styles.statusLine} viewBox="0 0 40 10">
          <line x1="0" y1="5" x2="40" y2="5" stroke="#4CAF50" strokeWidth="2" />
        </svg>
      );
    } else {
      // Fluctuating line for 'updated'
      return (
        <svg style={styles.statusLine} viewBox="0 0 40 10">
          <path
            d="M0 5 Q10 0, 20 5 T40 5"
            stroke="#FFC107"
            strokeWidth="2"
            fill="none"
          />
        </svg>
      );
    }
  };
  const renderLegend = () => {
    return (
      <div style={styles.legendContainer}>
        <h4>Symbol Meaning</h4>
        <div>
          <svg
            style={styles.statusLine}
            viewBox="0 0 40 10">
            <line x1="0" y1="5" x2="40" y2="5" stroke="#4CAF50"strokeWidth="2"/>
          </svg>
          <p>Order Completed</p>
        </div>
        <div>
          <svg style={styles.statusLine} viewBox="0 0 40 10">
            <path
              d="M0 5 Q10 0, 20 5 T40 5"
              stroke="#FFC107"
              strokeWidth="2"
              fill="none"
            />
          </svg>
          <p>Order Active</p>
        </div>
      </div>
    );
  };

  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/user/${userUuid}/orders/stats`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setOrderStats(data);
        console.log("stats", data);

      } catch (error) {
        console.error('Error fetching order stats:', error);
      }
    };


    const fetchOrders = async () => {
      const response = await fetch(`http://127.0.0.1:8000/user/${userUuid}/orders`);
      const data = await response.json();
      console.log("single user data:", data);
      setOrders(data);
    };
    fetchData();
    fetchOrders();
  }, [userUuid]);

  // Function to handle order click
  const handleOrderClick = (orderId) => {
    navigate(`/order/${orderId}`);
  };

  if (!orderStats) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      {renderLegend()}
      <h2 style={styles.header}>User Order Statistics</h2>
      <div style={styles.statsContainer}>
        <div style={styles.statItem}>
          <span style={styles.statLabel}>Matched Orders:</span>
          <span style={styles.statValue}>
            {orderStats.matched_orders_count}
          </span>
        </div>
        <div style={styles.statItem}>
          <span style={styles.statLabel}>Unmatched Orders:</span>
          <span style={styles.statValue}>
            {orderStats.unmatched_orders_count}
          </span>
        </div>
      </div>
      <div style={styles.ordersContainer}>
        {orders.map((order) => (
          <>
            <OrderDetail key={order.uuid} order={order} />
            <div
              key={order.uuid}
              style={styles.orderItem}
              onClick={() => handleOrderClick(order.uuid)}
            >
              <span style={styles.orderUuid}>
                {" "}
                <div style={styles.orderUuidText}>Order UUID</div> {order.uuid}
              </span>
              {renderStatusLine(order.status)}
            </div>
          </>
        ))}
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    padding: "20px",
    maxWidth: "600px",
    margin: "0 auto",
    backgroundColor: "#fff",
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
    borderRadius: "8px",
    
  },
  orderUuidText: {
    fontWeight: "bold", // Make 'Order UUID:' text bold
    marginRight: "5px", // Add some space between the label and the UUID
  },
  header: {
    textAlign: "center",
    color: "#333",
    marginBottom: "20px",
    fontSize: "32px"
  },
  statsContainer: {
    display: "flex",
    flexDirection: "column",
    marginBottom: "20px",
  },
  statItem: {
    display: "flex",
    justifyContent: "space-between",
    padding: "10px",
    borderBottom: "1px solid #eee",
  },
  statLabel: {
    fontWeight: "bold",
    color: "#555",
  },
  statValue: {
    color: "#333",
  },
  ordersContainer: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: "10px",
  },
  orderBox: {
    padding: "15px",
    borderRadius: "8px",
    backgroundColor: "#f9f9f9",
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.05)",
    cursor: "pointer",
    transition: "transform 0.1s ease-in-out, box-shadow 0.1s ease-in-out",
    display: "flex",
    alignItems: "center", // Align items vertically
    justifyContent: "space-between", // Space between the UUID and the chart/status
    marginBottom: "10px",
    "&:hover": {
      transform: "scale(1.02)", // Slightly increase size on hover
      boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)", // Increase shadow on hover
    },
  },

  orderUuid: {
    fontWeight: "500",
    color: "#000",
    flex: "1 0 auto", // Ensure it doesn't shrink or grow
    marginRight: "10px", // Space before the chart/status
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    fontSize: "24px",
  },
  orderChart: {
    width: "40px", // Fixed width for the chart/status
    height: "20px", // Fixed height for the chart/status
    backgroundColor: "#def", // Example color for the chart/status background
    borderRadius: "5px", // Rounded corners for the chart/status
  },
  statusLine: {
    height: "20px", // Height of the SVG container
  },
  legendContainer: {
    position: "fixed", // Fixed position
    left: "20%", // Positioned 20% from the top of the viewport
    right: "20px", // 20px from the right
    width: "200px", // Width of the container
    backgroundColor: "#fff", // Background color
    padding: "10px", // Padding inside the container
    borderRadius: "8px", // Rounded corners
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)", // Box shadow for a "floating" effect
    zIndex: 1000, // Make sure it's above other elements
  },
};

export default UserStats;
