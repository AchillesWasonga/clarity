"use client";

import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import Input from "@/components/ui/input";

export function MainContent() {
  const [showInput, setShowInput] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [showFullscreen, setShowFullscreen] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === "t" && !showInput) {
        event.preventDefault(); // Prevent the "t" from being typed
        setShowInput(true);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [showInput]);

  const handleInputSubmit = async (value: string) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('question', value);

      const response = await fetch('http://localhost:8000/video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Video generation failed');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
    } catch (error) {
      console.error("Error generating video:", error);
      // You might want to add error handling UI here
    } finally {
      setIsProcessing(false);
    }
  };

  // Clean up object URL when component unmounts or videoUrl changes
  useEffect(() => {
    return () => {
      if (videoUrl && videoUrl.startsWith('blob:')) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  }, [videoUrl]);

  const toggleFullscreen = () => {
    setShowFullscreen(!showFullscreen);
  };

  return (
    <div className="container mx-auto px-4 min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center">
        {/* Centered container for the header and landscape photo */}
        <div className="relative w-[953px]">
          {/* Header Image */}
          <Image
            src="/images/top1.png"
            alt="Header image"
            width={953}
            height={100}
            className="w-full object-cover"
            priority
          />
          {/* Main Image Container */}
          <div className="relative h-[539px]">
            <Image
              src="/images/option3.png"
              alt="Mountain landscape"
              width={953}
              height={539}
              className="w-full h-full object-cover"
              priority
            />
            {/* Level 2: Window Container - centered within the landscape */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-[812px] h-[483px] bg-black rounded-lg p-0.5 overflow-hidden">
                {/* Window Header */}
                <div className="bg-black h-8 flex items-center px-3 rounded-t-lg">
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                  </div>
                </div>
                {/* Window Content */}
                <div className="bg-black rounded-b-lg p-4 h-[443px] overflow-y-auto 
                  scrollbar-thin scrollbar-thumb-zinc-600 scrollbar-track-transparent
                  hover:scrollbar-thumb-zinc-500">
                  {videoUrl ? (
                    <div
                      className={`relative ${
                        showFullscreen ? "fixed inset-0 z-50" : "w-full h-full"
                      }`}
                    >
                      <video
                        src={videoUrl}
                        className="w-full h-full object-cover"
                        controls
                      />
                      
                    </div>
                  ) : (
                    <div className="flex">
                      {/* Constrain text to 60% and add left padding */}
                      <div className="w-[60%] pl-[10%]">
                        <h1 className="text-4xl font-extrabold mb-6">
                          Clarity
                        </h1>
                        {showInput ? (
                          <Input
                            placeholder="Ask a question…"
                            onEnter={handleInputSubmit}
                            isProcessing={isProcessing}
                            ref={inputRef}
                          />
                        ) : (
                          <>
                            <div className="text-xs text-gray-400 mb-4">
                              Clarity is an innovative AI-powered platform that transforms complex educational content into engaging visual stories. By combining cutting-edge artificial intelligence with dynamic visualization techniques, Clarity makes learning more accessible, memorable, and enjoyable for everyone. Whether you're a student, educator, or lifelong learner, our platform helps break down difficult concepts into clear, compelling narratives that stick.
                            </div>

                            <div className="space-y-4">
                              <section>
                                <h2 className="text-sm font-semibold mb-2">
                                  Sample Videos
                                </h2>
                                <span className="text-xs text-gray-300 leading-relaxed">
                                  <ul className="list-disc list-inside space-y-1">
                                    <li>
                                      <button 
                                        className="text-white hover:text-gray-300 transition-colors"
                                        onClick={() => setVideoUrl("/video/ac-motor.mp4")}
                                      >
                                        AC Motor Explained
                                      </button>
                                    </li>
                                    <li>
                                      <button
                                        className="text-white hover:text-gray-300 transition-colors"
                                        onClick={() => setVideoUrl("/video/neural-networks.mp4")}
                                      >
                                        Neural Networks Fundamentals
                                      </button>
                                    </li>
                                    <li>
                                      <button
                                        className="text-white hover:text-gray-300 transition-colors"
                                        onClick={() => setVideoUrl("/video/blockchain.mp4")}
                                      >
                                        Blockchain Technology
                                      </button>
                                    </li>
                                  </ul>
                                </span>
                              </section>


                              <section>
                                <h2 className="text-sm font-semibold mb-2">
                                  Contributors
                                </h2>
                                <p className="text-xs text-gray-300 leading-relaxed">
                                 Utkarsh, Bobir, JJ, and Achilles.
                                </p>
                              </section>
                            </div>
                          </>
                        )}
                      </div>

                      {/* Add any additional content or leave the remaining space empty */}
                      <div className="w-[40%]" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Monitor Stand */}
        <div className="mt-[10px] w-[250px]">
          <Image
            src="/images/stand.png"
            alt="Monitor stand"
            width={200}
            height={50}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}
