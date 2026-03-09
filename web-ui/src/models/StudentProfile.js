const mongoose = require('mongoose');

const StudentProfileSchema = new mongoose.Schema({
    student_id: { type: String, required: true, unique: true },
    preferred_modality: {
        visual: { type: Number, default: 0.33 },
        textual: { type: Number, default: 0.33 },
        interactive: { type: Number, default: 0.34 }
    },
    historical_mastery: {
        type: Map,
        of: Number,
        default: {}
    },
    engagement_baseline: { type: Number, default: 0.5 },
    strategy_blacklist: {
        type: Map,
        of: [String],
        default: {}
    },
    learning_history: [{
        timestamp: { type: Date, default: Date.now },
        action_taken: { type: String },
        user_feedback: { type: Number, enum: [1, -1] }
    }]
});

module.exports = mongoose.model('StudentProfile', StudentProfileSchema);
