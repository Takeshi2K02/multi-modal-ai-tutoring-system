import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { API_BASE_URL } from '../services/api';

const LectureUpload = ({ onBack }) => {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);

    const handleFileSelect = (e) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files).map(f => ({
                file: f,
                id: Math.random().toString(36).substr(2, 9),
                status: 'pending', // pending, uploading, success, error
                msg: ''
            }));
            setFiles([...files, ...newFiles]);
        }
    };

    const processQueue = async () => {
        setUploading(true);

        // Process sequentially for simplicity (or parallel)
        for (let i = 0; i < files.length; i++) {
            const item = files[i];
            if (item.status === 'success') continue; // Skip done

            // Update status to uploading
            updateStatus(item.id, 'uploading');

            try {
                const formData = new FormData();
                formData.append('file', item.file);

                await axios.post(`${API_BASE_URL}/api/upload`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                updateStatus(item.id, 'success', 'Ingested successfully');
            } catch (err) {
                console.error(err);
                updateStatus(item.id, 'error', err.response?.data?.detail || 'Upload failed');
            }
        }
        setUploading(false);
    };

    const updateStatus = (id, status, msg = '') => {
        setFiles(prev => prev.map(f => f.id === id ? { ...f, status, msg } : f));
    };

    return (
        <div className="flex h-full w-full bg-slate-50 flex-col">
            {/* Header */}
            <div className="bg-white border-b border-slate-200 px-8 py-6 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Lecture Ingestion</h1>
                    <p className="text-slate-500 text-sm">Upload PDFs to the local vector store.</p>
                </div>
                <button
                    onClick={onBack}
                    className="px-4 py-2 rounded-lg text-slate-500 hover:bg-slate-100 font-medium text-sm transition-colors"
                >
                    ← Back to Visualizer
                </button>
            </div>

            {/* Content */}
            <div className="p-8 max-w-4xl mx-auto w-full">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
                    <div className="mb-8">
                        <div className="mx-auto w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mb-4">
                            <span className="text-2xl">📄</span>
                        </div>
                        <h3 className="text-lg font-bold text-slate-800">Select Lecture PDFs</h3>
                        <p className="text-sm text-slate-500 mb-6">Supported Format: .pdf (University Lectures)</p>

                        <input
                            type="file"
                            multiple
                            accept=".pdf"
                            onChange={handleFileSelect}
                            className="hidden"
                            id="file-upload"
                        />
                        <label
                            htmlFor="file-upload"
                            className="cursor-pointer px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg transition-transform active:scale-95"
                        >
                            Browse Files
                        </label>
                    </div>

                    {files.length > 0 && (
                        <div className="text-left space-y-3 max-h-[300px] overflow-y-auto mb-6">
                            {files.map(f => (
                                <motion.div
                                    layout
                                    key={f.id}
                                    className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50"
                                >
                                    <div className="flex items-center gap-3 overflow-hidden">
                                        <span className="text-xl">
                                            {f.status === 'success' ? '✅' : f.status === 'error' ? '❌' : '📄'}
                                        </span>
                                        <div className="truncate">
                                            <div className="text-sm font-medium text-slate-700 truncate">{f.file.name}</div>
                                            <div className="text-xs text-slate-400">
                                                {(f.file.size / 1024 / 1024).toFixed(2)} MB • {f.status.toUpperCase()}
                                            </div>
                                        </div>
                                    </div>
                                    {f.status === 'error' && (
                                        <span className="text-xs text-red-500">{f.msg}</span>
                                    )}
                                </motion.div>
                            ))}
                        </div>
                    )}

                    {files.length > 0 && (
                        <button
                            onClick={processQueue}
                            disabled={uploading}
                            className={`w-full py-3 rounded-lg font-bold text-white transition-all ${uploading ? "bg-slate-400 cursor-not-allowed" : "bg-emerald-500 hover:bg-emerald-600 shadow-md shadow-emerald-200"
                                }`}
                        >
                            {uploading ? "Processing Pieline..." : "Start Ingestion Flow"}
                        </button>
                    )}
                </div>

                <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800">
                    <strong>Development Mode only:</strong> Files are stored in <code>local_data/</code>.
                    Ensure <code>VECTOR_PROVIDER=local</code> is set in your environment to query this data in Decomposition/ToT.
                </div>
            </div>
        </div>
    );
};

export default LectureUpload;
