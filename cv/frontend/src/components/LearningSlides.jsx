import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  Chip,
  Stack
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Home as HomeIcon
} from '@mui/icons-material'

// Sample learning content slides
const sampleSlides = [
  {
    id: 1,
    title: "Introduction to Machine Learning",
    subtitle: "What is Machine Learning?",
    content: [
      "Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
      "Key Concepts:",
      "• Supervised Learning: Learning from labeled data",
      "• Unsupervised Learning: Finding patterns in unlabeled data",
      "• Reinforcement Learning: Learning through trial and error",
      "Machine learning algorithms use statistical techniques to give computers the ability to progressively improve their performance on specific tasks."
    ],
    color: "#e3f2fd"
  },
  {
    id: 2,
    title: "Types of Machine Learning",
    subtitle: "Understanding Different Approaches",
    content: [
      "1. Supervised Learning",
      "   - Uses labeled training data",
      "   - Examples: Classification, Regression",
      "   - Applications: Email spam detection, Price prediction",
      "",
      "2. Unsupervised Learning",
      "   - Works with unlabeled data",
      "   - Examples: Clustering, Dimensionality reduction",
      "   - Applications: Customer segmentation, Anomaly detection",
      "",
      "3. Reinforcement Learning",
      "   - Learns through rewards and penalties",
      "   - Examples: Q-learning, Deep Q-Networks",
      "   - Applications: Game AI, Robotics"
    ],
    color: "#f3e5f5"
  },
  {
    id: 3,
    title: "Neural Networks Basics",
    subtitle: "Building Blocks of Deep Learning",
    content: [
      "Neural networks are computing systems inspired by biological neural networks in animal brains.",
      "",
      "Key Components:",
      "• Neurons (Nodes): Basic processing units",
      "• Layers: Input layer, Hidden layers, Output layer",
      "• Weights: Connection strengths between neurons",
      "• Activation Functions: Introduce non-linearity (ReLU, Sigmoid, Tanh)",
      "",
      "Neural networks excel at:",
      "- Image recognition",
      "- Natural language processing",
      "- Speech recognition",
      "- Pattern detection"
    ],
    color: "#e8f5e9"
  },
  {
    id: 4,
    title: "Python for Data Science",
    subtitle: "Essential Libraries and Tools",
    content: [
      "Popular Python Libraries:",
      "",
      "📊 NumPy: Numerical computing with arrays",
      "📈 Pandas: Data manipulation and analysis",
      "📉 Matplotlib: Data visualization",
      "🎨 Seaborn: Statistical data visualization",
      "🤖 Scikit-learn: Machine learning algorithms",
      "🧠 TensorFlow/PyTorch: Deep learning frameworks",
      "",
      "Python's simplicity and extensive ecosystem make it the preferred language for data science and machine learning projects."
    ],
    color: "#fff3e0"
  },
  {
    id: 5,
    title: "Model Training Process",
    subtitle: "Steps to Build ML Models",
    content: [
      "1. Data Collection",
      "   Gather relevant and quality data",
      "",
      "2. Data Preprocessing",
      "   Clean, normalize, and prepare data",
      "",
      "3. Feature Engineering",
      "   Select and create meaningful features",
      "",
      "4. Model Selection",
      "   Choose appropriate algorithm",
      "",
      "5. Training",
      "   Fit model to training data",
      "",
      "6. Evaluation",
      "   Test model performance",
      "",
      "7. Hyperparameter Tuning",
      "   Optimize model parameters",
      "",
      "8. Deployment",
      "   Put model into production"
    ],
    color: "#fce4ec"
  },
  {
    id: 6,
    title: "Overfitting vs Underfitting",
    subtitle: "Common Model Problems",
    content: [
      "Overfitting:",
      "• Model learns training data too well",
      "• Poor generalization to new data",
      "• High training accuracy, low test accuracy",
      "• Solutions: Regularization, dropout, more data",
      "",
      "Underfitting:",
      "• Model is too simple to capture patterns",
      "• Poor performance on both training and test data",
      "• Low accuracy overall",
      "• Solutions: More complex model, better features",
      "",
      "Goal: Find the right balance between bias and variance for optimal generalization."
    ],
    color: "#e0f2f1"
  },
  {
    id: 7,
    title: "Evaluation Metrics",
    subtitle: "Measuring Model Performance",
    content: [
      "Classification Metrics:",
      "• Accuracy: Overall correctness",
      "• Precision: True positives / (True + False positives)",
      "• Recall: True positives / (True positives + False negatives)",
      "• F1-Score: Harmonic mean of precision and recall",
      "• Confusion Matrix: Detailed error analysis",
      "",
      "Regression Metrics:",
      "• Mean Squared Error (MSE)",
      "• Root Mean Squared Error (RMSE)",
      "• Mean Absolute Error (MAE)",
      "• R² Score: Explained variance",
      "",
      "Choose metrics based on your specific problem and business objectives."
    ],
    color: "#f1f8e9"
  },
  {
    id: 8,
    title: "Congratulations! 🎉",
    subtitle: "You've Completed the Introduction",
    content: [
      "You've learned about:",
      "",
      "✓ Machine Learning fundamentals",
      "✓ Types of ML approaches",
      "✓ Neural networks basics",
      "✓ Python tools for data science",
      "✓ Model training process",
      "✓ Common pitfalls and solutions",
      "✓ Performance evaluation metrics",
      "",
      "Next Steps:",
      "• Practice with real datasets",
      "• Build your own projects",
      "• Explore advanced topics",
      "• Join ML communities",
      "",
      "Keep learning and experimenting! 🚀"
    ],
    color: "#ede7f6"
  }
]

