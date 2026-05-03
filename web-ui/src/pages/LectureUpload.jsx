import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { clsx } from 'clsx';
import { CloudUpload, FileText, CheckCircle2, Sparkles, AlertCircle, Trash2, Microscope, Download, X } from 'lucide-react';
import { API_BASE_URL } from '../services/api';

/**
 * LectureUpload Component
 * 
 * DESIGN RATIONALE:
 * 1. Premium Minimalism: Uses depth via mesh gradients and high-contrast typography.
 * 2. Interaction Feedback: Breathing pulse on the drop zone and animated Sparkle on action.
 * 3. Functional Glassmorphism: Backdrop-blur and subtle borders for a modern, focused feel.
 */
const LectureUpload = ({ onBack, onSuccess }) => {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [indexingProgress, setIndexingProgress] = useState(0);
    const [analysisMode, setAnalysisMode] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileSelect = (e) => {
        const selectedFiles = e.target.files ? Array.from(e.target.files) : [];
        addFiles(selectedFiles);
    };

    const addFiles = (selectedFiles) => {
        const newFiles = selectedFiles.map(f => ({
            file: f,
            id: Math.random().toString(36).substr(2, 9),
            status: 'pending', // pending, uploading, success, error
            msg: ''
        }));
        setFiles(prev => [...prev, ...newFiles]);
    };

    const removeFile = (id) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const allowedExtensions = ['.pdf', '.pptx', '.docx', '.txt'];
        const droppedFiles = Array.from(e.dataTransfer.files).filter(f => {
            const ext = '.' + f.name.split('.').pop().toLowerCase();
            return allowedExtensions.includes(ext);
        });
        addFiles(droppedFiles);
    };

    const processQueue = async () => {
        setUploading(true);
        setIndexingProgress(0);
        let successCount = 0;

        for (let i = 0; i < files.length; i++) {
            const item = files[i];
            if (item.status === 'success') {
                successCount++;
                continue;
            }

            updateStatus(item.id, 'uploading');
            try {
                const formData = new FormData();
                formData.append('file', item.file);

                if (analysisMode) {
                    setIsAnalyzing(true);
                    const response = await axios.post(`${API_BASE_URL}/api/analyze-anatomy`, formData, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    setAnalysisResult(response.data);
                    updateStatus(item.id, 'success', 'Analyzed successfully');
                } else {
                    // Phase 21: RAG Isolation - Use a stable collection ID for the batch
                    let batchCollectionId = localStorage.getItem('last_upload_collection');
                    if (!batchCollectionId || i === 0) {
                        batchCollectionId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
                        localStorage.setItem('last_upload_collection', batchCollectionId);
                    }

                    await axios.post(`${API_BASE_URL}/api/upload`, formData, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                        params: { collection_id: batchCollectionId }
                    });
                    updateStatus(item.id, 'success', 'Ingested successfully');
                }
                successCount++;
                setIndexingProgress((successCount / files.length) * 100);
            } catch (err) {
                console.error(err);
                updateStatus(item.id, 'error', err.response?.data?.detail || 'Process failed');
            } finally {
                if (analysisMode) setIsAnalyzing(false);
            }
        }
        setUploading(false);

        // Automated Navigation on Ingestion Success
        if (!analysisMode && successCount === files.length && files.length > 0) {
            const finalCollectionId = localStorage.getItem('last_upload_collection');
            setTimeout(() => {
                onSuccess(finalCollectionId);
            }, 1500);
        }
    };

    const handleDownloadSummary = () => {
        if (!analysisResult?.summary_file) return;
        window.open(`${API_BASE_URL}/api/download-summary/${analysisResult.summary_file}`, '_blank');
    };

    const updateStatus = (id, status, msg = '') => {
        setFiles(prev => prev.map(f => f.id === id ? { ...f, status, msg } : f));
    };

    return (
        <div className="h-full w-full bg-edu-bg-light dark:bg-edu-bg-dark font-sans selection:bg-primary/30 overflow-y-auto transition-colors">
            <div className="max-w-4xl mx-auto px-6 py-12 relative z-10">

                {/* Header Section */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="mb-16 text-center"
                >
                    <h1 className="text-5xl md:text-6xl font-light tracking-tight text-edu-text-light dark:text-white mb-6">
                        Lecture <br />
                        <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-400 to-primary animate-gradient-x shadow-sm">
                            Knowledge Ingestion
                        </span>
                    </h1>
                    <p className="text-zinc-500 dark:text-slate-400 text-lg md:text-xl font-light leading-relaxed max-w-lg mx-auto transition-colors">
                        {analysisMode ? "Analyze and summarize the structural anatomy of your learning content." : "Sythesize your course materials into the EduSynth agentic vector core."}
                    </p>

                    {/* Mode Toggle */}
                    <div className="mt-8 flex justify-center">
                        <div className="bg-zinc-100 dark:bg-zinc-800/50 p-1 rounded-2xl border border-edu-border-light dark:border-white/5 flex gap-1">
                            <button
                                onClick={() => setAnalysisMode(false)}
                                className={clsx(
                                    "px-6 py-2 rounded-xl text-sm font-medium transition-all duration-300",
                                    !analysisMode ? "bg-white dark:bg-zinc-700 text-primary shadow-sm" : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
                                )}
                            >
                                Ingestion Mode
                            </button>
                            <button
                                onClick={() => setAnalysisMode(true)}
                                className={clsx(
                                    "px-6 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2",
                                    analysisMode ? "bg-white dark:bg-zinc-700 text-primary shadow-sm" : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
                                )}
                            >
                                <Microscope size={14} />
                                Anatomy Analysis
                            </button>
                        </div>
                    </div>
                </motion.div>

                {/* Upload Zone: Glassmorphism Card with Breathing Pulse */}
                <motion.div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    animate={{
                        scale: isDragging ? 1.02 : 1,
                        boxShadow: isDragging
                            ? "0 0 50px -10px rgba(99, 102, 241, 0.4)"
                            : "0 0 20px -12px rgba(0, 0, 0, 0.1)",
                        borderColor: isDragging ? "#0077B6" : "rgba(144, 224, 239, 0.1)"
                    }}
                    className={clsx(
                        "relative bg-white/50 dark:bg-zinc-900/40 backdrop-blur-3xl rounded-[48px] border border-edu-border-light dark:border-white/5 p-12 text-center transition-all duration-500 group cursor-pointer overflow-hidden",
                        isDragging ? "bg-white dark:bg-zinc-900/60" : "hover:bg-white/80 dark:hover:bg-zinc-900/50"
                    )}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        type="file"
                        multiple
                        accept=".pdf,.pptx,.docx,.txt"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                    />

                    <div className="flex flex-col items-center gap-6">
                        <div className="w-20 h-20 rounded-full bg-zinc-100 dark:bg-zinc-950 border border-edu-border-light dark:border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-500 shadow-inner">
                            <CloudUpload size={32} strokeWidth={1.5} className={clsx("transition-colors duration-500", isDragging ? "text-primary" : "text-zinc-400 dark:text-zinc-500 group-hover:text-primary")} />
                        </div>
                        <div className="space-y-2">
                            <h3 className="text-2xl font-light tracking-tight text-edu-text-light dark:text-zinc-200 transition-colors">Drop course materials here</h3>
                            <p className="text-zinc-400 dark:text-zinc-600 text-[14px] font-medium uppercase tracking-[0.2em] transition-colors">Supported formats: PDF, PPTX, DOCX, TXT</p>
                        </div>
                    </div>

                    {/* Breathing Underglow Effect */}
                    <div className="absolute inset-0 rounded-[48px] border border-white/10 pointer-events-none opacity-20 group-hover:opacity-40 transition-opacity animate-pulse" />
                </motion.div>

                {/* File List Area */}
                <AnimatePresence>
                    {files.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className="mt-16 space-y-4"
                        >
                            <div className="flex items-center justify-between px-6 mb-6">
                                <span className="text-[11px] uppercase tracking-widest text-zinc-400 dark:text-zinc-500 font-bold transition-colors">Selection Queue</span>
                                <span className="text-[11px] uppercase tracking-widest text-zinc-400 dark:text-zinc-500 font-bold transition-colors">{files.length} Object(s)</span>
                            </div>

                            <div className="space-y-3">
                                {files.map(f => (
                                    <motion.div
                                        layout
                                        key={f.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="group p-5 rounded-[24px] border border-edu-border-light dark:border-white/[0.03] bg-white dark:bg-zinc-900/20 hover:bg-zinc-50 dark:hover:bg-zinc-900/40 transition-all flex items-center justify-between relative overflow-hidden shadow-sm"
                                    >
                                        <div className="flex items-center gap-6 relative z-10">
                                            <div className="w-10 h-10 rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-edu-border-light dark:border-white/5 flex items-center justify-center text-zinc-400 dark:text-zinc-500 transition-colors">
                                                {f.status === 'success' ? <CheckCircle2 size={18} className="text-secondary" /> :
                                                    f.status === 'error' ? <AlertCircle size={18} className="text-danger" /> :
                                                        <FileText size={18} />}
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[15px] font-light text-edu-text-light dark:text-zinc-200 truncate max-w-[200px] md:max-w-md transition-colors">{f.file.name}</span>
                                                <span className="text-[11px] text-zinc-400 dark:text-zinc-600 font-mono transition-colors">{(f.file.size / 1024 / 1024).toFixed(2)} MB • {f.status.toUpperCase()}</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-4 relative z-10">
                                            {f.status === 'pending' && !uploading && (
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); removeFile(f.id); }}
                                                    className="p-2 text-zinc-300 dark:text-zinc-700 hover:text-danger transition-colors"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            )}
                                            {f.status === 'uploading' && (
                                                <div className="w-4 h-4 border-2 border-zinc-200 dark:border-zinc-500 border-t-primary rounded-full animate-spin" />
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            {/* Action Button Section with Progress Bar */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="pt-12 text-center"
                            >
                                {uploading && !analysisMode && (
                                    <div className="max-w-md mx-auto mb-10 space-y-3">
                                        <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-zinc-500 font-bold">
                                            <span>Processing & Indexing</span>
                                            <span>{Math.round(indexingProgress)}%</span>
                                        </div>
                                        <div className="h-1 bg-zinc-100 dark:bg-zinc-800/50 rounded-full overflow-hidden border border-white/5">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${indexingProgress}%` }}
                                                className="h-full bg-gradient-to-r from-primary to-accent shadow-[0_0_15px_rgba(0,119,182,0.5)]"
                                            />
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={processQueue}
                                    disabled={uploading}
                                    className="inline-flex items-center gap-3 px-10 py-6 rounded-full bg-primary text-white font-bold text-lg hover:bg-primary/90 hover:scale-105 active:scale-95 transition-all duration-500 shadow-xl shadow-primary/20 group disabled:opacity-50"
                                >
                                    <AnimatePresence mode="wait">
                                        {uploading ? (
                                            <motion.div
                                                key="loader"
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                className="flex items-center gap-3"
                                            >
                                                <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                                                <span>{analysisMode ? "Analyzing..." : "Indexing..."}</span>
                                            </motion.div>
                                        ) : (
                                            <motion.div
                                                key="content"
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                className="flex items-center gap-3"
                                            >
                                                <span>{analysisMode ? "Analyze Content Anatomy" : "Begin Ingestion Flow"}</span>
                                                {analysisMode ? <Microscope size={20} className="text-white animate-pulse" /> : <Sparkles size={20} className="text-white animate-pulse" />}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </button>
                                <p className="mt-8 text-[10px] uppercase tracking-[0.4em] text-zinc-400 dark:text-zinc-700 flex items-center justify-center gap-2 transition-colors">
                                    <span className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800" />
                                    {uploading ? "Synthesizing Neural Patterns..." : (analysisMode ? "Structural Intelligence Active" : "Vector core Ready")}
                                    <span className="w-1 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800" />
                                </p>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Analysis Result Modal/Overlay */}
                <AnimatePresence>
                    {analysisResult && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, y: 20 }}
                                animate={{ scale: 1, y: 0 }}
                                exit={{ scale: 0.9, y: 20 }}
                                className="bg-white dark:bg-zinc-900 w-full max-w-3xl max-h-[80vh] rounded-[32px] border border-white/10 overflow-hidden flex flex-col shadow-2xl"
                            >
                                <div className="p-8 border-b border-edu-border-light dark:border-white/5 flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-800/20">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                            <Microscope size={24} />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-semibold dark:text-white">Content Anatomy Summary</h2>
                                            <p className="text-sm text-zinc-500 dark:text-zinc-400">{analysisResult.filename}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setAnalysisResult(null)}
                                        className="w-10 h-10 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 flex items-center justify-center transition-colors"
                                    >
                                        <X size={20} className="text-zinc-500" />
                                    </button>
                                </div>
                                <div className="flex-1 overflow-y-auto p-8 font-serif leading-relaxed text-lg text-edu-text-light dark:text-zinc-300 whitespace-pre-wrap">
                                    {analysisResult.summary_content}
                                </div>
                                <div className="p-8 border-t border-edu-border-light dark:border-white/5 bg-zinc-50/50 dark:bg-zinc-800/20 flex justify-end gap-4">
                                    <button
                                        onClick={handleDownloadSummary}
                                        className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                                    >
                                        <Download size={18} />
                                        Download .txt Summary
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Dev Note: Minimalist styling */}
                <div className="mt-24 pt-12 border-t border-edu-border-light dark:border-white/[0.03] text-[11px] text-zinc-400 dark:text-zinc-800 uppercase tracking-widest text-center leading-loose transition-colors">
                    Knowledge Objects are mapped to <code className="text-zinc-500 dark:text-zinc-700">local_data/</code> <br />
                    Agentic Reasoning mode: VECTOR_PROVIDER=local
                </div>
            </div>
        </div>
    );
};

export default LectureUpload;
