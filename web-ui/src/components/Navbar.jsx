import React, { useState } from 'react';
import { BrainCircuit, Menu, X, LayoutDashboard, BookOpen, Layers, GraduationCap, Upload, Activity, Database } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { logout } from '../services/api';

const Navbar = ({ onViewChange, currentView }) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const navItems = [
        { id: 'decomposition', label: 'New Goal', icon: <Layers size={16} strokeWidth={1.5} /> },
        { id: 'upload', label: 'Upload', icon: <Upload size={16} strokeWidth={1.5} /> },
        { id: 'dashboard', label: 'My Learning', icon: <LayoutDashboard size={16} strokeWidth={1.5} /> },
        { id: 'agent', label: 'Agent Debugger', icon: <BrainCircuit size={16} strokeWidth={1.5} /> },
        { id: 'monitor', label: 'Live Monitor', icon: <Activity size={16} strokeWidth={1.5} /> },
        { id: 'data', label: 'Data', icon: <Database size={16} strokeWidth={1.5} /> },
    ];

    return (
        <nav className="fixed top-6 left-0 right-0 z-[100] flex justify-center px-4 pointer-events-none">
            <div className="flex items-center gap-2 bg-white/80 dark:bg-[#121212]/70 backdrop-blur-xl border border-edu-border-light dark:border-[#6366F1]/20 px-2 py-1.5 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.4)] pointer-events-auto transition-all duration-500 hover:border-edu-border-light/50 dark:hover:border-[#6366F1]/40">

                {/* Logo Section */}
                <div
                    className="flex items-center gap-2 px-4 py-2 cursor-pointer group"
                    onClick={() => onViewChange('decomposition')}
                >
                    <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#0077B6] to-[#48CAE4] flex items-center justify-center shadow-lg shadow-[#0077B6]/10 group-hover:scale-105 transition-transform duration-300">
                        <GraduationCap className="text-white" size={16} />
                    </div>
                    <span className="font-medium text-sm tracking-tight text-edu-text-light dark:text-white/90">
                        EduSynth
                    </span>
                </div>

                <div className="h-4 w-[1px] bg-edu-border-light dark:bg-white/10 mx-1" />

                {/* Desktop Menu */}
                <div className="hidden md:flex items-center gap-1">
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={`px-4 py-2 rounded-full text-[13px] font-medium transition-all duration-300 flex items-center gap-2 group relative overflow-hidden ${currentView === item.id
                                ? 'text-primary dark:text-white'
                                : 'text-zinc-500 dark:text-zinc-400 hover:text-primary dark:hover:text-zinc-200'
                                }`}
                        >
                            {/* Active State Glow */}
                            {currentView === item.id && (
                                <motion.div
                                    layoutId="nav-active"
                                    className="absolute inset-0 bg-primary/10 dark:bg-white/5 border border-primary/20 dark:border-white/10 rounded-full shadow-[inset_0_1px_12px_rgba(255,255,255,0.05)]"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                />
                            )}

                            <span className={`relative z-10 transition-transform duration-300 group-hover:-translate-y-[1px] flex items-center gap-2 ${currentView === item.id ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'
                                }`}>
                                {item.icon}
                                <span>{item.label}</span>
                            </span>
                        </button>
                    ))}
                </div>

                <div className="h-4 w-[1px] bg-edu-border-light dark:bg-white/10 mx-1" />

                <div className="px-2">
                    <ThemeToggle />
                </div>

                <div className="h-4 w-[1px] bg-edu-border-light dark:bg-white/10 mx-1" />

                {localStorage.getItem('token') ? (
                    <button
                        onClick={() => {
                            logout();
                            window.location.reload();
                        }}
                        className="px-4 py-2 text-[13px] font-medium text-red-500 hover:text-red-400 transition-colors"
                    >
                        Logout
                    </button>
                ) : (
                    <button
                        onClick={() => onViewChange('login')}
                        className="px-4 py-2 text-[13px] font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                        Login
                    </button>
                )}

                {/* Mobile Menu Toggle (Simplified for context) */}
                <div className="md:hidden flex items-center px-2">
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="text-zinc-400 hover:text-white p-2 transition-colors"
                    >
                        {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu Dropdown - Refined for floating style */}
            <AnimatePresence>
                {isMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -20, scale: 0.95 }}
                        className="absolute top-16 left-4 right-4 bg-white/95 dark:bg-[#121212]/90 backdrop-blur-xl border border-edu-border-light dark:border-[#6366F1]/20 rounded-3xl p-3 shadow-2xl md:hidden pointer-events-auto"
                    >
                        <div className="grid grid-cols-1 gap-1">
                            {navItems.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => {
                                        onViewChange(item.id);
                                        setIsMenuOpen(false);
                                    }}
                                    className={`w-full text-left px-4 py-3 rounded-2xl text-[15px] font-medium flex items-center gap-4 transition-all ${currentView === item.id
                                        ? 'bg-white/10 text-white border border-white/10 shadow-inner'
                                        : 'text-zinc-400 hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    <span className={currentView === item.id ? 'text-primary' : ''}>{item.icon}</span>
                                    {item.label}
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
};

// Internal motion dependency mock if not wrapped, but App.jsx uses framer-motion
import { motion, AnimatePresence } from 'framer-motion';

export default Navbar;