function LearningSlides({ material, onClose }) {
  const [currentSlide, setCurrentSlide] = useState(0)
  
  const slides = material?.slides || sampleSlides
  const totalSlides = slides.length
  const progress = ((currentSlide + 1) / totalSlides) * 100

  const handleNext = () => {
    if (currentSlide < totalSlides - 1) {
      setCurrentSlide(currentSlide + 1)
    }
  }

  const handlePrevious = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1)
    }
  }

  const handleSlideSelect = (index) => {
    setCurrentSlide(index)
  }

  const currentSlideData = slides[currentSlide]

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Progress Bar */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="caption" color="textSecondary">
            Slide {currentSlide + 1} of {totalSlides}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {Math.round(progress)}% Complete
          </Typography>
        </Box>
        <LinearProgress variant="determinate" value={progress} />
      </Box>

      {/* Main Slide Content */}
      <Paper
        elevation={2}
        sx={{
          flex: 1,
          p: 4,
          mb: 2,
          backgroundColor: currentSlideData.color || '#ffffff',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '500px',
          position: 'relative',
          overflow: 'auto'
        }}
      >
        <Box>
          <Chip 
            label={`Slide ${currentSlide + 1}`} 
            size="small" 
            color="primary" 
            sx={{ mb: 2 }}
          />
          
          <Typography variant="h4" gutterBottom fontWeight="bold">
            {currentSlideData.title}
          </Typography>
          
          {currentSlideData.subtitle && (
            <Typography variant="h6" color="textSecondary" gutterBottom sx={{ mb: 3 }}>
              {currentSlideData.subtitle}
            </Typography>
          )}

          <Box sx={{ mt: 2 }}>
            {currentSlideData.content.map((line, index) => (
              <Typography
                key={index}
                variant="body1"
                sx={{
                  mb: line === "" ? 1 : 0.5,
                  fontWeight: line.includes('Key') || line.includes(':') && !line.includes('•') ? 'bold' : 'normal',
                  fontSize: line.startsWith('•') || line.startsWith('✓') || line.startsWith('📊') || line.startsWith('📈') || line.startsWith('📉') || line.startsWith('🎨') || line.startsWith('🤖') || line.startsWith('🧠') ? '1.1rem' : '1rem',
                  lineHeight: 1.8,
                  pl: line.startsWith('   ') ? 4 : 0
                }}
              >
                {line || '\u00A0'}
              </Typography>
            ))}
          </Box>
        </Box>

        {/* Slide Number Indicator at Bottom Right */}
        <Box sx={{ position: 'absolute', bottom: 16, right: 16 }}>
          <Typography variant="caption" color="textSecondary" sx={{ opacity: 0.5 }}>
            {currentSlide + 1} / {totalSlides}
          </Typography>
        </Box>
      </Paper>

      {/* Navigation Controls */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handlePrevious}
          disabled={currentSlide === 0}
          sx={{ flex: 1 }}
        >
          Previous
        </Button>
        
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', justifyContent: 'center' }}>
          {slides.map((_, index) => (
            <Box
              key={index}
              onClick={() => handleSlideSelect(index)}
              sx={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: index === currentSlide ? 'primary.main' : 'grey.300',
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': {
                  backgroundColor: index === currentSlide ? 'primary.dark' : 'grey.400',
                  transform: 'scale(1.2)'
                }
              }}
            />
          ))}
        </Box>

        <Button
          variant="contained"
          endIcon={currentSlide === totalSlides - 1 ? <HomeIcon /> : <ArrowForwardIcon />}
          onClick={currentSlide === totalSlides - 1 ? onClose : handleNext}
          sx={{ flex: 1 }}
        >
          {currentSlide === totalSlides - 1 ? 'Finish' : 'Next'}
        </Button>
      </Box>

      {/* Slide Thumbnails */}
      <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1 }}>
        {slides.map((slide, index) => (
          <Card
            key={slide.id}
            onClick={() => handleSlideSelect(index)}
            sx={{
              minWidth: 120,
              cursor: 'pointer',
              border: index === currentSlide ? 2 : 0,
              borderColor: 'primary.main',
              transition: 'all 0.3s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 3
              }
            }}
          >
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography variant="caption" fontWeight="bold" noWrap>
                {index + 1}. {slide.title}
              </Typography>
              <Typography variant="caption" color="textSecondary" noWrap sx={{ display: 'block' }}>
                {slide.subtitle}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  )
}

export default LearningSlides
