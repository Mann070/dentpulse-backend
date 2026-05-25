const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(bodyParser.json());

// Mock Data
let patients = [
  { id: '1', name: 'Sarah Johnson', age: 45, implantSite: 'Tooth #14', lastVisit: '2/22/2026', stability: 92, riskStatus: 'Low' },
  { id: '2', name: 'Michael Chen', age: 58, implantSite: 'Tooth #30', lastVisit: '2/20/2026', stability: 78, riskStatus: 'Moderate' },
  { id: '3', name: 'Emma Davis', age: 62, implantSite: 'Tooth #19', lastVisit: '2/18/2026', stability: 65, riskStatus: 'High' },
  { id: '4', name: 'Robert Williams', age: 51, implantSite: 'Tooth #3', lastVisit: '2/15/2026', stability: 95, riskStatus: 'Low' },
  { id: '5', name: 'Lisa Anderson', age: 47, implantSite: 'Tooth #46', lastVisit: '2/14/2026', stability: 82, riskStatus: 'Moderate' },
];

const stats = [
  { label: 'Total Patients', value: 347, trend: 12, icon: 'users', color: '#3b82f6' },
  { label: 'Active Implants', value: 892, trend: 8, icon: 'activity', color: '#10b981' },
  { label: 'High Risk Cases', value: 23, trend: 3, icon: 'alert-triangle', color: '#ef4444' },
  { label: 'Success Rate', value: '94.7%', trend: 2.1, icon: 'trending-up', color: '#8b5cf6' },
];

const recommendations = [
  { id: 'im1', type: 'Endosteal Root', dim: '4.5 × 11.5', score: 98, success: 94, risk: 'Low' },
  { id: 'im2', type: 'Tapered Platform', dim: '4.0 × 13.0', score: 82, success: 89, risk: 'Med' }
];

// Routes
app.get('/api/patients', (req, res) => {
  res.json(patients);
});

app.post('/api/patients', (req, res) => {
  const newPatient = {
    id: (patients.length + 1).toString(),
    ...req.body,
    stability: 85,
    lastVisit: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    riskStatus: 'Low',
  };
  patients = [newPatient, ...patients];
  res.status(201).json(newPatient);
});

app.get('/api/stats', (req, res) => {
  res.json(stats);
});

app.get('/api/recommendations', (req, res) => {
  res.json(recommendations);
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date() });
});

app.listen(PORT, () => {
  console.log(`DentPulse AI Clinical Backend running on http://localhost:${PORT}`);
});
