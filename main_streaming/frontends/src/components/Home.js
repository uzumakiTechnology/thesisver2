// src/components/Home.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const [uuid, setUuid] = useState('');
  const navigate = useNavigate();

  const handleSubmit = () => {
    // Redirect to the OrderChart page with the UUID
    navigate(`/order/${uuid}`);
  };

  return (
    <div>
      <input
        type="text"
        value={uuid}
        onChange={(e) => setUuid(e.target.value)}
        placeholder="Enter your UUID"
      />
      <button onClick={handleSubmit}>View Order</button>
    </div>
  );
};

export default Home;
