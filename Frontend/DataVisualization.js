import React, { useState, useEffect, useMemo } from 'react';
import { Bar, Line, Pie } from 'react-chartjs-2';
import axios from 'axios';
import 'chart.js/auto';

const DataVisualization = () => {
  // State to hold bill data
  const [billData, setBillData] = useState([]);
  // State for filters
  const [filters, setFilters] = useState({
    status: 'All',
    sponsor: 'All',
    topic: 'All',
  });
  // State for chart type
  const [chartType, setChartType] = useState('Bar');
  // State for loading and error handling
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch bill data from backend API on component mount
  useEffect(() => {
    const fetchBillData = async () => {
      try {
        const response = await axios.get('/api/bill_dashboard');
        setBillData(response.data);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching bill data:', error);
        setError('Failed to load bill data.');
        setIsLoading(false);
      }
    };
    fetchBillData();
  }, []);

  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prevFilters) => ({
      ...prevFilters,
      [name]: value,
    }));
  };

  // Memoized filtered data based on user-selected filters
  const filteredData = useMemo(() => {
    return billData.filter((bill) => {
      return (
        (filters.status === 'All' || bill.status === filters.status) &&
        (filters.sponsor === 'All' || bill.sponsor === filters.sponsor) &&
        (filters.topic === 'All' || bill.topic === filters.topic)
      );
    });
  }, [billData, filters]);

  // Memoized chart data preparation
  const chartData = useMemo(() => {
    // Example: Bill progress by status
    const statusCounts = filteredData.reduce((acc, bill) => {
      acc[bill.status] = (acc[bill.status] || 0) + 1;
      return acc;
    }, {});

    return {
      labels: Object.keys(statusCounts),
      datasets: [
        {
          label: 'Number of Bills',
          data: Object.values(statusCounts),
          backgroundColor: 'rgba(75,192,192,0.6)',
          borderWidth: 1,
        },
      ],
    };
  }, [filteredData]);

  // Define chart options with enhanced interactive elements
  const chartOptions = {
    responsive: true,
    plugins: {
      tooltip: {
        callbacks: {
          label: function (context) {
            return `Count: ${context.parsed.y}`;
          },
          title: function (context) {
            return `Status: ${context[0].label}`;
          },
        },
      },
      legend: {
        display: true,
        position: 'top',
      },
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const chartElement = elements[0];
        const label = chartData.labels[chartElement.index];
        const value = chartData.datasets[0].data[chartElement.index];
        alert(`You clicked on ${label} with count ${value}`);
      }
    },
  };

  // Handle chart type change
  const handleChartTypeChange = (e) => {
    setChartType(e.target.value);
  };

  // Render loading state
  if (isLoading) {
    return <div className="loading">Loading data...</div>;
  }

  // Render error state
  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="data-visualization-container">
      {/* Filter Controls */}
      <div className="filters">
        <label>
          Status:
          <select name="status" value={filters.status} onChange={handleFilterChange}>
            <option value="All">All</option>
            <option value="Introduced">Introduced</option>
            <option value="In Committee">In Committee</option>
            <option value="Passed">Passed</option>
            <option value="Failed">Failed</option>
          </select>
        </label>
        <label>
          Sponsor:
          <select name="sponsor" value={filters.sponsor} onChange={handleFilterChange}>
            <option value="All">All</option>
            {/* Dynamically populate sponsor options based on billData */}
            {[...new Set(billData.map((bill) => bill.sponsor))].map((sponsor) => (
              <option key={sponsor} value={sponsor}>
                {sponsor}
              </option>
            ))}
          </select>
        </label>
        <label>
          Topic:
          <select name="topic" value={filters.topic} onChange={handleFilterChange}>
            <option value="All">All</option>
            {/* Dynamically populate topic options based on billData */}
            {[...new Set(billData.map((bill) => bill.topic))].map((topic) => (
              <option key={topic} value={topic}>
                {topic}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Chart Type Selection */}
      <div className="chart-type-selector">
        <label>
          Chart Type:
          <select value={chartType} onChange={handleChartTypeChange}>
            <option value="Bar">Bar</option>
            <option value="Line">Line</option>
            <option value="Pie">Pie</option>
          </select>
        </label>
      </div>

      {/* Chart Rendering */}
      <div className="chart">
        {chartType === 'Bar' && <Bar data={chartData} options={chartOptions} />}
        {chartType === 'Line' && <Line data={chartData} options={chartOptions} />}
        {chartType === 'Pie' && <Pie data={chartData} options={chartOptions} />}
      </div>

      {/* Styles for responsiveness and enhanced UI */}
      <style jsx>{`
        .data-visualization-container {
          padding: 20px;
          max-width: 1200px;
          margin: auto;
        }
        .filters,
        .chart-type-selector {
          display: flex;
          justify-content: space-around;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .filters label,
        .chart-type-selector label {
          margin: 10px;
          min-width: 150px;
        }
        .chart {
          position: relative;
          height: 60vh;
          width: 100%;
        }
        .loading,
        .error {
          text-align: center;
          font-size: 1.2em;
          margin-top: 50px;
        }
        @media (max-width: 768px) {
          .filters,
          .chart-type-selector {
            flex-direction: column;
            align-items: center;
          }
          .filters label,
          .chart-type-selector label {
            width: 100%;
            max-width: 300px;
          }
        }
      `}</style>
    </div>
  );
};

export default DataVisualization;