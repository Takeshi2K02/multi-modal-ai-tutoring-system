import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { login, register } from '../services/api';
import { GraduationCap, ArrowRight } from 'lucide-react';

const Auth = ({ onAuthSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                await login(username, password);
                onAuthSuccess();
            } else {
                await register(username, password);
                setIsLogin(true);
                setError('Account created! Please login.');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-[80vh]">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md p-8 bg-white/10 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl"
            >
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-primary to-cyan-400 flex items-center justify-center mb-4">
                        <GraduationCap className="text-white" size={24} />
                    </div>
                    <h2 className="text-2xl font-bold text-white">
                        {isLogin ? 'Welcome Back' : 'Join EduSynth'}
                    </h2>
                    <p className="text-zinc-400 text-sm mt-1">
                        {isLogin ? 'Login to continue your learning journey' : 'Start your personalized AI learning path'}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-zinc-400 mb-1.5 ml-1">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-black/20 border border-white/5 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                            placeholder="Enter username"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-zinc-400 mb-1.5 ml-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-black/20 border border-white/5 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && (
                        <p className={`text-sm ml-1 ${error.includes('created') ? 'text-green-400' : 'text-red-400'}`}>
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2"
                    >
                        {loading ? 'Processing...' : isLogin ? 'Login' : 'Register'}
                        {!loading && <ArrowRight size={18} />}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <button
                        onClick={() => setIsLogin(!isLogin)}
                        className="text-zinc-400 hover:text-white text-sm transition-colors"
                    >
                        {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
                    </button>
                </div>
            </motion.div>
        </div>
    );
};

export default Auth;
