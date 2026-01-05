import axios from 'axios';

// Ensure this matches uvicorn port
export const API_BASE_URL = 'http://127.0.0.1:8000';

export const runSimulation = async (scenario) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/run_sim`, { scenario });
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

export const deleteSession = async (sessionId) => {
    try {
        const response = await axios.delete(`${API_BASE_URL}/api/sessions/${sessionId}`);
        return response.data;
    } catch (error) {
        console.error("Delete Session Error", error);
        throw error;
    }
};
