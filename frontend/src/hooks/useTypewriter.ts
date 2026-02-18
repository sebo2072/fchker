import { useState, useEffect, useRef } from 'react';

export const useTypewriter = (text: string, speed: number = 30) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    // Use refs so interval closure always sees current values
    const indexRef = useRef(0);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const textRef = useRef(text);

    // Sync textRef whenever text prop changes
    useEffect(() => {
        textRef.current = text;
    }, [text]);

    useEffect(() => {
        // Always clear existing interval first — no exceptions
        if (intervalRef.current !== null) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        // If text is empty or shorter than where we are, do a hard reset
        if (text.length === 0 || text.length < indexRef.current) {
            setDisplayedText('');
            setIsComplete(false);
            indexRef.current = 0;
            if (text.length === 0) return;
        }

        // If we are already past the end of the new text, nothing to do
        if (indexRef.current >= text.length) {
            setIsComplete(true);
            return;
        }

        setIsComplete(false);

        // Single interval — reads from indexRef (not closure variable)
        intervalRef.current = setInterval(() => {
            const currentIndex = indexRef.current;
            const currentText = textRef.current;

            if (currentIndex < currentText.length) {
                setDisplayedText(currentText.slice(0, currentIndex + 1));
                indexRef.current = currentIndex + 1;
            } else {
                if (intervalRef.current !== null) {
                    clearInterval(intervalRef.current);
                    intervalRef.current = null;
                }
                setIsComplete(true);
            }
        }, speed);

        return () => {
            if (intervalRef.current !== null) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [text, speed]);

    return { displayedText, isComplete };
};
