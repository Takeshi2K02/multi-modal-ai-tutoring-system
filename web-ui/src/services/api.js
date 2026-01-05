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
