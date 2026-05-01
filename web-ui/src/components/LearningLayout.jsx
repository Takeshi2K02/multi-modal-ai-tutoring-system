import React from 'react';
import LiveAffectSensing from './LiveAffectSensing';

const LearningLayout = ({ children, studentId = localStorage.getItem('userId'), topicId, enabled = false }) => {
    return (
        <div className="h-full w-full relative">
            <LiveAffectSensing userId={studentId} materialId={topicId} enabled={enabled} />
            {children}
        </div>
    );
};

export default LearningLayout;
