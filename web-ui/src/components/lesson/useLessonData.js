import { useState, useEffect, useMemo, useRef } from 'react';
import useSWR from 'swr';
import toast from 'react-hot-toast';
import { useAuth } from "../../AuthContext";
import {
    savePerformance,
    updateSessionProgress,
    saveLessonContent,
    getLessonContent,
    syncStudentProgress,
    handleUserFeedback,
    acceptShadowIntervention,
    runSimulation,
    manualPrefetch,
    fetcher,
    API_BASE_URL,
    getSynthesis
} from '../../services/api';

export const useLessonData = (sessionId, topic, onBack, onReady, sio, onPrefetchStarted) => {
    const { userId } = useAuth();
    const [loading, setLoading] = useState(true);
    const [content, setContent] = useState(null);
    const [isThinking, setIsThinking] = useState(true);
    const [selectedOption, setSelectedOption] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isChallengeComplete, setIsChallengeComplete] = useState(false);
    const [shadowReady, setShadowReady] = useState(null);
    const [isCompleting, setIsCompleting] = useState(false);
    const [response, setResponse] = useState('');
    const [error, setError] = useState(null);
    const [isVisualReady, setIsVisualReady] = useState(false);
    const [interactionId, setInteractionId] = useState(null);
    const [strategyLabel, setStrategyLabel] = useState(null);
    const [feedbackSent, setFeedbackSent] = useState(false);
    const [score, setScore] = useState(0);
    const [signalData, setSignalData] = useState({ nodes: [], edges: [] });
    const [currentModality, setCurrentModality] = useState('TEXTUAL');
    const pipelineLockRef = useRef(null);
    const [ragSources, setRagSources] = useState([]);
    const [profileToast, setProfileToast] = useState(null);
    const [progressPhases, setProgressPhases] = useState([]);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [isDeliveryComplete, setIsDeliveryComplete] = useState(false);
    const [isFromCache, setIsFromCache] = useState(false);

    const { data: sessionData } = useSWR(
        sessionId ? `${API_BASE_URL}/api/session/${sessionId}` : null,
        fetcher
    );

    const hasDesignChallenge = useMemo(() => {
        const text = typeof content?.content === 'string' ? content.content : '';
        return text.includes('Design Challenge') || text.includes('### Challenge');
    }, [content]);

    const sanitizedContent = useMemo(() => {
        if (typeof content?.content !== 'string') return '';
        let text = content.content;
        text = text.replace(/\[MERMAID_START\][\s\S]*?\[MERMAID_END\]/mg, '');
        text = text.replace(/\[IMAGE_FOR_ALEX\]/g, '\n\n> [!TIP]\n> **Visual Context Generated**: An specialized architectural snapshot has been generated for your learning profile.\n\n');
        return text.trim();
    }, [content]);

    const mermaidData = useMemo(() => {
        if (!content?.content || !content.content.includes('[MERMAID_START]')) return null;
        const match = content.content.match(/\[MERMAID_START\]([\s\S]*?)\[MERMAID_END\]/);
        return match?.[1]?.trim() || null;
    }, [content]);

    const isContentViewable = useMemo(() => {
        return !!(sanitizedContent || mermaidData || content?.type === 'quiz' || hasDesignChallenge || signalData?.nodes?.length > 0);
    }, [sanitizedContent, mermaidData, content, hasDesignChallenge, signalData?.nodes]);

    const isReadyToComplete = useMemo(() => {
        if (!isContentViewable) return false;
        if (mermaidData && !isVisualReady) return false;
        if (content?.type === 'quiz') return isSubmitted;
        if (hasDesignChallenge) return isChallengeComplete;
        return !!feedbackSent;
    }, [content, isSubmitted, hasDesignChallenge, isChallengeComplete, isContentViewable, mermaidData, isVisualReady, feedbackSent]);

    // Timer for loading feedback
    useEffect(() => {
        let interval;
        if ((isThinking || loading) && !isDeliveryComplete) {
            interval = setInterval(() => {
                setElapsedSeconds(prev => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isThinking, loading, isDeliveryComplete]);

    useEffect(() => {
        const hasVisuals = (signalData?.nodes?.length > 0) || !!mermaidData;
        if (hasVisuals && !isVisualReady) {
            const timer = setTimeout(() => setIsVisualReady(true), 800);
            return () => clearTimeout(timer);
        }
    }, [signalData?.nodes, mermaidData, isVisualReady]);

    // 1. Initial Socket Setup & Persistence (Join Room)
    useEffect(() => {
        if (!sio || !userId) return;

        const handleConnect = () => {
            if (userId) sio.emit("join_room", { student_id: userId });
        };

        const handleTotFinal = (data) => {
            setContent({
                content: data.full_text || data.final_content || "Content updated.",
                type: data.current_modality || "explanation"
            });
            if (data.interaction_id) setInteractionId(data.interaction_id);
            if (data.strategy) setStrategyLabel(data.strategy);
            setShadowReady(null);
            setIsThinking(false);
            setLoading(false);
        };

        const handleShadowReady = (data) => {
            console.error("[SHADOW] shadow_ready received:", data);
            setShadowReady(data);
            if (data.interaction_id) setInteractionId(data.interaction_id);
        };

        const handleSynthesisComplete = (data) => {
            const finalContent = data.full_text || data.final_content;
            if (finalContent) {
                setContent({
                    content: finalContent,
                    type: data.current_modality || "explanation"
                });
            }
            if (data.interaction_id) setInteractionId(data.interaction_id);
            setIsThinking(false);
            setLoading(false);
        };

        const handleProfileUpdated = (data) => {
            setProfileToast(data);
            setTimeout(() => setProfileToast(null), 5000);
        };

        const handleProgress = (data) => {
            if (data.phase === 'delivery_complete') {
                setIsDeliveryComplete(true);
                if (data.elapsed_ms) setElapsedSeconds(Math.floor(data.elapsed_ms / 1000));
            }
            setProgressPhases(prev => {
                if (prev.find(p => p.phase === data.phase)) return prev;
                return [...prev, data];
            });
        };

        sio.on("connect", handleConnect);
        sio.on('tot_final', handleTotFinal);
        
        sio.on('shadow_ready', handleShadowReady);
        
        sio.on('synthesis_complete', handleSynthesisComplete);
        sio.on('profile_updated', handleProfileUpdated);
        sio.on('progress', handleProgress);

        if (sio.connected) handleConnect();

        return () => {
            sio.off("connect", handleConnect);
            sio.off('tot_final', handleTotFinal);
            sio.off('shadow_ready', handleShadowReady);
            sio.off('synthesis_complete', handleSynthesisComplete);
            sio.off('profile_updated', handleProfileUpdated);
            sio.off('progress', handleProgress);
        };
    }, [sio, userId]);

    // 2. Topic-Specific Initialization Logic
    useEffect(() => {
        const initializeLesson = async (signal) => {
            if (!topic) return;
            
            const topicKey = topic.id || topic.title;
            if (pipelineLockRef.current === topicKey) return;
            pipelineLockRef.current = topicKey;

            setLoading(true);
            setIsThinking(true);
            setIsVisualReady(false);
            setSelectedOption(null);
            setIsSubmitted(false);
            setIsChallengeComplete(false);
            setShadowReady(null);
            setIsDeliveryComplete(false);
            setElapsedSeconds(0);
            
            try {
                const topicId = topic.id || topic.title;

                // PART 2: Persistent Synthesis Check (MongoDB)
                const saved = await getSynthesis(userId, topicId, sessionId);
                
                if (saved && (saved.final_content || saved.full_text)) {
                    // Step 5: Data Integrity Check
                    if (saved.session_id && saved.session_id !== sessionId) {
                        if (import.meta.env.DEV) console.error("[INTEGRITY] Stale session data detected — ignoring cache for synthesis");
                        // fall through to simulation
                    } else {
                        if (import.meta.env.DEV) console.log(">>> [LessonView] Serving persistent synthesis from MongoDB");
                        
                        const finalContent = saved.full_text || saved.final_content;
                        const modality = saved.current_modality || (finalContent?.includes('[MERMAID_START]') ? 'VISUAL' : 'TEXTUAL');
                        
                        setContent({
                            type: modality === 'VISUAL' ? 'visual_explanation' : 'explanation',
                            content: finalContent
                        });
                        setInteractionId(saved.interaction_id || saved.synthesis_id);
                        setStrategyLabel(saved.strategy);
                        setRagSources(saved.rag_sources || []);
                        setCurrentModality(modality);
                        setIsFromCache(true);
                        
                        setIsThinking(false);
                        setLoading(false);
                        onReady?.();
                        return;
                    }
                }

                // Fallback to legacy local content if MongoDB is empty
                const existing = await getLessonContent(userId, topicId, sessionId);
                if (signal.aborted) return;
                if (existing && (existing.content || existing.directive)) {
                    // Step 5: Data Integrity Check for legacy content
                    if (existing.session_id && existing.session_id !== sessionId) {
                        if (import.meta.env.DEV) console.error("[INTEGRITY] Stale session data detected — ignoring cache for content");
                        // fall through to simulation
                    } else {
                        setContent(existing.directive || existing.content);
                        setIsFromCache(true);
                        setIsThinking(false);
                        if (existing.user_response) setResponse(existing.user_response);
                        if (existing.ai_evaluation_score !== undefined) {
                            setScore(existing.ai_evaluation_score);
                            if (existing.ai_evaluation_score >= 0.7) setIsChallengeComplete(true);
                        }
                        setLoading(false);
                        onReady?.();
                        return;
                    }
                }

                if (!sessionId) {
                    setError('No active session found.');
                    setIsThinking(false);
                    return;
                }

                // If no saved synthesis, run simulation
                const scenario = `Teach me about ${topic.title}`;
                const result = await runSimulation(scenario, topic, null, null, sessionId);

                if (result.error) {
                    setError(result.message || result.error);
                    setIsThinking(false);
                    return;
                }

                if (result.nodes) setSignalData({ nodes: result.nodes, edges: result.edges || [] });
                if (signal.aborted) return;

                if (result.meta?.strategy === 'ERROR' || result.meta?.strategy === 'TIMED_OUT') {
                    setError(result.meta?.body_text || "Re-calibrating...");
                    setIsThinking(false);
                    return;
                }

                const bestNodeId = result.meta?.best_path_ids?.[result.meta.best_path_ids.length - 1];
                const bestNode = result.nodes?.find(n => n.id === bestNodeId);
                const finalContent = result.meta?.content?.full_text || result.meta?.body_text || result.meta?.final_response || result.full_text;

                const directive = bestNode?.data?.directive || {
                    type: result.meta?.current_modality === 'VISUAL' ? "visual_explanation" : "explanation",
                    content: finalContent || "Complete."
                };

                if (directive.content) setContent(directive);
                setInteractionId(result.meta?.interaction_id);
                setIsFromCache(!!result.meta?.from_cache);
                setStrategyLabel(result.meta?.selected_strategy_label || result.meta?.strategy_label);
                setRagSources(result.meta?.rag_sources || []);
                setCurrentModality(result.meta?.current_modality || (directive?.content?.includes('graph TD') ? 'VISUAL' : 'TEXTUAL'));

                setTimeout(() => {
                    if (signal.aborted) return;
                    setIsThinking(false);
                    onReady?.();
                }, 1500);

            } catch (err) {
                if (err.name === 'AbortError') return;
                setError(`Failed to initialize: ${err.message}`);
            } finally {
                if (!signal.aborted) setLoading(false);
            }
        };

        const controller = new AbortController();
        initializeLesson(controller.signal);

        // Bug 2: Lesson Lifecycle Tracking
        if (sio && userId && topic) {
            const topicId = topic.id || topic.title;
            sio.emit("lesson_entered", { student_id: userId, topic_id: topicId });
        }

        return () => {
            controller.abort();
            if (sio && userId) {
                sio.emit("lesson_exited", { student_id: userId });
            }
        };
    }, [topic.id || topic.title, userId, sio]);

    const handleAcceptShadow = async () => {
        if (!shadowReady || !interactionId) return;
        try {
            if (sio && userId) {
                sio.emit("intervention_resolved", { student_id: userId });
            }
            await acceptShadowIntervention({
                student_id: userId,
                interaction_id: interactionId,
                modality_type: shadowReady.current_modality,
                action_type: shadowReady.alternative_label,
                topic_id: topic.id || topic.title
            });
            setContent({ content: shadowReady.full_text, type: shadowReady.current_modality || "explanation" });
            setShadowReady(null);
        } catch (err) {
            console.error("Shadow Accept Error:", err);
        }
    };

    const handleDismissShadow = () => {
        if (sio && userId) {
            sio.emit("intervention_resolved", { student_id: userId });
        }
        setShadowReady(null);
    };

    const handleForceRegenerate = async () => {
        setIsThinking(true);
        setContent(null);
        setError(null);
        setShadowReady(null);
        try {
            const result = await runSimulation(`Teach me about ${topic.title}`, topic);
            const directive = result.nodes?.find(n => n.id === result.meta?.best_path_ids?.slice(-1)[0])?.data?.directive;
            setContent(directive);
            setIsThinking(false);
        } catch (e) {
            setError("Regeneration failed.");
        }
    };

    const handleComplete = async () => {
        if (!sessionId || !topic || isCompleting) return;
        setIsCompleting(true);
        try {
            await updateSessionProgress(sessionId, topic.title);
            const finalPayload = {
                student_id: userId,
                session_id: sessionId,
                topic_id: topic.title,
                content: content,
                user_response: response,
                ai_evaluation_score: score,
                interaction_id: interactionId
            };
            await saveLessonContent(finalPayload);
            await syncStudentProgress(finalPayload);
            
            if (content?.type === 'quiz' && isSubmitted) {
                await savePerformance({
                    student_id: userId,
                    session_id: sessionId,
                    topic_id: topic.title,
                    score: selectedOption === content.quiz?.correct_index ? 100 : 0,
                    total_questions: 1,
                    correct_answers: selectedOption === content.quiz?.correct_index ? 1 : 0
                });
            }

            if (sessionData?.plan?.curriculum?.structure) {
                const currentCompleted = [...(sessionData.session?.progress?.completed_topics || []), topic.title];
                let nextTopic = null;
                for (const lecture of sessionData.plan.curriculum.structure) {
                    for (const t of (lecture.children || [])) {
                        if (!currentCompleted.includes(t.title)) {
                            nextTopic = t;
                            break;
                        }
                    }
                    if (nextTopic) break;
                }
                if (nextTopic) {
                    const colId = sessionData.plan.system_metadata?.collection_id || sessionData.plan.collection_id;
                    console.error("[PREFETCH] Triggering next topic:", nextTopic.title);
                    onPrefetchStarted?.(nextTopic.title);
                    manualPrefetch({
                        session_id: sessionId,
                        topic_title: nextTopic.title,
                        student_id: userId,
                        collection_id: colId
                    }).catch(() => {});
                }
            }

            onBack();
        } catch (err) {
            console.error("Completion Error:", err);
            toast.error("Failed to synchronize completion.");
        } finally {
            setIsCompleting(false);
        }
    };

    const handleFeedback = async (sentiment) => {
        if (feedbackSent) return;
        setFeedbackSent(sentiment ? 'up' : 'down');
        const feedbackToast = toast.loading("Sending feedback...");
        try {
            const modality = (content?.type === 'visual_explanation' || (content?.content && content.content.includes('graph TD'))) ? 'visual' : 'textual';
            const targetInteractionId = interactionId || topic?.title || sessionId || "fallback_id";
            await handleUserFeedback({
                student_id: userId,
                interaction_id: targetInteractionId,
                action_type: strategyLabel || "SIMPLIFY_EXPLANATION",
                sentiment: sentiment,
                modality_type: modality,
                topic_id: topic?.title
            });
            toast.success("Feedback recorded!", { id: feedbackToast });
        } catch (err) {
            toast.error("Couldn't save feedback.", { id: feedbackToast });
        }
    };

    return {
        loading, content, isThinking, selectedOption, setSelectedOption, isSubmitted, setIsSubmitted,
        isChallengeComplete, setIsChallengeComplete, shadowReady, setShadowReady, isCompleting, response, setResponse,
        error, isVisualReady, interactionId, strategyLabel, feedbackSent, score, setScore,
        signalData, currentModality, ragSources, profileToast, progressPhases, elapsedSeconds,
        isDeliveryComplete, isFromCache, sanitizedContent, mermaidData, isContentViewable,
        isReadyToComplete, handleAcceptShadow, handleDismissShadow, handleForceRegenerate, handleComplete, handleFeedback
    };
};
