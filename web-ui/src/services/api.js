import axios from 'axios';

// Ensure this matches uvicorn port
const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const runSimulation = async (scenario) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/run_sim`, { scenario });
        return response.data;
    } catch (error) {
        console.error("API Connection Error:", error);
        throw error;
    }
};
