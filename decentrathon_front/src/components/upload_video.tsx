"use client"
import React, { useState, useRef, useEffect } from "react";
import { useReactMediaRecorder } from "react-media-recorder";
import axiosInstance from "./axios_instance";

const UploadVideo: React.FC = () => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const videoPreviewRef = useRef<HTMLVideoElement | null>(null);
  const [urlVideo, setUrlVideo] = useState('');
  const [prompt, setPrompt] = useState('');
  const [csvData, setCsvData] = useState<string | null>(null); // New state for CSV data

  const {
    startRecording,
    stopRecording,
    mediaBlobUrl,
    previewStream,
  } = useReactMediaRecorder({
    video: true,
  });

  // Attach the media stream to the video element for live preview
  useEffect(() => {
    if (videoPreviewRef.current && previewStream) {
      videoPreviewRef.current.srcObject = previewStream;
    }
  }, [previewStream]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null;
    setVideoFile(file);
  };

  const handlePromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(e.target.value); // Update the prompt state
  };

  const handleUpload = async () => {
    if (videoFile || mediaBlobUrl) {
      const formData = new FormData();
      if (videoFile) {
        formData.append("file", videoFile);
      } else if (mediaBlobUrl) {
        const response = await fetch(mediaBlobUrl);
        const blob = await response.blob();
        formData.append("file", blob);
      }

      try {
        // Upload the video
        const res = await axiosInstance.post("/llm/upload-video/", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        console.log(res.data.message);
        setUrlVideo(res.data.message);

        // Request the CSV based on the uploaded video and prompt
        const res2 = await axiosInstance.post("/llm/download-csv/", {
          "video_file": res.data.message,
          "prompt": prompt
        }, {
          responseType: 'blob' // Important for handling binary data
        });

        // Convert the blob to a downloadable URL
        const csvBlob = new Blob([res2.data], { type: 'text/csv' });
        const csvUrl = URL.createObjectURL(csvBlob);
        setCsvData(csvUrl); // Store the CSV URL

        console.log("CSV file received");
        alert("Video uploaded and CSV generated successfully!");

      } catch (error) {
        console.error("Upload failed:", error);
        alert("Failed to upload video.");
      }
    } else {
      alert("Please select or record a video first.");
    }
  };

  const handleDownloadCSV = () => {
    if (csvData) {
      const link = document.createElement('a');
      link.href = csvData;
      link.download = 'data.csv'; // Specify the default file name
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-6 bg-white shadow-lg rounded-lg mt-10">
      <h2 className="text-2xl font-bold mb-6 text-center">
        Upload or Record a Video
      </h2>

      {/* File Upload Section */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">
          Select a video:
        </label>
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring focus:border-blue-300"
        />
      </div>

      {/* Prompt Input Section */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">
          Enter a prompt:
        </label>
        <input
          type="text"
          value={prompt}
          onChange={handlePromptChange}
          placeholder="Type your prompt here"
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring focus:border-blue-300"
        />
      </div>

      {/* Video Recording Section */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-center">
          Or Record a Video
        </h3>
        <div className="flex justify-center space-x-4 mb-4">
          <button
            onClick={startRecording}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Start Recording
          </button>
          <button
            onClick={stopRecording}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            Stop Recording
          </button>
        </div>

        {/* Real-time Preview while recording */}
        {previewStream && (
          <video
            ref={videoPreviewRef}
            autoPlay
            muted
            className="w-full rounded-md shadow-lg border mt-4"
          />
        )}

        {/* Video Preview after recording stops */}
        {mediaBlobUrl && (
          <video
            src={mediaBlobUrl}
            controls
            autoPlay
            loop
            className="w-full rounded-md shadow-lg border mt-4"
          />
        )}
      </div>

      {/* Upload Button */}
      <div className="text-center">
        <button
          onClick={handleUpload}
          className="px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
        >
          Upload Video
        </button>
      </div>

      {/* Display CSV Data and Download Button */}
      {csvData && (
        <div className="mt-8 p-4 bg-gray-100 rounded-md shadow-inner">
          <h3 className="text-xl font-semibold mb-2">CSV Data:</h3>
          <pre className="whitespace-pre-wrap text-sm text-gray-700">
            {/* Optionally, you can fetch and display the CSV content */}
            {/* For simplicity, we're providing a download link/button instead */}
            Your CSV file is ready for download.
          </pre>
          <button
            onClick={handleDownloadCSV}
            className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
          >
            Download CSV
          </button>
        </div>
      )}
    </div>
  );
};

export default UploadVideo;
