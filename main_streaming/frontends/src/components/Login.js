import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = ({ onLogin }) => {
  const [uuid, setUuid] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (event) => {
    event.preventDefault();
    setIsLoading(true);
  
    try {
      const response = await fetch(`http://localhost:8000/login/${uuid}`, {
        method: 'POST',
      });
  
      if (response.ok) {
        const data = await response.json();
        onLogin(data.user_id);
        navigate('/user-stats', { state: { user_id: data.user_id } }); // Ensure data.user_id exists and is correct
      } else {
        alert('Login failed: Invalid UUID or server error.');
      }
      
    } catch (error) {
      alert('Login failed: Network error or server is down.');
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Trailing Stop Sell Order Simulation</h1>
      <form onSubmit={handleLogin} style={styles.form}>
        <input
          type="text"
          value={uuid}
          onChange={(e) => setUuid(e.target.value)}
          placeholder="Enter your UUID"
          style={styles.input}
          disabled={isLoading}
        />
        <button type="submit" style={styles.button} disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

// Styles
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    height: '100vh',
    background: 'linear-gradient(to bottom, #4A90E2, #348AC7)', // Gradient background
    color: 'white', // Text color
  },
  heading: {
    fontSize: '44px',
    marginBottom: '20px',
    fontFamily: 'Arial, sans-serif', // Choose a suitable font
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    width: '300px',
  },
  input: {
    padding: '10px',
    marginBottom: '0px',
    borderRadius: '5px',
    border: '1px solid #ddd',
    fontSize: '16px',
  },
  button: {
    padding: '10px',
    borderRadius: '5px',
    border: 'none',
    backgroundColor: '#5C6BC0',
    color: 'white',
    cursor: 'pointer',
    fontSize: '16px',
    transition: 'background-color 0.2s', // Add a hover effect
  },
};

export default Login;
