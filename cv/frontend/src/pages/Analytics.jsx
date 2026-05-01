import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  Paper,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Grid,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Timer as TimerIcon
} from '@mui/icons-material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import axios from 'axios'

function Analytics() {
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState(null)
  const [confidenceReport, setConfidenceReport] = useState(null)
  const [days, setDays] = useState(7)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [days])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const [dashboardRes, confidenceRes] = await Promise.all([
        axios.get(`/api/analytics/dashboard?days=${days}`),
        axios.get('/api/analytics/confidence-report')
      ])
      
      setDashboard(dashboardRes.data.dashboard)
      setConfidenceReport(confidenceRes.data.report)
    } catch (error) {
      console.error('Error fetching analytics:', error)
    }
    setLoading(false)
  }

  if (loading || !dashboard || !confidenceReport) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Loading analytics...</Typography>
      </Box>
    )
  }

  // Prepare data for charts
  const emotionData = Object.entries(confidenceReport.emotion_distribution).map(([emotion, count]) => ({
    emotion,
    count
  }))

  const engagementStateData = Object.entries(confidenceReport.engagement_distribution).map(([state, count]) => ({
    state,
    count
  }))

  const emotionTimelineData = dashboard.emotion_timeline.slice(-20).map((item, index) => ({
    time: index,
    score: item.engagement_score,
    emotion: item.emotion
  }))

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Learning Analytics
          </Typography>
          <FormControl sx={{ minWidth: 120 }} size="small">
            <InputLabel sx={{ color: 'white' }}>Period</InputLabel>
            <Select
              value={days}
              onChange={(e) => setDays(e.target.value)}
              sx={{ color: 'white', '.MuiOutlinedInput-notchedOutline': { borderColor: 'white' } }}
            >
              <MenuItem value={1}>Last Day</MenuItem>
              <MenuItem value={7}>Last Week</MenuItem>
              <MenuItem value={30}>Last Month</MenuItem>
            </Select>
          </FormControl>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={3} sx={{ bgcolor: '#667eea', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUpIcon sx={{ mr: 1 }} />
                  <Typography variant="body2">Confidence Score</Typography>
                </Box>
                <Typography variant="h3">
                  {confidenceReport.confidence_percentage}%
                </Typography>
                <Typography variant="caption">
                  {confidenceReport.interpretation}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <PsychologyIcon sx={{ mr: 1 }} />
                  <Typography variant="body2">Avg Engagement</Typography>
                </Box>
                <Typography variant="h3">
                  {dashboard.avg_engagement_score}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Out of 1.0
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TimerIcon sx={{ mr: 1 }} />
                  <Typography variant="body2">Learning Sessions</Typography>
                </Box>
                <Typography variant="h3">
                  {dashboard.learning_sessions}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Materials accessed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="body2" gutterBottom>
                  Total Queries
                </Typography>
                <Typography variant="h3">
                  {dashboard.total_queries}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Topics searched
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={3}>
          {/* Engagement Timeline */}
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Engagement Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={emotionTimelineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="score" stroke="#667eea" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Emotion Distribution */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Emotion Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={emotionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.emotion}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {emotionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Engagement States */}
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Engagement States
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={engagementStateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="state" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#667eea" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Topic Access Distribution */}
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Topics Accessed
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(dashboard.topic_access_distribution).map(([topic, count]) => ({
                  topic,
                  count
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#764ba2" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}

export default Analytics
