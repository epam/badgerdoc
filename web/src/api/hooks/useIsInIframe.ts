import { useEffect, useState } from "react";

export const useIsInIframe = () => {
    const [isInIframe, setIsInIframe] = useState(false);
    
    useEffect(() => {
        const checkIframe = () => {
        try {
            return window.self !== window.top;
        } catch (e) {
            return true; // If accessing window.top throws error, we're in iframe
        }
        };
        
        setIsInIframe(checkIframe());
    }, []);
    
    return isInIframe;
};
