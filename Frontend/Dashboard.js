import React, { useState, useEffect } from 'react';
import { Bar, Pie } from 'react-chartjs-2';
import Chart from 'chart.js/auto';
import './Dashboard.css';

const Dashboard = () => {
  // State variables for data, filters, loading, and error
  const [billData, setBillData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [sponsorFilter, setSponsorFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch bill data from the backend on component mount
  useEffect(() => {
    fetch('/api/bill_dashboard')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setBillData(data);
        setFilteredData(data);
        setLoading(false);
      })
      .catch(error => {
        setError(error.message);
        setLoading(false);
      });
  }, []);

  // Update filtered data whenever filters change
  useEffect(() => {
    let data = billData;

    if (statusFilter) {
      data = data.filter(bill => bill.status === statusFilter);
    }

    if (sponsorFilter) {
      data = data.filter(bill => bill.sponsor === sponsorFilter);
    }

    if (topicFilter) {
      data = data.filter(bill => bill.topic.includes(topicFilter));
    }

    setFilteredData(data);
  }, [statusFilter, sponsorFilter, topicFilter, billData]);

  // Get unique values for filters
  const getUniqueValues = (key) => {
    return [...new Set(billData.map(item => item[key]))];
  };

  // Prepare data for status distribution chart
  const statusDistribution = {
    labels: getUniqueValues('status'),
    datasets: [
      {
        label: '# of Bills',
        data: getUniqueValues('status').map(status => filteredData.filter(bill => bill.status === status).length),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
    ],
  };

  // Prepare data for sponsor distribution chart
  const sponsorDistribution = {
    labels: getUniqueValues('sponsor'),
    datasets: [
      {
        label: '# of Bills',
        data: getUniqueValues('sponsor').map(sponsor => filteredData.filter(bill => bill.sponsor === sponsor).length),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      },
    ],
  };

  // Handle filter changes
  const handleStatusChange = (e) => {
    setStatusFilter(e.target.value);
  };

  const handleSponsorChange = (e) => {
    setSponsorFilter(e.target.value);
  };

  const handleTopicChange = (e) => {
    setTopicFilter(e.target.value);
  };

  if (loading) {
    return <div className="dashboard-container">Loading...</div>;
  }

  if (error) {
    return <div className="dashboard-container">Error: {error}</div>;
  }

  return (
    <div className="dashboard-container">
      <h1>Legislative Dashboard</h1>
      <div className="filters">
        <div className="filter">
          <label>Status:</label>
          <select value={statusFilter} onChange={handleStatusChange}>
            <option value="">All</option>
            {getUniqueValues('status').map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
        </div>
        <div className="filter">
          <label>Sponsor:</label>
          <select value={sponsorFilter} onChange={handleSponsorChange}>
            <option value="">All</option>
            {getUniqueValues('sponsor').map(sponsor => (
              <option key={sponsor} value={sponsor}>{sponsor}</option>
            ))}
          </select>
        </div>
        <div className="filter">
          <label>Topic:</label>
          <select value={topicFilter} onChange={handleTopicChange}>
            <option value="">All</option>
            {getUniqueValues('topic').map(topic => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="charts">
        <div className="chart">
          <h2>Status Distribution</h2>
          <Bar data={statusDistribution} />
        </div>
        <div className="chart">
          <h2>Sponsor Distribution</h2>
          <Pie data={sponsorDistribution} />
        </div>
      </div>
      <div className="bill-list">
        <h2>Bill List</h2>
        <table>
          <thead>
            <tr>
              <th>Bill ID</th>
              <th>Title</th>
              <th>Status</th>
              <th>Sponsor</th>
              <th>Topic</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map(bill => (
              <tr key={bill.id}>
                <td>{bill.id}</td>
                <td>{bill.title}</td>
                <td>{bill.status}</td>
                <td>{bill.sponsor}</td>
                <td>{bill.topic.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;