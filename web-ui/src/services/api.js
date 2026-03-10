import axios from 'axios';

// Ensure this matches uvicorn port
export const API_BASE_URL = 'http://localhost:8000';

export const runSimulation = async (scenario, topicContext = null, synthesisId = null) => {
    try {
        const payload = { scenario };
        if (topicContext) {
            payload.topic_title = topicContext.title;
            payload.topic_content = topicContext.content;
        }
        if (synthesisId) {
            payload.synthesis_id = synthesisId;
        }
        const response = await axios.post(`${API_BASE_URL}/api/run_sim`, payload);
        return response.data;
    } catch (error) {
        console.error("API Connection Error:", error);
        throw error;
    }
};

export const decomposeGoal = async (goal) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/goal_decompose`, { goal });
        return response.data;
    } catch (error) {
        console.error("API Connection Error:", error);
        throw error;
    }
};


export const saveLearningPlan = async (planData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/learning_plan/save`, { plan_data: planData });
        return response.data;
    } catch (error) {
        console.error("API Connection Error:", error);
        throw error;
    }
};

export const createSession = async (planId, studentId) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/session/create`, { plan_id: planId, student_id: studentId });
        return response.data;
    } catch (error) {
        console.error("Create Session Error", error);
        throw error;
    }
};

export const getSession = async (sessionId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/session/${sessionId}`);
        return response.data;
    } catch (error) {
        console.error("Get Session Error", error);
        throw error;
    }
};

export const getStudentSessions = async (studentId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/sessions/student/${studentId}`);
        return response.data;
    } catch (error) {
        console.error("List Sessions Error", error);
        return { sessions: [] };
    }
};


export const fetcher = url => axios.get(url).then(res => res.data);

export const deleteSession = async (sessionId) => {
    try {
        const response = await axios.delete(`${API_BASE_URL}/api/sessions/${sessionId}`);
        return response.data;
    } catch (error) {
        console.error("Delete Session Error", error);
        throw error;
    }
};

export const savePerformance = async (performanceData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/performance/save`, performanceData);
        return response.data;
    } catch (error) {
        console.error("Save Performance Error", error);
        throw error;
    }
};

export const updateSessionProgress = async (sessionId, topicId) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/session/progress`, { session_id: sessionId, topic_id: topicId });
        return response.data;
    } catch (error) {
        console.error("Update Progress Error", error);
        throw error;
    }
};

export const evaluateChallenge = async (challengeData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/challenge/evaluate`, challengeData);
        return response.data;
    } catch (error) {
        console.error("Evaluate Challenge Error", error);
        throw error;
    }
};

export const getLessonContent = async (studentId, topicId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/lesson/content`, {
            params: { student_id: studentId, topic_id: topicId }
        });
        return response.data.content;
    } catch (error) {
        console.error("Get Lesson Content Error", error);
        return null;
    }
};

export const saveLessonContent = async (contentData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/lesson/save_content`, contentData);
        return response.data;
    } catch (error) {
        console.error("Save Lesson Content Error", error);
        throw error;
    }
};

export const syncStudentProgress = async (progressData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/lesson/sync_progress`, progressData);
        return response.data;
    } catch (error) {
        console.error("Sync Progress Error", error);
        throw error;
    }
};

export const handleUserFeedback = async (feedbackData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/user/feedback`, feedbackData);
        return response.data;
    } catch (error) {
        console.error("Feedback Error", error);
        throw error;
    }
};

export const getStudentProfile = async (studentId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/user/profile/${studentId}`);
        return response.data;
    } catch (error) {
        console.error("Get Profile Error", error);
        return null;
    }
};
export const acceptShadowIntervention = async (shadowData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/user/accept_shadow`, shadowData);
        return response.data;
    } catch (error) {
        console.error("Shadow Acceptance Error", error);
        throw error;
    }
};
