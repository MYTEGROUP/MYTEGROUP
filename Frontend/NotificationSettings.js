import React, { useState, useEffect } from 'react';

const NotificationSettings = () => {
  const [bills, setBills] = useState([]);
  const [selectedBills, setSelectedBills] = useState([]);
  const [notificationMethods, setNotificationMethods] = useState({
    email: false,
    sms: false,
    inApp: false,
  });
  const [notificationFrequency, setNotificationFrequency] = useState('daily');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Fetch available bills from backend on component mount
  useEffect(() => {
    fetch('/api/get-bills')
      .then(response => response.json())
      .then(data => setBills(data.bills))
      .catch(err => setError('Failed to fetch bills.'));
  }, []);

  // Handle bill selection
  const handleBillChange = (e) => {
    const billId = e.target.value;
    setSelectedBills(prev =>
      prev.includes(billId) ? prev.filter(id => id !== billId) : [...prev, billId]
    );
  };

  // Handle notification method changes
  const handleMethodChange = (e) => {
    const { name, checked } = e.target;
    setNotificationMethods(prev => ({ ...prev, [name]: checked }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    // Validate inputs
    if (notificationMethods.email && !validateEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (notificationMethods.sms && !validatePhone(phone)) {
      setError('Please enter a valid phone number.');
      return;
    }
    if (selectedBills.length === 0) {
      setError('Please select at least one bill to subscribe.');
      return;
    }
    if (!Object.values(notificationMethods).some(method => method)) {
      setError('Please select at least one notification method.');
      return;
    }

    const preferences = {
      bills: selectedBills,
      methods: notificationMethods,
      frequency: notificationFrequency,
      email: notificationMethods.email ? email : '',
      phone: notificationMethods.sms ? phone : '',
    };

    try {
      const response = await fetch('/api/update-notification-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      });
      const result = await response.json();
      if (response.ok) {
        setMessage('Notification preferences updated successfully.');
      } else {
        setError(result.message || 'Failed to update preferences.');
      }
    } catch (err) {
      setError('An error occurred while updating preferences.');
    }
  };

  // Validate email format
  const validateEmail = (email) => {
    const regex = /^\S+@\S+\.\S+$/;
    return regex.test(email);
  };

  // Validate phone number format
  const validatePhone = (phone) => {
    const regex = /^\+?[1-9]\d{1,14}$/;
    return regex.test(phone);
  };

  return (
    <div className="notification-settings-container">
      <h2>Notification Settings</h2>
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}
      <form onSubmit={handleSubmit}>
        <div className="section">
          <h3>Subscribe to Bills</h3>
          {bills.map(bill => (
            <div key={bill.id} className="checkbox">
              <label>
                <input
                  type="checkbox"
                  value={bill.id}
                  checked={selectedBills.includes(bill.id)}
                  onChange={handleBillChange}
                />
                {bill.name}
              </label>
            </div>
          ))}
        </div>
        <div className="section">
          <h3>Notification Methods</h3>
          <div className="checkbox">
            <label>
              <input
                type="checkbox"
                name="email"
                checked={notificationMethods.email}
                onChange={handleMethodChange}
              />
              Email
            </label>
          </div>
          {notificationMethods.email && (
            <div className="input-field">
              <label>Email Address:</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
          )}
          <div className="checkbox">
            <label>
              <input
                type="checkbox"
                name="sms"
                checked={notificationMethods.sms}
                onChange={handleMethodChange}
              />
              SMS
            </label>
          </div>
          {notificationMethods.sms && (
            <div className="input-field">
              <label>Phone Number:</label>
              <input
                type="tel"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                required
              />
            </div>
          )}
          <div className="checkbox">
            <label>
              <input
                type="checkbox"
                name="inApp"
                checked={notificationMethods.inApp}
                onChange={handleMethodChange}
              />
              In-App
            </label>
          </div>
        </div>
        <div className="section">
          <h3>Notification Frequency</h3>
          <select
            value={notificationFrequency}
            onChange={e => setNotificationFrequency(e.target.value)}
          >
            <option value="immediate">Immediate</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        <button type="submit">Save Preferences</button>
      </form>
    </div>
  );
};

export default NotificationSettings;