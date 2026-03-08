import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { motion } from 'framer-motion';

const ThemeToggle = () => {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors duration-300 flex items-center justify-center relative overflow-hidden group"
            aria-label="Toggle Theme"
        >
            <motion.div
                animate={{
                    rotate: theme === 'dark' ? 0 : 180,
                    scale: theme === 'dark' ? 1 : 0,
                    opacity: theme === 'dark' ? 1 : 0,
                }}
                transition={{ type: 'spring', damping: 12 }}
                className="absolute"
            >
                <Moon size={18} className="text-primary" />
            </motion.div>
            <motion.div
                animate={{
                    rotate: theme === 'light' ? 0 : -180,
                    scale: theme === 'light' ? 1 : 0,
                    opacity: theme === 'light' ? 1 : 0,
                }}
                transition={{ type: 'spring', damping: 12 }}
            >
                <Sun size={18} className="text-accent" />
            </motion.div>
        </button>
    );
};

export default ThemeToggle;
