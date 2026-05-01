import React, { useState, useRef, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Webcam from 'react-webcam'
import html2canvas from 'html2canvas'
import {
  Container,
  Box,
  Paper,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  Divider
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
  Slideshow as SlideshowIcon,
  Language as LanguageIcon,
  School as SchoolIcon,
  Article as ArticleIcon
} from '@mui/icons-material'
import axios from 'axios'
import LearningSlides from '../components/LearningSlides'

function LearningSession() {
  const location = useLocation()
  const navigate = useNavigate()
  const webcamRef = useRef(null)
  
  const material = location.state?.material
  const [webcamEnabled, setWebcamEnabled] = useState(true)
  const [engagementData, setEngagementData] = useState(null)
  const [trackingInterval, setTrackingInterval] = useState(null)
  const [sessionStartTime] = useState(Date.now())
  const [viewMode, setViewMode] = useState('slides') // 'slides' or 'webpage'

  // ── Content Detection (NEW) ────────────────────────────────────────────────
  const contentAreaRef = useRef(null)
  const [contentData, setContentData] = useState(null)
  const [contentLoading, setContentLoading] = useState(false)

  useEffect(() => {
    if (!material) {
      navigate('/dashboard')
      return
    }

    // Start engagement tracking
    if (webcamEnabled) {
      const interval = setInterval(() => {
        captureAndSendFrame()
      }, 2000) // Every 2 seconds
      
      setTrackingInterval(interval)
    }

    return () => {
      if (trackingInterval) {
        clearInterval(trackingInterval)
      }
    }
  }, [webcamEnabled])

  // ── Content Detection interval (NEW) ────────────────────────────────────────
  useEffect(() => {
    if (!material) return

    // Detect content every 10 seconds
    const contentInterval = setInterval(() => {
      captureAndDetectContent()
    }, 10000)

    // Run immediately on mount
    captureAndDetectContent()

    return () => clearInterval(contentInterval)
  }, [viewMode])

  const captureAndSendFrame = async () => {
    if (!webcamRef.current) return

    try {
      const imageSrc = webcamRef.current.getScreenshot()
      
      if (!imageSrc) return

      // Send to backend for processing
      const response = await axios.post('/api/engagement/track', {
        frame_data: imageSrc,
        material_id: material.id
      })

      setEngagementData(response.data)
    } catch (error) {
      console.error('Error tracking engagement:', error)
    }
  }

  // ── Content Detection (NEW) ────────────────────────────────────────────────
  const captureAndDetectContent = async () => {
    if (!contentAreaRef.current) return

    try {
      setContentLoading(true)
      const canvas = await html2canvas(contentAreaRef.current, {
        useCORS: true,
        allowTaint: true,
        scale: 0.5, // reduce resolution for faster transfer
        logging: false,
      })
      const screenDataUrl = canvas.toDataURL('image/jpeg', 0.7)

      const response = await axios.post('/api/content/detect', {
        screen_data: screenDataUrl,
      })

      setContentData(response.data)
    } catch (error) {
      console.error('Error detecting content:', error)
    } finally {
      setContentLoading(false)
    }
  }

  const handleEndSession = () => {
    if (trackingInterval) {
      clearInterval(trackingInterval)
    }
    
    // Log session duration
    const duration = Math.floor((Date.now() - sessionStartTime) / 1000)
    
    navigate('/dashboard')
  }

  if (!material) {
    return null
  }

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleEndSession}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Learning: {material.title}
          </Typography>
          <IconButton
            color="inherit"
            onClick={() => setWebcamEnabled(!webcamEnabled)}
          >
            {webcamEnabled ? <VideocamIcon /> : <VideocamOffIcon />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Main Content Area */}
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 3 }} ref={contentAreaRef}>
              <Typography variant="h5" gutterBottom>
                {material.title}
              </Typography>
              <Chip
                label={material.type.toUpperCase()}
                color="primary"
                size="small"
                sx={{ mb: 2 }}
              />
              <Typography variant="body1" paragraph>
                {material.description}
              </Typography>
              {/* View Mode Toggle */}
              <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={(e, newMode) => newMode && setViewMode(newMode)}
                  aria-label="content view mode"
                  size="small"
                >
                  <ToggleButton value="slides" aria-label="slides view">
                    <SlideshowIcon sx={{ mr: 1 }} />
                    Learning Slides
                  </ToggleButton>
                  <ToggleButton value="webpage" aria-label="webpage view">
                    <LanguageIcon sx={{ mr: 1 }} />
                    Web Content
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <Box sx={{ mt: 3 }}>
                {viewMode === 'slides' ? (
                  <LearningSlides 
                    material={material} 
                    onClose={handleEndSession}
                  />
                ) : (
                  <>
                    {material.type === 'pdf' || material.url.includes('search') || material.url.includes('google.com') ? (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          This material cannot be displayed directly in the browser. 
                          Click "Open in New Tab" below to access it.
                        </Typography>
                      </Alert>
                    ) : null}
                    
                    <iframe
                      src={material.url}
                      width="100%"
                      height="600"
                      frameBorder="0"
                      title={material.title}
                      style={{ borderRadius: '8px' }}
                      onError={(e) => {
                        console.error('Iframe loading error:', e);
                      }}
                    />

                    <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                      <Button
                        variant="contained"
                        href={material.url}
                        target="_blank"
                        fullWidth
                      >
                        Open in New Tab
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={handleEndSession}
                        fullWidth
                      >
                        End Session
                      </Button>
                    </Box>
                  </>
                )}
              </Box>
            </Paper>
          </Grid>

          {/* Engagement Tracking Sidebar */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Engagement Tracking
              </Typography>
              
              {webcamEnabled ? (
                <Box>
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    width="100%"
                    style={{ borderRadius: '8px' }}
                  />
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                    📹 Camera active - Tracking your engagement
                  </Typography>
                </Box>
              ) : (
                <Alert severity="info">
                  Camera disabled. Enable to track engagement.
                </Alert>
              )}
            </Paper>

            {engagementData && webcamEnabled && (
              <Paper elevation={3} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Your Engagement
                </Typography>
                
                <Card variant="outlined" sx={{ mb: 1, bgcolor: getEngagementColor(engagementData.engagement_score) }}>
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      Engagement Score
                    </Typography>
                    <Typography variant="h4">
                      {Math.round(engagementData.engagement_score * 100)}%
                    </Typography>
                  </CardContent>
                </Card>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>Emotion:</strong> {getEmotionEmoji(engagementData.emotion)} {engagementData.emotion}
                  </Typography>
                  <Typography variant="body2">
                    <strong>State:</strong> {engagementData.engagement_state}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Gaze:</strong> {engagementData.gaze}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Posture:</strong> {engagementData.posture}
                  </Typography>
                </Box>

                {engagementData.context_match && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Content Topic Detected:
                    </Typography>
                    <Chip
                      label={engagementData.context_match}
                      size="small"
                      color="secondary"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                )}
              </Paper>
            )}

            {/* ── Content Detection (NEW) ───────────────────────────── */}
            <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Content Detection</Typography>
                {contentLoading && (
                  <CircularProgress size={16} sx={{ ml: 'auto' }} />
                )}
              </Box>

              <Divider sx={{ mb: 2 }} />

              {contentData ? (
                <Box>
                  {/* Subject */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      mb: 1.5,
                    }}
                  >
                    <SchoolIcon fontSize="small" color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Subject
                      </Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {contentData.subject}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {Math.round((contentData.subject_confidence || 0) * 100)}% confidence
                      </Typography>
                    </Box>
                  </Box>

                  {/* Content Type */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <ArticleIcon fontSize="small" color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Content Type
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.25 }}>
                        <Chip
                          label={contentData.content_type}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                        <Typography variant="caption" color="textSecondary">
                          {Math.round((contentData.content_type_confidence || 0) * 100)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  {contentLoading
                    ? 'Analysing content…'
                    : 'Waiting for content snapshot…'}
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}

function getEngagementColor(score) {
  if (score >= 0.7) return '#d4edda'
  if (score >= 0.4) return '#fff3cd'
  return '#f8d7da'
}

function getEmotionEmoji(emotion) {
  const emojis = {
    happy: '😊',
    focused: '🎯',
    neutral: '😐',
    confused: '😕',
    frustrated: '😤',
    bored: '😴',
    tired: '😫'
  }
  return emojis[emotion] || '😐'
}

export default LearningSession
