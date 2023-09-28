// temporary_disabled_rules
/* eslint-disable react-hooks/exhaustive-deps */
import React, { useRef, useEffect } from 'react';
import './progress-bar.scss';

type ProgressBarProps = {
    value: number;
};

export const ProgressBar: React.FC<ProgressBarProps> = ({ value }) => {
    const circle = useRef<HTMLDivElement>(null);

    const changeColor = () => {
        if (value < 0.2) return 'danger';
        else if (value < 0.6) return 'warning';
        else return 'success';
    };

    useEffect(() => {
        if (value > 1) return;
        const percentage = value * 180 + 180;
        if (circle.current) {
            circle.current.style.transform = `rotate(${percentage}deg)`;
            circle.current.style.transition = 'transform 1s';
        }
    }, []);
    return (
        <div className="progress-wheel-wrapper">
            <div className="pw-body">
                <div className={`pw-circle ${changeColor()}`} ref={circle} />
                <div className="pw-circle-overlay">
                    <span className="pw-value-label">{value}</span>
                </div>
            </div>
        </div>
    );
};
