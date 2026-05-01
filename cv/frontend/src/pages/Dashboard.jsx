import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Card,
  CardContent,
  Grid
} from '@mui/material'
import {
  Logout as LogoutIcon,
  School as SchoolIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material'
import { useAuth } from '../context/AuthContext'
import axios from 'axios'

function Dashboard() {
  const [query, setQuery] = useState('')
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSearchMaterials = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const response = await axios.post('/api/materials/suggest', {
        query: query
      })
      
      setMaterials(response.data.materials)
      
      // Store query_id for later use
      sessionStorage.setItem('current_query_id', response.data.query_id)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch materials')
    }
    
    setLoading(false)
  }

  const handleStartLearning = (material) => {
    // Navigate to learning session with material
    navigate('/learn', { state: { material } })
  }

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <SchoolIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            EduSynth
          </Typography>
          <Button
            color="inherit"
            startIcon={<AnalyticsIcon />}
            onClick={() => navigate('/analytics')}
          >
            Analytics
          </Button>
          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
          <Typography variant="h4" gutterBottom>
            Welcome, {user?.username}! 👋
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            What would you like to learn today? Type your topic below and I'll suggest 
            the best learning materials for you.
          </Typography>

          <Box component="form" onSubmit={handleSearchMaterials} sx={{ mt: 3 }}>
            <TextField
              fullWidth
              label="What do you want to learn?"
              placeholder="e.g., Python programming, Calculus, World History..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
              multiline
              rows={3}
              sx={{ mb: 2 }}
            />
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={loading}
            >
              {loading ? 'Finding Materials...' : 'Get Learning Materials 🚀'}
            </Button>
          </Box>

          {error && (
            <Typography color="error" sx={{ mt: 2 }}>
              {error}
            </Typography>
          )}
        </Paper>

        {materials.length > 0 && (
          <Box>
            <Typography variant="h5" gutterBottom>
              Suggested Learning Materials
            </Typography>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              {materials.map((material, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Card elevation={2}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography
                          variant="caption"
                          sx={{
                            bgcolor: getTypeColor(material.type),
                            color: 'white',
                            px: 1.5,
                            py: 0.5,
                            borderRadius: 1,
                            fontWeight: 'bold'
                          }}
                        >
                          {material.type.toUpperCase()}
                        </Typography>
                      </Box>
                      <Typography variant="h6" gutterBottom>
                        {material.title}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" paragraph>
                        {material.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => handleStartLearning(material)}
                        >
                          Start Learning
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          href={material.url}
                          target="_blank"
                        >
                          Open Link
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Container>
    </Box>
  )
}

function getTypeColor(type) {
  const colors = {
    video: '#FF6B6B',
    blog: '#4ECDC4',
    pdf: '#45B7D1'
  }
  return colors[type] || '#667eea'
}

export default Dashboard
