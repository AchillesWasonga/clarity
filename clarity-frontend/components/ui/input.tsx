"use client";

import React, { useState, useEffect, forwardRef } from "react";
import { LoaderCore } from "./multi-step-loader";
import OpenAI from 'openai';

interface InputProps {
  placeholder: string;
  onEnter?: (value: string) => void;
  isProcessing: boolean;
}

const openai = new OpenAI({
  apiKey: process.env.NEXT_PUBLIC_OPENAI_API_KEY,
  dangerouslyAllowBrowser: true
});

const defaultLoadingStates = [
  { text: "Initializing request..." },
  { text: "Understanding your question..." },
  { text: "Analyzing topic complexity..." },
  { text: "Generating script outline..." },
  { text: "Creating storyboard..." },
  { text: "Preparing visual elements..." },
  { text: "Rendering initial frames..." },
  { text: "Processing video segments..." },
];

const Input = forwardRef<HTMLTextAreaElement, InputProps>(
  ({ placeholder, onEnter, isProcessing }, ref) => {
    const [value, setValue] = useState("");
    const [currentState, setCurrentState] = useState(0);
    const [loadingStates, setLoadingStates] = useState(defaultLoadingStates);

    const generateLoadingSteps = async (query: string) => {
      try {
        const completion = await openai.chat.completions.create({
          messages: [
            {
              role: "system",
              content: "You are an AI that generates detailed step-by-step processes for video creation. Generate at least 40 specific, technical steps that would be involved in creating an educational video about the given topic. Each step should be concise. Examples of steps: 'Initializing request', 'Understanding your question', 'Analyzing topic complexity', 'Generating script outline', 'Creating storyboard', 'Preparing visual elements', 'Rendering initial frames', 'Processing video segments'. Format the output as a JSON array of objects with a 'text' property."
            },
            {
              role: "user",
              content: `Generate detailed steps for creating an educational video about: ${query}`
            }
          ],
          model: "gpt-4o-mini",
          response_format: { type: "json_object" },
          temperature: 0.7,
        });

        const response = JSON.parse(completion.choices[0].message.content || "{}");
        if (response.steps && Array.isArray(response.steps)) {
          setLoadingStates(prev => [...prev, ...response.steps]);
        }
      } catch (error) {
        console.error("Error generating loading steps:", error);
        // Continue with default steps if there's an error
      }
    };

    useEffect(() => {
      const handleFirstFocus = () => {
        setValue("");
      };

      const inputElement = ref as React.RefObject<HTMLTextAreaElement>;
      inputElement.current?.addEventListener("focus", handleFirstFocus, {
        once: true,
      });

      return () => {
        inputElement.current?.removeEventListener("focus", handleFirstFocus);
      };
    }, []);

    useEffect(() => {
      if (!isProcessing) {
        setCurrentState(0);
        setLoadingStates(defaultLoadingStates); // Reset to default states
        return;
      }

      const interval = setInterval(() => {
        setCurrentState((prev) => (prev === loadingStates.length - 1 ? 0 : prev + 1));
      }, 3000);

      return () => clearInterval(interval);
    }, [isProcessing, loadingStates.length]);

    const handleKeyDown = async (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (onEnter && !isProcessing && value.trim() !== "") {
          // Start with default states immediately
          onEnter(value);
          setValue("");
          // Generate additional steps in the background
          generateLoadingSteps(value.trim());
        }
      }
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (e.target.value.length <= 100) {
        setValue(e.target.value);
      }
    };

    return (
      <div className="relative w-full">
        {isProcessing ? (
          <div className="w-full h-[200px] bg-black rounded overflow-hidden">
            <div className="relative h-full">
              {/* Top fade gradient */}
              <div className="pt-4 absolute top-0 left-0 right-0 h-2 bg-gradient-to-b from-black to-transparent z-10" />
              
              <LoaderCore 
                value={currentState} 
                loadingStates={loadingStates}
                className="h-full p-4"
              />
              
              {/* Bottom fade gradient */}
              <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black to-transparent z-10" />
            </div>
          </div>
        ) : (
          <textarea
            ref={ref}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full bg-black text-white p-2 text-sm rounded focus:outline-none focus:border-gray-300 resize-none"
            maxLength={200}
            rows={4}
            disabled={isProcessing}
          />
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
